"""Render a game .glb, textures and all, so what's judged is what's exported.

A small software renderer: z-buffered triangles with alpha test, mip-mapped textures, normal maps,
a sun with a shadow map, sky light with occlusion from a handful of directions, and light through
leaves (KHR_materials_diffuse_transmission, as the file has it).  It reads only the .glb.

This is for looking at the work, on any machine, without an engine.  An engine won't look exactly
like it, and its lighting is plain on purpose.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from numba import njit

from .export import glb_accessor, read_glb


def srgb_decode(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4).astype(np.float32)


def srgb_encode(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * a ** (1.0 / 2.4) - 0.055)


def _mips(a: np.ndarray) -> list:
    out = [a]
    while min(out[-1].shape[:2]) > 1:
        b = out[-1]
        h, w = b.shape[:2]
        h2, w2 = (h // 2) * 2, (w // 2) * 2
        b = b[:h2, :w2]
        out.append(0.25 * (b[::2, ::2] + b[1::2, ::2] + b[::2, 1::2] + b[1::2, 1::2]))
    return out


class Texture:
    def __init__(self, arr: np.ndarray, wrap_s=True, wrap_t=True):
        self.mips = _mips(arr)
        self.wrap_s, self.wrap_t = wrap_s, wrap_t

    def sample(self, uv: np.ndarray, lod: np.ndarray) -> np.ndarray:
        """Trilinear."""
        lod = np.clip(lod, 0.0, len(self.mips) - 1.0)
        k = np.floor(lod).astype(np.int64)
        f = (lod - k).astype(np.float32)[:, None]
        out = np.zeros((len(uv), self.mips[0].shape[2] if self.mips[0].ndim == 3 else 1), np.float32)
        for m in np.unique(k):
            idx = np.nonzero(k == m)[0]
            a = self._bilinear(self.mips[int(m)], uv[idx])
            if int(m) + 1 < len(self.mips):
                a = a * (1 - f[idx]) + self._bilinear(self.mips[int(m) + 1], uv[idx]) * f[idx]
            out[idx] = a
        return out

    def _bilinear(self, mip, uv):
        h, w = mip.shape[:2]
        x = uv[:, 0] * w - 0.5
        y = uv[:, 1] * h - 0.5
        x0 = np.floor(x).astype(np.int64)
        y0 = np.floor(y).astype(np.int64)
        fx = (x - x0).astype(np.float32)[:, None]
        fy = (y - y0).astype(np.float32)[:, None]
        if self.wrap_s:
            x0, x1 = x0 % w, (x0 + 1) % w
        else:
            x1 = np.clip(x0 + 1, 0, w - 1)
            x0 = np.clip(x0, 0, w - 1)
        if self.wrap_t:
            y0, y1 = y0 % h, (y0 + 1) % h
        else:
            y1 = np.clip(y0 + 1, 0, h - 1)
            y0 = np.clip(y0, 0, h - 1)
        a = mip[y0, x0] * (1 - fx) + mip[y0, x1] * fx
        b = mip[y1, x0] * (1 - fx) + mip[y1, x1] * fx
        return a * (1 - fy) + b * fy


class Primitive:
    """A mesh of the file, back in z-up, with its material's textures."""

    def __init__(self, name, V, N, F, UV=None, T=None, C=None, base=None, normal=None, orm=None, factor=(1, 1, 1, 1), rough=1.0, metal=0.0,
                 alpha=None, cutoff=0.5, double=False, dt_factor=0.0, dt_color=(1, 1, 1), normal_scale=1.0):
        self.name = name
        self.V, self.N, self.F, self.UV, self.T, self.C = V, N, F, UV, T, C
        self.base, self.normal, self.orm = base, normal, orm
        self.factor = np.asarray(factor, np.float32)
        self.rough, self.metal = rough, metal
        self.alpha, self.cutoff, self.double = alpha, cutoff, double
        self.dt_factor, self.dt_color = dt_factor, np.asarray(dt_color, np.float32)
        self.normal_scale = normal_scale


