"""Shadow propagation on a voxel grid (Palubicki et al. 2009, Sec. 4.2).

In the paper every bud adds shadow to the voxels of a pyramid below it, and a
bud's light exposure is ``Q = max(C - s + a, 0)``.  Here the same rule is
applied along every light direction supplied by the environment, with two
physical refinements:

* the shadow cast by a leaf is conserved along each direction: it spreads
  into a widening penumbra instead of being copied into every voxel of a
  growing pyramid, fades slowly with depth (scattering) and over a few metres
  of horizontal travel;
* ``a`` is not a free constant: it is the light a bud's leaf area blocks in
  one voxel, ``a = k * A_leaf / voxel_size**2`` (Beer-Lambert with extinction
  coefficient k, Monsi & Saeki 1953).

Implementation: the grid is swept from the top layer down.  For each light
direction the shadow carried from one layer to the next is shifted along
the ray, smeared over the horizontal path the ray crosses inside the layer,
blurred (penumbra) and decayed.  All of that is one transfer function per
direction in the 2-D Fourier domain, so each layer costs one forward and one
inverse FFT for all directions together.  A horizontal margin keeps the
periodic wrap of the FFT away from the crown.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.spatial import cKDTree


def _fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    th = np.pi * (1.0 + 5.0 ** 0.5) * i
    return np.stack([r * np.cos(th), r * np.sin(th), z], axis=1)


class ShadowPropagation:
    def __init__(self, environment, lp, horizontal_reach: float | None = None, vertical_decay: float | None = None):
        self.vs = float(lp.voxel_size)
        self.k_ext = float(lp.extinction_coefficient)
        self.leaf_area = float(lp.leaf_area_m2)
        # shadow one leaf casts into its own voxel
        self.a = self.k_ext * self.leaf_area / self.vs ** 2
        # leaves stand off the node on petiole and blade: a bud's leaf area is
        # spread over a small Gaussian around it before propagation (shade is
        # conserved); g0 is the share that stays in the bud's own voxel
        self.leaf_sigma = float(lp.leaf_spread) / self.vs
        if self.leaf_sigma > 0:
            delta = np.zeros((9, 9, 9))
            delta[4, 4, 4] = 1.0
            self.g0 = float(gaussian_filter(delta, self.leaf_sigma, mode="constant")[4, 4, 4])
        else:
            self.g0 = 1.0
        self.decay_vertical = float(lp.shadow_decay_length if vertical_decay is None else vertical_decay)
        self.decay_horizontal = float(lp.shadow_horizontal_reach if horizontal_reach is None else horizontal_reach)
        self.penumbra = float(lp.penumbra_diffusion)
        self.margin = float(lp.horizontal_margin)
        self.C = float(environment.full_light)
        self.perception_r = float(lp.perception_radius)
        self.perception_cos = math.cos(math.radians(lp.perception_cone_deg))
        self.softmin = float(lp.perception_softmin)
        dirs, w = environment.light_directions()
        self.light_dirs = dirs.astype(np.float64)
        self.light_w = w.astype(np.float64)
        self.probe_dirs = _fibonacci_sphere(int(lp.perception_samples))
        self._tf_cache: dict = {}
        self._impulse = None

    def _transfer(self, nx: int, ny: int) -> np.ndarray:
        """Per-direction transfer functions for one layer step, (K, nx, ny//2+1)."""
        key = (nx, ny)
        if key in self._tf_cache:
            return self._tf_cache[key]
        fx = np.fft.fftfreq(nx)[:, None]
        fy = np.fft.rfftfreq(ny)[None, :]
        out = []
        for d in self.light_dirs:
            dz = -d[2]
            hx, hy = d[0] / dz, d[1] / dz              # horizontal shift per layer, voxels
            path = self.vs / dz                          # path length per layer, m
            # shade is conserved going down (scattering only, long length) and
            # fades with horizontal travel, which also keeps the periodic wrap
            # of the FFT from bringing a tree's low-angle shadow back onto it
            decay = math.exp(-self.vs / self.decay_vertical - self.vs * math.hypot(hx, hy) / self.decay_horizontal)
            sigma2 = self.penumbra * path / self.vs ** 2  # penumbra variance per layer, voxels^2
            phase = fx * hx + fy * hy
            shift = np.exp(-2j * np.pi * phase)
            smear = np.sinc(phase)                       # box over the path crossed in the layer
            blur = np.exp(-2.0 * np.pi ** 2 * sigma2 * (fx ** 2 + fy ** 2))
            out.append((decay * shift * smear * blur).astype(np.complex64))
        tf = np.stack(out)
        self._tf_cache = {key: tf}
        return tf

    # window of the own-shoot shade: horizontal half-width and layers below
    OWN_HALF = 3
    OWN_DOWN = 5

    def impulse_response(self) -> np.ndarray:
        """Shade that a unit deposit casts on the voxels around it,
        R[dx + h, dy + h, dz + d] for |dx|, |dy| <= h and -d <= dz <= 2 (offset
        of the receiving voxel from the depositing one; h = OWN_HALF, d =
        OWN_DOWN).  Propagation is linear and the same everywhere, so the
        shade a group of sources casts on one another is a sum of shifted
        copies of R."""
        if self._impulse is None:
            h, d, vs = self.OWN_HALF, self.OWN_DOWN, self.vs
            pos = np.array([[0.5 * vs, 0.5 * vs, (d + 1.5) * vs], [0.5 * vs, 0.5 * vs, 0.5 * vs]])
            f = self.compute(pos, np.array([1.0 / self.a, 0.0]))
            i = np.floor(pos[0] / vs).astype(int) - f.lo
            self._impulse = f.S[i[0] - h:i[0] + h + 1, i[1] - h:i[1] + h + 1, i[2] - d:i[2] + 3].astype(np.float64)
            self._tf_cache = {}
        return self._impulse

    def own_shade(self, pos: np.ndarray, w: np.ndarray, group: np.ndarray) -> np.ndarray:
        """Shade at each source from its own group (itself and the other
        sources with the same group id, e.g. a shoot and its short shoots),
        as the field computes it."""
        R = self.impulse_response()
        h, d = self.OWN_HALF, self.OWN_DOWN
        a = self.a
        idx = np.floor(pos / self.vs).astype(np.int64)
        out = a * w * R[h, h, d]
        if len(pos) < 2:
            return out
        span = int(idx[:, 0].max() - idx[:, 0].min()) + 4 * (h + d) + 8
        key = idx.astype(np.float64)
        key[:, 0] += np.asarray(group, np.float64) * span
        pairs = cKDTree(key).query_pairs(r=math.sqrt(2 * h * h + d * d) + 1e-6, output_type="ndarray")
        if len(pairs) == 0:
            return out
        i, j = pairs[:, 0], pairs[:, 1]
        dv = idx[i] - idx[j]
        for rec, src, off in ((i, j, dv), (j, i, -dv)):
            ok = (np.abs(off[:, 0]) <= h) & (np.abs(off[:, 1]) <= h) & (off[:, 2] >= -d) & (off[:, 2] <= 2)
            o = off[ok]
            np.add.at(out, rec[ok], a * w[src[ok]] * R[o[:, 0] + h, o[:, 1] + h, o[:, 2] + d])
        return out

    def compute(self, src_pos: np.ndarray, src_w: np.ndarray, region: np.ndarray | None = None,
                periodic: tuple | None = None,
                wood_pos: np.ndarray | None = None, wood_area: np.ndarray | None = None,
                k_wood: float = 0.40) -> "LightField":
        """Shadow field from weighted sources.

        ``region`` (2, 3) bounds the part of the grid that must be accurate
        (the focal tree).  ``periodic`` = (x0, y0, nx, ny) makes the grid one
        horizontally repeating cell of nx * ny voxels starting at (x0, y0):
        sources wrap into it and the FFT's periodic boundary continues it
        without end (a stand with no edge).  Otherwise a margin keeps the wrap
        away from the crown.
        """
        vs = self.vs
        has_wood = wood_pos is not None and wood_area is not None and len(wood_pos) > 0
        if has_wood:
            all_pts = np.concatenate([src_pos, wood_pos])
            hi = np.floor(all_pts.max(0) / vs).astype(int)
            lo = np.floor(all_pts.min(0) / vs).astype(int)
        else:
            hi = np.floor(src_pos.max(0) / vs).astype(int)
            lo = np.floor(src_pos.min(0) / vs).astype(int)
        lo[2] = max(lo[2] - 1, -1)
        hi[2] += 2
        if periodic is not None:
            x0, y0, nx, ny = periodic
            lo[0] = int(round(x0 / vs))
            lo[1] = int(round(y0 / vs))
            nz = int(hi[2] - lo[2] + 1)
            idx = np.floor(src_pos / vs).astype(int) - lo
            idx[:, 0] %= nx
            idx[:, 1] %= ny
        else:
            m = int(math.ceil(self.margin / vs))
            lo[:2] -= m
            hi[:2] += m
            nx, ny, nz = (int(v) for v in (hi - lo + 1))
            idx = np.floor(src_pos / vs).astype(int) - lo
        shape = (int(nx), int(ny), int(nz))
        D = np.zeros(shape, dtype=np.float32)
        np.add.at(D, (idx[:, 0], idx[:, 1], idx[:, 2]), (self.a * src_w).astype(np.float32))
        if has_wood:
            idx_wood = np.floor(wood_pos / vs).astype(int) - lo
            if periodic is not None:
                idx_wood[:, 0] %= nx
                idx_wood[:, 1] %= ny
                ok_w = (idx_wood[:, 2] >= 0) & (idx_wood[:, 2] < nz)
            else:
                ok_w = (idx_wood[:, 0] >= 0) & (idx_wood[:, 0] < nx) &                        (idx_wood[:, 1] >= 0) & (idx_wood[:, 1] < ny) &                        (idx_wood[:, 2] >= 0) & (idx_wood[:, 2] < nz)
            if ok_w.any():
                iw = idx_wood[ok_w]
                wood_d = (float(k_wood) * wood_area[ok_w] / (vs ** 2)).astype(np.float32)
                np.add.at(D, (iw[:, 0], iw[:, 1], iw[:, 2]), wood_d)
        if self.leaf_sigma > 0:
            mode = ("wrap", "wrap", "constant") if periodic is not None else "constant"
            D = gaussian_filter(D, self.leaf_sigma, mode=mode, truncate=3.0)
        tf = self._transfer(nx, ny)
        wk = self.light_w.astype(np.float32)
        S = np.zeros(shape, dtype=np.float32)
        B = np.zeros(tf.shape, dtype=np.complex64)
        occupied = np.nonzero(D.reshape(-1, nz).any(0))[0]
        if len(occupied) == 0:
            return LightField(self, S, lo, periodic is not None)
        top = int(occupied.max())
        bottom = 0 if region is None else max(0, int(math.floor(region[0, 2] / vs)) - lo[2] - 1)
        for z in range(top, bottom - 1, -1):
            B *= tf
            layer = D[:, :, z]
            if layer.any():
                B += np.fft.rfft2(layer)[None]
            S[:, :, z] = np.fft.irfft2(np.tensordot(wk, B, axes=1), s=(nx, ny))
        np.maximum(S, 0.0, out=S)
        return LightField(self, S, lo, periodic is not None)


class LightField:
    """Shadow values for one growth cycle."""

    def __init__(self, prop: ShadowPropagation, S: np.ndarray, lo: np.ndarray, periodic: bool = False):
        self.p = prop
        self.S = S
        self.lo = lo
        self.periodic = periodic   # horizontally repeating (a stand or plot cell)

    def shadow_at_voxel(self, pos: np.ndarray) -> np.ndarray:
        idx = np.floor(pos / self.p.vs).astype(int) - self.lo
        if self.periodic:
            idx[:, 0] %= self.S.shape[0]
            idx[:, 1] %= self.S.shape[1]
        inside = np.all((idx >= 0) & (idx < np.array(self.S.shape)), axis=1)
        out = np.zeros(len(pos))
        ii = idx[inside]
        out[inside] = self.S[ii[:, 0], ii[:, 1], ii[:, 2]]
        return out

    def exposure(self, pos: np.ndarray, self_weight: np.ndarray, own_shade: np.ndarray | None = None) -> np.ndarray:
        """Light exposure of a bud.  Palubicki et al. (Sec. 4.2) use
        Q = max(C - s + a*w_self, 0), the first-order form of Beer-Lambert;
        the full form Q = C exp(-(s - a*w_self)/C) (Monsi & Saeki 1953) keeps
        realistic light under a closed canopy (leaf-area index 3-5).  With
        ``own_shade`` (the shade of the bud's own shoot, see
        ShadowPropagation.own_shade) that is removed instead of the bud's own
        leaves only: no shoot shades itself."""
        s = self.shadow_at_voxel(pos)
        own = self.p.a * self.p.g0 * self_weight if own_shade is None else own_shade
        return self.p.C * np.exp(-np.maximum(s - own, 0.0) / self.p.C)

    def sample(self, pts: np.ndarray) -> np.ndarray:
        """Trilinear shadow lookup at arbitrary points (0 outside the grid)."""
        c = pts / self.p.vs - self.lo - 0.5
        if self.periodic:
            # wrap horizontally; above or below the grid there is no shade
            c[:, 0] %= self.S.shape[0]
            c[:, 1] %= self.S.shape[1]
            out = map_coordinates(self.S, c.T, order=1, mode="grid-wrap")
            return np.where((c[:, 2] < -0.5) | (c[:, 2] > self.S.shape[2] - 0.5), 0.0, out)
        return map_coordinates(self.S, c.T, order=1, mode="constant", cval=0.0)

    def optimal_direction(self, pos: np.ndarray, heading: np.ndarray) -> np.ndarray:
        """Direction of least shadow inside the perception cone around ``heading``.

        Palubicki et al. use the direction to the least-shaded voxel; a soft-min
        over probe directions gives the same answer without voxel aliasing.
        """
        p = self.p
        dirs = p.probe_dirs
        m, k = len(pos), len(dirs)
        cosang = heading @ dirs.T  # (m, k)
        pts = pos[:, None, :] + p.perception_r * dirs[None, :, :]
        s = self.sample(pts.reshape(-1, 3)).reshape(m, k)
        s = np.where(pts[..., 2] < 0.05, s + 10.0 * p.C, s)  # the ground is opaque
        s = np.where(cosang >= p.perception_cos, s, np.inf)
        smin = s.min(1, keepdims=True)
        wts = np.where(np.isfinite(s), np.exp(-(s - smin) / max(p.softmin, 1e-6)), 0.0)
        v = wts @ dirs
        n = np.linalg.norm(v, axis=1, keepdims=True)
        return np.where(n > 1e-9, v / np.maximum(n, 1e-12), heading)