def load_glb_primitives(path) -> list:
    """Every mesh of a .glb written by GameGLB, ready to render."""
    from PIL import Image

    doc, blob = read_glb(path)
    cache = {}

    def image(tex_index, srgb):
        key = (tex_index, srgb)
        if key not in cache:
            t = doc["textures"][tex_index]
            img = doc["images"][t["source"]]
            if "uri" in img:
                a = np.asarray(Image.open(Path(path).parent / img["uri"]).convert("RGBA"), np.float32) / 255.0
            else:
                v = doc["bufferViews"][img["bufferView"]]
                data = blob[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]
                a = np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"), np.float32) / 255.0
            if srgb:
                a = np.concatenate([srgb_decode(a[..., :3]), a[..., 3:]], axis=-1)
            s = doc["samplers"][t.get("sampler", 0)]
            cache[key] = (a, s.get("wrapS", 10497) == 10497, s.get("wrapT", 10497) == 10497)
        return cache[key]

    def from_y_up(a):
        return np.stack([a[:, 0], -a[:, 2], a[:, 1]], 1)

    out = []
    for mesh in doc["meshes"]:
        for prim in mesh["primitives"]:
            attrs = prim["attributes"]
            V = from_y_up(glb_accessor(doc, blob, attrs["POSITION"]).astype(np.float64))
            N = from_y_up(glb_accessor(doc, blob, attrs["NORMAL"]).astype(np.float32))
            F = glb_accessor(doc, blob, prim["indices"]).reshape(-1, 3).astype(np.int64)
            UV = glb_accessor(doc, blob, attrs["TEXCOORD_0"]).astype(np.float32) if "TEXCOORD_0" in attrs else None
            T = None
            if "TANGENT" in attrs:
                t = glb_accessor(doc, blob, attrs["TANGENT"]).astype(np.float32)
                T = np.c_[from_y_up(t[:, :3]), t[:, 3]]
            C = None
            m = doc["materials"][prim.get("material", 0)]
            # in a file for Unreal, COLOR_0 holds the wind's data, not a colour
            if "COLOR_0" in attrs and m.get("extras", {}).get("color0") != "wind":
                span = 255.0 if doc["accessors"][attrs["COLOR_0"]]["componentType"] == 5121 else 65535.0
                C = glb_accessor(doc, blob, attrs["COLOR_0"]).astype(np.float32) / span
            pbr = m.get("pbrMetallicRoughness", {})
            base = alpha = normal = orm = None
            if "baseColorTexture" in pbr:
                a, ws, wt = image(pbr["baseColorTexture"]["index"], True)
                base = Texture(a[..., :3], ws, wt)
                if m.get("alphaMode") == "MASK":
                    alpha = (_mips(a[..., 3]), ws, wt)
            if "normalTexture" in m:
                a, ws, wt = image(m["normalTexture"]["index"], False)
                normal = Texture(a[..., :3] * 2.0 - 1.0, ws, wt)
            if "metallicRoughnessTexture" in pbr:
                a, ws, wt = image(pbr["metallicRoughnessTexture"]["index"], False)
                orm = Texture(a[..., :3], ws, wt)
            dt = m.get("extensions", {}).get("KHR_materials_diffuse_transmission", {})
            out.append(Primitive(mesh.get("name", ""), V, N, F, UV, T, C, base, normal, orm, pbr.get("baseColorFactor", (1, 1, 1, 1)),
                                 pbr.get("roughnessFactor", 1.0), pbr.get("metallicFactor", 0.0), alpha, m.get("alphaCutoff", 0.5),
                                 bool(m.get("doubleSided", False)), dt.get("diffuseTransmissionFactor", 0.0), dt.get("diffuseTransmissionColorFactor", (1, 1, 1)),
                                 m.get("normalTexture", {}).get("scale", 1.0)))
    return out


# -- rasterising ----------------------------------------------------------------------------------
@njit(cache=True)
def _raster(sx, sy, depth, w, F, W, H, zbuf, pbuf, tbuf, b0, b1, prim_id, cull, uv, va, alpha_map, cutoff, use_alpha):
    """Into the buffers.  ``depth``: larger is nearer, linear on the screen.  ``w``: 1 / view depth,
    for perspective-correct weights (1 for an orthographic view).  Triangles between pixel centres
    are drawn as one sample with probability equal to their area, so a thin twig covers the share
    of the picture it really does."""
    ah, aw = alpha_map.shape[0], alpha_map.shape[1]
    state = np.uint64(88172645463325252) + np.uint64(prim_id)
    for t in range(F.shape[0]):
        i0, i1, i2 = F[t, 0], F[t, 1], F[t, 2]
        x0, y0, x1, y1, x2, y2 = sx[i0], sy[i0], sx[i1], sy[i1], sx[i2], sy[i2]
        if not (x0 == x0 and x1 == x1 and x2 == x2):
            continue
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if area == 0.0:
            continue
        if cull and area > 0.0:   # y grows down the screen: a face turned to the camera comes out negative
            continue
        state ^= state << np.uint64(13)
        state ^= state >> np.uint64(7)
        state ^= state << np.uint64(17)
        rnd = float(state >> np.uint64(11)) / 9007199254740992.0
        xlo = max(int(np.ceil(min(x0, x1, x2) - 0.5)), 0)
        xhi = min(int(np.floor(max(x0, x1, x2) - 0.5)), W - 1)
        ylo = max(int(np.ceil(min(y0, y1, y2) - 0.5)), 0)
        yhi = min(int(np.floor(max(y0, y1, y2) - 0.5)), H - 1)
        if xhi < xlo or yhi < ylo:
            if rnd >= 0.5 * abs(area):
                continue
            state ^= state << np.uint64(13)
            state ^= state >> np.uint64(7)
            state ^= state << np.uint64(17)
            r = float(state >> np.uint64(11)) / 9007199254740992.0
            px = x0 + (x1 - x0) * r
            py = y0 + (y1 - y0) * r
            ix, iy = int(np.floor(px)), int(np.floor(py))
            if ix < 0 or iy < 0 or ix >= W or iy >= H:
                continue
            xlo, xhi, ylo, yhi = ix, ix, iy, iy
            fixed = True
        else:
            fixed = False
        inv = 1.0 / area
        for y in range(ylo, yhi + 1):
            py = y + 0.5
            for x in range(xlo, xhi + 1):
                px = x + 0.5
                l1 = ((px - x0) * (y2 - y0) - (x2 - x0) * (py - y0)) * inv
                l2 = ((x1 - x0) * (py - y0) - (px - x0) * (y1 - y0)) * inv
                l0 = 1.0 - l1 - l2
                if fixed:
                    l0, l1, l2 = max(l0, 0.0), max(l1, 0.0), max(l2, 0.0)
                    s = l0 + l1 + l2
                    l0, l1, l2 = l0 / s, l1 / s, l2 / s
                elif l0 < 0.0 or l1 < 0.0 or l2 < 0.0:
                    continue
                d = l0 * depth[i0] + l1 * depth[i1] + l2 * depth[i2]
                k = y * W + x
                if d <= zbuf[k]:
                    continue
                g = l0 * w[i0] + l1 * w[i1] + l2 * w[i2]
                p0 = l0 * w[i0] / g
                p1 = l1 * w[i1] / g
                p2 = 1.0 - p0 - p1
                if use_alpha:
                    u = p0 * uv[i0, 0] + p1 * uv[i1, 0] + p2 * uv[i2, 0]
                    v = p0 * uv[i0, 1] + p1 * uv[i1, 1] + p2 * uv[i2, 1]
                    ax = int(np.floor(u * aw)) % aw
                    ay = int(np.floor(v * ah)) % ah
                    a = alpha_map[ay, ax] * (p0 * va[i0] + p1 * va[i1] + p2 * va[i2])
                    if a < cutoff:
                        continue
                zbuf[k] = d
                pbuf[k] = prim_id
                tbuf[k] = t
                b0[k] = p0
                b1[k] = p1


class View:
    """A camera: a perspective view from ``eye`` towards ``target`` with a vertical field of view,
    or an orthographic one (``ortho_half_h`` metres half height) along ``eye`` -> ``target``."""

    def __init__(self, eye, target, W, H, fov_deg=30.0, ortho_half_h=None, up=(0.0, 0.0, 1.0)):
        self.eye = np.asarray(eye, float)
        self.target = np.asarray(target, float)
        self.W, self.H = int(W), int(H)
        f = self.target - self.eye
        self.dist = float(np.linalg.norm(f))
        self.fwd = f / self.dist
        r = np.cross(self.fwd, np.asarray(up, float))
        if np.linalg.norm(r) < 1e-6:
            r = np.cross(self.fwd, np.array([0.0, 1.0, 0.0]))
        self.right = r / np.linalg.norm(r)
        self.up = np.cross(self.right, self.fwd)
        self.ortho = ortho_half_h
        self.scale = self.H / 2.0 / (np.tan(np.radians(fov_deg) / 2.0)) if ortho_half_h is None else self.H / 2.0 / ortho_half_h

    def project(self, V):
        d = V - self.eye
        xc = d @ self.right
        yc = d @ self.up
        zc = d @ self.fwd
        if self.ortho is not None:
            return (self.W / 2.0 + xc * self.scale).astype(np.float64), (self.H / 2.0 - yc * self.scale).astype(np.float64), (-zc).astype(np.float64), np.ones(len(V))
        zs = np.where(zc > 0.02, zc, np.nan)
        return self.W / 2.0 + xc / zs * self.scale, self.H / 2.0 - yc / zs * self.scale, 1.0 / zs, 1.0 / zs


class GBuffer:
    def __init__(self, W, H):
        self.W, self.H = W, H
        n = W * H
        self.z = np.full(n, -np.inf, np.float32)
        self.p = np.full(n, -1, np.int16)
        self.t = np.zeros(n, np.int32)
        self.b0 = np.zeros(n, np.float32)
        self.b1 = np.zeros(n, np.float32)


_NO_ALPHA = np.zeros((1, 1), np.float32)
_NO_UV = np.zeros((1, 2), np.float32)
_NO_VA = np.zeros(1, np.float32)


def rasterise(prims: list, view: View, gb: GBuffer, casters_only: bool = False):
    for i, p in enumerate(prims):
        if casters_only and getattr(p, "no_cast", False):
            continue
        sx, sy, depth, w = view.project(p.V)
        use_alpha = p.alpha is not None and p.UV is not None
        amap = _NO_ALPHA
        if use_alpha:
            # the alpha mip that suits this view of this mesh, from a sample of its triangles
            F = p.F[:: max(len(p.F) // 2000, 1)]
            dx = sx[F[:, 1]] - sx[F[:, 0]]
            dy = sy[F[:, 1]] - sy[F[:, 0]]
            ex = sx[F[:, 2]] - sx[F[:, 0]]
            ey = sy[F[:, 2]] - sy[F[:, 0]]
            area_s = np.nanmedian(np.abs(dx * ey - dy * ex)) + 1e-9
            du = p.UV[F[:, 1]] - p.UV[F[:, 0]]
            dv = p.UV[F[:, 2]] - p.UV[F[:, 0]]
            mips = p.alpha[0]
            area_t = np.median(np.abs(du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0])) * mips[0].shape[0] * mips[0].shape[1] + 1e-9
            lod = int(np.clip(0.5 * np.log2(area_t / area_s), 0, len(mips) - 1))
            amap = mips[lod].astype(np.float32)
        uv = p.UV.astype(np.float32) if use_alpha else _NO_UV
        va = (p.C[:, 3].astype(np.float32) * p.factor[3]) if use_alpha and p.C is not None else (np.full(len(p.V), float(p.factor[3]), np.float32) if use_alpha else _NO_VA)
        _raster(sx.astype(np.float64), sy.astype(np.float64), depth.astype(np.float64), w.astype(np.float64), p.F, view.W, view.H, gb.z, gb.p, gb.t, gb.b0, gb.b1,
                i, not p.double, uv, va, amap, float(p.cutoff), use_alpha)


class Lights:
    """A sun and a sky, with occlusion from depth maps along the light directions."""

    def __init__(self, prims: list, sun_dir, res=2048, sky_res=768, sky_dirs=10, focus=None):
        """``focus``: (centre, radius) to keep the depth maps to, for a close view."""
        self.sun_dir = np.asarray(sun_dir, float) / np.linalg.norm(sun_dir)
        V = np.concatenate([p.V for p in prims if not getattr(p, "no_cast", False)] or [p.V for p in prims])
        lo, hi = V.min(0), V.max(0)
        self.centre = 0.5 * (lo + hi)
        self.radius = float(np.linalg.norm(hi - lo)) * 0.55 + 0.1
        if focus is not None:
            self.centre, self.radius = np.asarray(focus[0], float), float(focus[1])
        self.maps = []
        self.maps.append(self._map(prims, self.sun_dir, res))
        # a cosine-weighted spiral of sky directions
        self.sky_maps = []
        for k in range(sky_dirs):
            z = np.sqrt((k + 0.5) / sky_dirs)
            s = np.sqrt(max(1.0 - z * z, 0.0))
            a = k * 2.39996
            self.sky_maps.append(self._map(prims, np.array([s * np.cos(a), s * np.sin(a), z]), sky_res))

    def _map(self, prims, direction, res):
        eye = self.centre + direction * self.radius * 2.0
        v = View(eye, self.centre, res, res, ortho_half_h=self.radius)
        gb = GBuffer(res, res)
        rasterise(prims, v, gb, casters_only=True)
        return v, gb.z.reshape(res, res)

    @staticmethod
    def _visible(mapping, P, bias, soft=False):
        v, z = mapping
        sx, sy, d, _ = v.project(P)
        H, W = z.shape
        if not soft:
            ix = np.clip(sx.astype(np.int64), 0, W - 1)
            iy = np.clip(sy.astype(np.int64), 0, H - 1)
            return (d + bias >= z[iy, ix]).astype(np.float32)
        out = np.zeros(len(P), np.float32)
        for ox, oy in ((-1.2, -0.4), (0.4, -1.2), (1.2, 0.4), (-0.4, 1.2), (0.0, 0.0)):
            ix = np.clip((sx + ox).astype(np.int64), 0, W - 1)
            iy = np.clip((sy + oy).astype(np.int64), 0, H - 1)
            out += (d + bias >= z[iy, ix]).astype(np.float32)
        return out / 5.0

    def sun_visible(self, P, bias):
        return self._visible(self.maps[0], P, bias, soft=True)

    def sky_visible(self, P, bias):
        out = np.zeros(len(P), np.float32)
        for m in self.sky_maps:
            out += self._visible(m, P, bias, soft=True)
        return out / max(len(self.sky_maps), 1)


SUN = np.array([1.34, 1.24, 1.06], np.float32)
SKY_UP = np.array([0.42, 0.56, 0.78], np.float32)
SKY_LOW = np.array([0.56, 0.60, 0.62], np.float32)
BOUNCE = np.array([0.20, 0.20, 0.14], np.float32)


def _shade_primitive(p: Primitive, idx: np.ndarray, gb: GBuffer, view: View, lights: Lights | None, out_rgb, albedo_out=None, normal_out=None):
    t = gb.t[idx]
    l0 = gb.b0[idx][:, None]
    l1 = gb.b1[idx][:, None]
    l2 = 1.0 - l0 - l1
    F = p.F[t]
    i0, i1, i2 = F[:, 0], F[:, 1], F[:, 2]

    def lerp(a):
        return a[i0] * l0 + a[i1] * l1 + a[i2] * l2

    P = lerp(p.V)
    N = lerp(p.N)
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    if p.UV is not None:
        uv = lerp(p.UV)
        # level of detail from each triangle's texture and screen areas
        sx, sy, _, _ = view.project(p.V)
        ax = sx[i1] - sx[i0]
        ay = sy[i1] - sy[i0]
        bx = sx[i2] - sx[i0]
        by = sy[i2] - sy[i0]
        sarea = np.abs(ax * by - ay * bx) + 1e-9
        du, dv = p.UV[i1] - p.UV[i0], p.UV[i2] - p.UV[i0]
        tarea = np.abs(du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0])
        base_mip = p.base.mips[0].shape if p.base is not None else (1, 1)
        lod = 0.5 * np.log2(np.maximum(tarea * base_mip[0] * base_mip[1] / sarea, 1e-9))
    else:
        uv, lod = None, None
    col = np.broadcast_to(p.factor[:3], (len(idx), 3)).copy()
    if p.base is not None:
        col = col * p.base.sample(uv, lod)
    if p.C is not None:
        col = col * lerp(p.C)[:, :3]
    rough = np.full(len(idx), float(p.rough), np.float32)
    ao = np.ones(len(idx), np.float32)
    if p.orm is not None:
        o = p.orm.sample(uv, lod)
        rough = rough * o[:, 1]
        ao = o[:, 0]
    if p.normal is not None and p.T is not None:
        t3 = lerp(p.T[:, :3])
        t3 = t3 - (t3 * N).sum(1, keepdims=True) * N
        t3 = t3 / np.maximum(np.linalg.norm(t3, axis=1, keepdims=True), 1e-9)
        b3 = np.cross(N, t3) * p.T[i0, 3:4]
        m = p.normal.sample(uv, lod)
        m[:, :2] *= float(p.normal_scale)
        Ns = t3 * m[:, 0:1] + b3 * m[:, 1:2] + N * m[:, 2:3]
        Ns = Ns / np.maximum(np.linalg.norm(Ns, axis=1, keepdims=True), 1e-9)
    else:
        Ns = N
    if view.ortho is not None:
        Vv = np.broadcast_to(-view.fwd, P.shape)
    else:
        Vv = view.eye - P
        Vv = Vv / np.maximum(np.linalg.norm(Vv, axis=1, keepdims=True), 1e-9)
    # for a bake: the normal as it is on the part, not turned to the viewer, so the far card from one
    # side lights the same as the card from another
    if albedo_out is not None:
        # a bake keeps the crown's own soft shade, the one thing a card can't get from the lights
        albedo_out[idx] = col if lights is None else col * (0.35 + 0.65 * lights.sky_visible(P + N * 0.015, 0.05))[:, None]
    if normal_out is not None:
        normal_out[idx] = Ns.astype(np.float32)
    if out_rgb is None:
        return
    if p.double:
        flip = (N * Vv).sum(1) < 0.0
        Ns = np.where(flip[:, None], -Ns, Ns)
        N = np.where(flip[:, None], -N, N)
    L = lights.sun_dir[None, :]
    NoL = (Ns * L).sum(1)
    # a small offset along the true normal keeps a surface from shadowing itself
    Pb = P + N * 0.015
    bias = 0.03
    vis = lights.sun_visible(Pb, bias)
    sky = lights.sky_visible(Pb, 0.05)
    t_up = np.clip(0.5 + 0.5 * Ns[:, 2:3], 0.0, 1.0)
    amb_front = (BOUNCE * (1.0 - t_up) + (SKY_LOW + (SKY_UP - SKY_LOW) * t_up) * t_up) * (0.3 + 0.7 * sky[:, None]) * ao[:, None]
    f = float(p.dt_factor)
    front = np.clip(NoL, 0.0, 1.0)[:, None] * vis[:, None] * SUN
    diffuse = (1.0 - f) * col * (front + amb_front)
    if f > 0.0:
        back = np.clip(-NoL, 0.0, 1.0)[:, None] * vis[:, None] * SUN
        t_low = 1.0 - t_up
        amb_back = (BOUNCE * t_up + (SKY_LOW + (SKY_UP - SKY_LOW) * t_low) * t_low) * (0.3 + 0.7 * sky[:, None])
        diffuse = diffuse + f * p.dt_color * (back + amb_back)
    # sun highlight, GGX with F0 = 0.04
    H = L + Vv
    H = H / np.maximum(np.linalg.norm(H, axis=1, keepdims=True), 1e-9)
    NoH = np.clip((Ns * H).sum(1), 0.0, 1.0)
    NoV = np.clip((Ns * Vv).sum(1), 1e-3, 1.0)
    VoH = np.clip((Vv * H).sum(1), 0.0, 1.0)
    a2 = (rough * rough) ** 2
    D = a2 / (np.pi * (NoH * NoH * (a2 - 1.0) + 1.0) ** 2 + 1e-6)
    k = (rough + 1.0) ** 2 / 8.0
    Lc = np.clip(NoL, 0.0, 1.0)
    Gv = NoV / (NoV * (1.0 - k) + k)
    Gl = Lc / (Lc * (1.0 - k) + k)
    Fr = 0.04 + 0.96 * (1.0 - VoH) ** 5
    spec = (D * Gv * Gl * Fr / (4.0 * NoV * np.maximum(Lc, 1e-3) + 1e-6)) * Lc * vis
    env = 0.04 * (0.25 + 0.75 * (1.0 - rough)) * (0.5 + 0.5 * sky)
    out_rgb[idx] = diffuse + spec[:, None] * SUN + (env * ao)[:, None] * SKY_UP


def make_ground(radius: float, colour=(0.055, 0.05, 0.035), res: int = 80, seed: int = 3) -> Primitive:
    """A flat ground: darker than anything in the tree, so stems stand out; leaf litter is left out."""
    g = np.linspace(-radius, radius, res)
    X, Y = np.meshgrid(g, g, indexing="ij")
    V = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], 1)
    i, j = np.meshgrid(np.arange(res - 1), np.arange(res - 1), indexing="ij")
    a = (i * res + j).ravel()
    F = np.concatenate([np.stack([a, a + res, a + res + 1], 1), np.stack([a, a + res + 1, a + 1], 1)]).astype(np.int64)
    rng = np.random.default_rng(seed)
    C = np.ones((len(V), 4), np.float32)
    C[:, :3] = np.asarray(colour, np.float32) * (0.75 + 0.5 * rng.random((len(V), 1), dtype=np.float32))
    p = Primitive("ground", V, np.tile(np.array([0.0, 0.0, 1.0], np.float32), (len(V), 1)), F, C=C, rough=1.0)
    p.no_cast = True
    return p


def render(prims: list, view: View, lights: Lights, ss: int = 2, sky: bool = True, exposure: float = 1.0) -> np.ndarray:
    """A picture, as uint8 RGB, height view.H, width view.W; ``ss`` samples a side per pixel."""
    v = View(view.eye, view.target, view.W * ss, view.H * ss, ortho_half_h=view.ortho)
    v.scale = view.scale * ss
    gb = GBuffer(v.W, v.H)
    rasterise(prims, v, gb)
    rgb = np.zeros((v.W * v.H, 3), np.float32)
    for i, p in enumerate(prims):
        idx = np.nonzero(gb.p == i)[0]
        if idx.size:
            _shade_primitive(p, idx, gb, v, lights, rgb)
    img = rgb.reshape(v.H, v.W, 3) * float(exposure)
    empty = (gb.p < 0).reshape(v.H, v.W)
    if sky:
        rows = (np.arange(v.H) / max(v.H - 1, 1))[:, None, None]
        grad = (1 - rows) * np.array([0.42, 0.58, 0.82]) + rows * np.array([0.80, 0.86, 0.92])
        img = np.where(empty[:, :, None], grad, img)
    img = img.reshape(view.H, ss, view.W, ss, 3).mean((1, 3))
    # a gentle shoulder, so a white stem in sun keeps its detail
    img = np.where(img < 0.75, img, 0.75 + 0.25 * (1.0 - np.exp(-(img - 0.75) / 0.25)))
    return (srgb_encode(img) * 255.0 + 0.5).astype(np.uint8)


def bake_views(prims: list, view: View, ss: int = 3, lights: Lights | None = None) -> dict:
    """Albedo, normal and coverage of a view with no sun in it, for far cards.  Each pixel is the
    average of the samples that hit something.  With ``lights``, colour carries the sky occlusion."""
    v = View(view.eye, view.target, view.W * ss, view.H * ss, ortho_half_h=view.ortho)
    v.scale = view.scale * ss
    gb = GBuffer(v.W, v.H)
    rasterise(prims, v, gb)
    alb = np.zeros((v.W * v.H, 3), np.float32)
    nrm = np.zeros((v.W * v.H, 3), np.float32)
    for i, p in enumerate(prims):
        idx = np.nonzero(gb.p == i)[0]
        if idx.size:
            _shade_primitive(p, idx, gb, v, lights, None, alb, nrm)
    hit = (gb.p >= 0).astype(np.float32).reshape(v.H, v.W, 1)
    a = hit.reshape(view.H, ss, view.W, ss, 1).sum((1, 3))
    col = (alb.reshape(v.H, v.W, 3) * hit).reshape(view.H, ss, view.W, ss, 3).sum((1, 3)) / np.maximum(a, 1e-6)
    n = (nrm.reshape(v.H, v.W, 3) * hit).reshape(view.H, ss, view.W, ss, 3).sum((1, 3)) / np.maximum(a, 1e-6)
    return {"albedo": col, "normal": n, "coverage": a[..., 0] / float(ss * ss)}
