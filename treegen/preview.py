"""Silhouette previews: side and top views with line width = branch diameter."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

MIN_LINEWIDTH_PT = 0.3


def _positions_at(model, age: int) -> np.ndarray:
    """Node positions at the end of year ``age`` (branches bend over time;
    the nearest stored keyframe at or before ``age`` is used)."""
    keys = sorted(k for k in model.keyframes if k <= age)
    if not keys:
        return model.tree.pos
    return model.keyframes[keys[-1]]


def segments_at_age(model, age: int):
    """Internodes present at the end of year ``age``: (p0, p1, radius)."""
    T = model.tree
    H = model.radius_history[age]
    P = _positions_at(model, age)
    idx = np.arange(1, min(len(H), len(P)))
    present = (T.birth[idx] <= age) & ((T.death[idx] < 0) | (T.death[idx] > age))
    idx = idx[present]
    return P[T.parent[idx]].astype(float), P[idx].astype(float), H[idx].astype(float)


def root_segments_at_age(model, age: int):
    R = model.roots.tree
    H = model.roots.radius_history[age]
    idx = np.arange(1, len(H))
    present = (R.birth[idx] <= age) & ((R.death[idx] < 0) | (R.death[idx] > age))
    idx = idx[present]
    return R.pos[R.parent[idx]], R.pos[idx], H[idx].astype(float)


def _draw(ax, p0, p1, r, view: str, pts_per_m: float):
    if view == "side":
        a, b = p0[:, [0, 2]], p1[:, [0, 2]]
    elif view == "side_ns":
        a, b = p0[:, [1, 2]], p1[:, [1, 2]]
    else:
        a, b = p0[:, [0, 1]], p1[:, [0, 1]]
    order = np.argsort(-r)  # thick first
    lw = np.maximum(2.0 * r[order] * pts_per_m, MIN_LINEWIDTH_PT)
    lc = LineCollection(np.stack([a[order], b[order]], 1), linewidths=lw, colors="black", capstyle="round")
    ax.add_collection(lc)


def _frame(fig_w_in, fig_h_in, xlim, ylim, dpi):
    fig = plt.figure(figsize=(fig_w_in, fig_h_in), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_facecolor("white")
    return fig, ax


def _scale_bar(ax, x0, y0, length, label):
    ax.plot([x0, x0 + length], [y0, y0], color="0.3", lw=1.2)
    ax.text(x0 + length / 2, y0, label, ha="center", va="bottom", fontsize=7, color="0.3")


def render_age(model, age: int, out_dir: Path, dpi: int = 200, height_in: float = 8.0):
    p0, p1, r = segments_at_age(model, age)
    st = model.stats[age]
    pts = np.concatenate([p0, p1])
    lo, hi = pts.min(0), pts.max(0)
    pad = 0.06 * max(hi[2], 1.0)
    files = []
    label = (f"age {age}   H {st['height_m']:.1f} m   "
             f"DBH {st['dbh_cm']:.1f} cm   " if st["dbh_cm"] is not None else f"age {age}   H {st['height_m']:.1f} m   ")
    label += f"crown {st['crown_width_m']:.1f} m"
    # side view (looking north): x horizontal, z vertical
    half = max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])) + pad
    xlim = (-half, half)
    ylim = (-pad, hi[2] + pad)
    w_in = height_in * (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])
    for view, name in (("side", "side"), ("side_ns", "side_ns")):
        fig, ax = _frame(w_in, height_in, xlim, ylim, dpi)
        ppm = 72.0 * height_in / (ylim[1] - ylim[0])
        ax.plot(xlim, [0, 0], color="0.75", lw=0.6)
        _draw(ax, p0, p1, r, view, ppm)
        bar = 1.0 if hi[2] < 12 else 5.0
        _scale_bar(ax, xlim[0] + pad * 0.5, ylim[0] + pad * 0.3, bar, f"{bar:g} m")
        ax.text(xlim[0] + pad * 0.5, ylim[1] - pad * 0.3, label, fontsize=7, va="top", color="0.2")
        f = out_dir / f"{name}_age{age:02d}.png"
        fig.savefig(f, dpi=dpi, facecolor="white")
        plt.close(fig)
        files.append(f)
    # top view
    fig, ax = _frame(height_in * 0.75, height_in * 0.75, (-half, half), (-half, half), dpi)
    ppm = 72.0 * height_in * 0.75 / (2 * half)
    _draw(ax, p0, p1, r, "top", ppm)
    bar = 1.0 if half < 6 else 2.0
    _scale_bar(ax, -half + pad * 0.5, -half + pad * 0.3, bar, f"{bar:g} m")
    ax.text(-half + pad * 0.5, half - pad * 0.3, label + "   (top, north up)", fontsize=6, va="top", color="0.2")
    f = out_dir / f"top_age{age:02d}.png"
    fig.savefig(f, dpi=dpi, facecolor="white")
    plt.close(fig)
    files.append(f)
    return files


def render_summary(model, ages, out_dir: Path, dpi: int = 160):
    """All ages side by side at one common scale (side row + top row)."""
    segs = [segments_at_age(model, a) for a in ages]
    allp = np.concatenate([np.concatenate([s[0], s[1]]) for s in segs])
    H = allp[:, 2].max()
    half = max(np.abs(allp[:, :2]).max(), 1.0) * 1.05
    pad = 0.04 * H
    panel_w = 2 * half
    total_w = panel_w * len(ages)
    height_in = 7.0
    side_h = H + 2 * pad
    w_in = height_in * total_w / (side_h + panel_w)
    fig = plt.figure(figsize=(w_in, height_in), dpi=dpi, facecolor="white")
    ppm = 72.0 * height_in / (side_h + panel_w)
    for i, (a, (p0, p1, r)) in enumerate(zip(ages, segs)):
        ax = fig.add_axes([i / len(ages), panel_w / (side_h + panel_w), 1 / len(ages), side_h / (side_h + panel_w)])
        ax.set_xlim(-half, half)
        ax.set_ylim(-pad, H + pad)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.plot([-half, half], [0, 0], color="0.75", lw=0.5)
        _draw(ax, p0, p1, r, "side", ppm)
        st = model.stats[a]
        ax.text(0, H + pad * 0.2, f"age {a}: {st['height_m']:.1f} m", ha="center", va="top", fontsize=7)
        ax2 = fig.add_axes([i / len(ages), 0, 1 / len(ages), panel_w / (side_h + panel_w)])
        ax2.set_xlim(-half, half)
        ax2.set_ylim(-half, half)
        ax2.set_aspect("equal")
        ax2.axis("off")
        _draw(ax2, p0, p1, r, "top", ppm)
    f = out_dir / "summary.png"
    fig.savefig(f, dpi=dpi, facecolor="white")
    plt.close(fig)
    return f


def render_previews(model, ages, out_dir: Path):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ages = [a for a in ages if a <= model.year]
    files = []
    for a in ages:
        files += render_age(model, a, out_dir)
    if ages:
        files.append(render_summary(model, ages, out_dir))
    return files


# --- roots ------------------------------------------------------------------
def render_roots_side(model, ages, out_dir: Path, dpi: int = 160):
    """Side view (east-west) of crown and roots at several ages, one common
    scale, ground line at z = 0."""
    data = [(a, segments_at_age(model, a), root_segments_at_age(model, a)) for a in ages]
    allp = np.concatenate([np.concatenate([s_[0], s_[1], r_[0], r_[1]]) for _, s_, r_ in data])
    half = max(np.abs(allp[:, 0]).max(), 1.0) * 1.05
    top, bot = allp[:, 2].max() * 1.03, min(allp[:, 2].min() * 1.15, -0.5)
    panel_w = 2 * half
    h = top - bot
    height_in = 7.0
    w_in = height_in * panel_w * len(ages) / h
    fig = plt.figure(figsize=(w_in, height_in), dpi=dpi, facecolor="white")
    ppm = 72.0 * height_in / h
    for i, (a, (p0, p1, r), (q0, q1, rr)) in enumerate(data):
        ax = fig.add_axes([i / len(ages), 0, 1 / len(ages), 1])
        ax.set_xlim(-half, half)
        ax.set_ylim(bot, top)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.axhspan(bot, 0, color="#efe6da", zorder=0)
        ax.plot([-half, half], [0, 0], color="0.4", lw=0.8)
        _draw(ax, p0, p1, r, "side", ppm)
        if len(q0):
            order = np.argsort(-rr)
            lw = np.maximum(2.0 * rr[order] * ppm, MIN_LINEWIDTH_PT)
            ax.add_collection(LineCollection(np.stack([q0[order][:, [0, 2]], q1[order][:, [0, 2]]], 1),
                                             linewidths=lw, colors="#5a3a22", capstyle="round"))
        st = model.stats[a]
        rs = st.get("roots") or {}
        ax.text(0, top, f"age {a}: H {st['height_m']:.1f} m, roots to {rs.get('root_max_depth_m', 0):.2f} m deep, "
                        f"{rs.get('root_spread_max_m', 0):.1f} m out", ha="center", va="top", fontsize=6)
    f = out_dir / "roots_side.png"
    fig.savefig(f, dpi=dpi, facecolor="white")
    plt.close(fig)
    return f


def render_roots_top(model, age: int, out_dir: Path, dpi: int = 160):
    """Top view of the root system with the crown outline (convex hull of the
    projected crown) drawn over it."""
    from scipy.spatial import ConvexHull
    q0, q1, rr = root_segments_at_age(model, age)
    p0, p1, _ = segments_at_age(model, age)
    crown = np.concatenate([p0, p1])[:, :2]
    pts = np.concatenate([q0[:, :2], q1[:, :2], crown])
    half = np.abs(pts).max() * 1.08
    fig, ax = _frame(7.0, 7.0, (-half, half), (-half, half), dpi)
    ax.set_facecolor("#efe6da")
    ax.add_patch(plt.Rectangle((-half, -half), 2 * half, 2 * half, color="#efe6da", zorder=0))
    ppm = 72.0 * 7.0 / (2 * half)
    order = np.argsort(-rr)
    lw = np.maximum(2.0 * rr[order] * ppm, MIN_LINEWIDTH_PT)
    depth = -0.5 * (q0[order, 2] + q1[order, 2])
    cmap = plt.get_cmap("copper_r")
    cols = cmap(np.clip(depth / max(float(depth.max()), 1e-6), 0, 1) * 0.8 + 0.1)
    ax.add_collection(LineCollection(np.stack([q0[order][:, :2], q1[order][:, :2]], 1), linewidths=lw, colors=cols))
    if len(crown) >= 3:
        hull = ConvexHull(crown)
        hp = crown[np.r_[hull.vertices, hull.vertices[0]]]
        ax.plot(hp[:, 0], hp[:, 1], color="#2b7a2b", lw=1.6)
    rs = model.stats[age].get("roots") or {}
    ax.text(-half * 0.95, half * 0.95, f"age {age}: roots (darker = deeper) and crown outline (green)\n"
            f"root spread max {rs.get('root_spread_max_m', 0):.1f} m, 95% of length within {rs.get('root_spread_95pct_m', 0):.1f} m; "
            f"crown width {model.stats[age]['crown_width_m']:.1f} m", fontsize=7, va="top")
    f = out_dir / f"roots_top_age{age:02d}.png"
    fig.savefig(f, dpi=dpi, facecolor="white")
    plt.close(fig)
    return f


# --- shaded rendering ---------------------------------------------------------
def _camera(azim_deg, elev_deg):
    a, e = np.radians(azim_deg), np.radians(elev_deg)
    fwd = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])  # towards the camera
    right = np.cross([0.0, 0.0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    return fwd, right, up


SKY_TOP = np.array([0.55, 0.70, 0.88])
SKY_HORIZON = np.array([0.88, 0.92, 0.95])
GROUND = np.array([0.36, 0.38, 0.24])
ROOT = np.array([0.42, 0.30, 0.20])
LEAF = np.array([0.24, 0.40, 0.13])


class Rasterizer:
    """Z-buffer triangle rasterizer with supersampling and simple sky light.

    Triangles that cover pixel centres are rasterized exactly (barycentric
    coverage, interpolated depth and normal).  Sub-pixel triangles (fine
    twigs) are drawn as a single sample with probability equal to their
    projected area, so a twig covers the fraction of a pixel it really
    does; supersampling then averages that coverage.  Back faces are culled.
    Light: a hemispherical sky (blue above, ground bounce below) and a sun.

    Meshes are added a chunk at a time (``add``), so a tree is rendered
    while it streams to disk.  Bark colour follows branch size: white birch
    bark on stem and limbs, dark red-brown on fine twigs; roots are brown.
    """

    def __init__(self, center, half_w, half_h, azim, elev, res_h=1400, supersample=2, seed=0, eye=None):
        """Orthographic view of the box ``half_w`` x ``half_h`` around
        ``center``; with ``eye`` (a camera position), a perspective view from
        there towards ``center`` whose image plane through ``center`` spans
        that box (a photograph taken from ``eye``)."""
        self.eye = None if eye is None else np.asarray(eye, float)
        if self.eye is not None:
            v = self.eye - np.asarray(center, float)
            azim = float(np.degrees(np.arctan2(v[1], v[0])))
            elev = float(np.degrees(np.arctan2(v[2], np.hypot(v[0], v[1]))))
            self.dist = float(np.linalg.norm(v))
        self.fwd, self.right, self.up = _camera(azim, elev)
        self.center = np.asarray(center, float)
        self.ss = int(supersample)
        self.out_h = int(res_h)
        self.out_w = int(round(res_h * half_w / half_h))
        self.H, self.W = self.out_h * self.ss, self.out_w * self.ss
        self.half_w, self.half_h = float(half_w), float(half_h)
        self.px = 2.0 * self.half_h / self.H
        a = np.radians(azim + 35.0)
        self.sun = np.array([0.55 * np.cos(a), 0.55 * np.sin(a), 0.83])
        self.sun /= np.linalg.norm(self.sun)
        self.zbuf = np.full(self.H * self.W, -np.inf, np.float32)
        self.img = np.zeros((self.H * self.W, 3), np.float32)
        self.rng = np.random.default_rng(seed)

    def _shade(self, N, base, flip=True):
        N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        if flip:
            N = np.where(((N @ self.fwd) < 0)[:, None], -N, N)  # thin open shells: light the side we see
        t = (0.5 + 0.5 * N[:, 2])[:, None]
        sky = (1 - t) * (0.6 * GROUND + 0.15) + t * SKY_TOP
        sun = np.clip(N @ self.sun, 0, 1)[:, None]
        return base * (0.55 * sky + 0.75 * sun)

    def _resolve(self, pix, dep, col):
        if pix.size == 0:
            return
        order = np.lexsort((dep, pix))
        pix, dep, col = pix[order], dep[order], col[order]
        last = np.r_[pix[1:] != pix[:-1], True]
        pix, dep, col = pix[last], dep[last], col[last]
        better = dep > self.zbuf[pix]
        self.zbuf[pix[better]] = dep[better]
        self.img[pix[better]] = col[better]

    def _colours(self, md, kind, idx):
        if kind == "root":
            return np.tile(ROOT, (len(idx), 1))
        if kind == "ground":
            return np.tile(GROUND, (len(idx), 1))
        if kind == "leaf":
            return np.tile(LEAF, (len(idx), 1))
        rad = md.attributes["radius"][idx].astype(float)
        t = np.clip((np.log(np.maximum(rad, 1e-4)) - np.log(0.002)) / (np.log(0.03) - np.log(0.002)), 0, 1)[:, None]
        return (1 - t) * np.array([0.30, 0.17, 0.12]) + t * np.array([0.90, 0.89, 0.85])

    def add(self, md, kind="shoot", face_mask=None, batch=4_000_000):
        if md is None or not len(md.faces):
            return
        F = md.faces if face_mask is None else md.faces[face_mask]
        if self.eye is None:
            V = md.vertices - self.center
            sx = (V @ self.right + self.half_w) / self.px
            sy = (self.half_h - V @ self.up) / self.px
            dz = V @ self.fwd
        else:
            # perspective: scale by distance along the view axis; depth is
            # 1 / distance (linear in screen space, larger = nearer)
            V = md.vertices - self.eye
            zc = np.maximum(-(V @ self.fwd), 1e-3)
            k = self.dist / zc
            sx = (k * (V @ self.right) + self.half_w) / self.px
            sy = (self.half_h - k * (V @ self.up)) / self.px
            dz = 1.0 / zc
            F = F[(zc[F] > 0.05).all(1)]
        ax, ay = sx[F[:, 0]], sy[F[:, 0]]
        bx, by = sx[F[:, 1]], sy[F[:, 1]]
        cx, cy = sx[F[:, 2]], sy[F[:, 2]]
        # screen-space signed area (y down): > 0 for faces turned to the camera
        area = 0.5 * ((bx - ax) * (cy - ay) - (cx - ax) * (by - ay))
        lo_x = np.minimum(np.minimum(ax, bx), cx)
        hi_x = np.maximum(np.maximum(ax, bx), cx)
        lo_y = np.minimum(np.minimum(ay, by), cy)
        hi_y = np.maximum(np.maximum(ay, by), cy)
        vis = (area < 0) & (hi_x >= 0) & (lo_x < self.W) & (hi_y >= 0) & (lo_y < self.H)
        x0 = np.ceil(lo_x - 0.5).astype(np.int64)
        x1 = np.floor(hi_x - 0.5).astype(np.int64)
        y0 = np.ceil(lo_y - 0.5).astype(np.int64)
        y1 = np.floor(hi_y - 0.5).astype(np.int64)
        big = vis & (x1 >= x0) & (y1 >= y0)
        small = vis & ~big
        nrm = md.normals
        # sub-pixel triangles: one sample with probability = covered area
        s = np.nonzero(small & (self.rng.random(len(F)) < np.abs(area)))[0]
        if s.size:
            r1 = np.sqrt(self.rng.random(s.size))
            r2 = self.rng.random(s.size)
            w = np.stack([1 - r1, r1 * (1 - r2), r1 * r2], 1)
            px_ = w[:, 0] * ax[s] + w[:, 1] * bx[s] + w[:, 2] * cx[s]
            py_ = w[:, 0] * ay[s] + w[:, 1] * by[s] + w[:, 2] * cy[s]
            ix, iy = np.floor(px_).astype(np.int64), np.floor(py_).astype(np.int64)
            ok = (ix >= 0) & (ix < self.W) & (iy >= 0) & (iy < self.H)
            f = F[s]
            dep = (w * dz[f]).sum(1)
            N = (w[:, :, None] * nrm[f]).sum(1)
            col = self._shade(N, self._colours(md, kind, f[:, 0]), kind not in ("ground", "leaf"))
            self._resolve((iy * self.W + ix)[ok], dep[ok], col[ok])
        # covering triangles: exact rasterization in batches of pixels
        g = np.nonzero(big)[0]
        if not g.size:
            return
        x0, y0 = np.clip(x0[g], 0, self.W - 1), np.clip(y0[g], 0, self.H - 1)
        x1, y1 = np.clip(x1[g], 0, self.W - 1), np.clip(y1[g], 0, self.H - 1)
        wb, hb = x1 - x0 + 1, y1 - y0 + 1
        cnt = np.maximum(wb, 0) * np.maximum(hb, 0)
        cum = np.cumsum(cnt)
        start = 0
        while start < g.size:
            stop = max(start + 1, int(np.searchsorted(cum, cum[start] - cnt[start] + batch, side="right")))
            sl = slice(start, stop)
            k = np.repeat(np.arange(start, stop), cnt[sl])
            if k.size:
                loc = np.arange(k.size) - np.repeat(cum[sl] - cnt[sl] - (cum[start] - cnt[start]), cnt[sl])
                ix = x0[k] + loc % wb[k]
                iy = y0[k] + loc // wb[k]
                pxc, pyc = ix + 0.5, iy + 0.5
                t = g[k]
                d = (by[t] - cy[t]) * (ax[t] - cx[t]) + (cx[t] - bx[t]) * (ay[t] - cy[t])
                l0 = ((by[t] - cy[t]) * (pxc - cx[t]) + (cx[t] - bx[t]) * (pyc - cy[t])) / d
                l1 = ((cy[t] - ay[t]) * (pxc - cx[t]) + (ax[t] - cx[t]) * (pyc - cy[t])) / d
                l2 = 1.0 - l0 - l1
                inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
                if inside.any():
                    t, l0, l1, l2 = t[inside], l0[inside], l1[inside], l2[inside]
                    f = F[t]
                    w = np.stack([l0, l1, l2], 1)
                    dep = (w * dz[f]).sum(1)
                    N = (w[:, :, None] * nrm[f]).sum(1)
                    col = self._shade(N, self._colours(md, kind, f[:, 0]), kind not in ("ground", "leaf"))
                    self._resolve(iy[inside] * self.W + ix[inside], dep, col)
            start = stop

    def add_ground(self, radius: float, z: float = 0.0):
        """An opaque ground disc (as a fan of triangles) at height z."""
        from .mesh import MeshData
        if self.eye is not None:
            # perspective: a grid, so cells behind the camera drop out alone
            g = np.linspace(-radius, radius, 61)
            X, Y = np.meshgrid(self.center[0] + g, self.center[1] + g, indexing="ij")
            V = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z)], 1)
            i, j = np.meshgrid(np.arange(60), np.arange(60), indexing="ij")
            a0 = (i * 61 + j).ravel()
            F = np.concatenate([np.stack([a0, a0 + 61, a0 + 62], 1), np.stack([a0, a0 + 62, a0 + 1], 1)])
            self.add(MeshData(V, F, np.tile([0.0, 0.0, 1.0], (len(V), 1)), {}), "ground")
            self.add(MeshData(V, F[:, ::-1], np.tile([0.0, 0.0, 1.0], (len(V), 1)), {}), "ground")
            return
        a = np.linspace(0, 2 * np.pi, 49)[:-1]
        V = np.vstack([[self.center[0], self.center[1], z],
                       np.stack([self.center[0] + radius * np.cos(a), self.center[1] + radius * np.sin(a), np.full(48, z)], 1)])
        i = np.arange(48)
        F = np.stack([np.zeros(48, int), 1 + i, 1 + (i + 1) % 48], 1)
        self.add(MeshData(V, F, np.tile([0.0, 0.0, 1.0], (len(V), 1)), {}), "ground")

    def image(self) -> np.ndarray:
        img = self.img.reshape(self.H, self.W, 3).copy()
        empty = ~np.isfinite(self.zbuf.reshape(self.H, self.W))
        t = (np.arange(self.H) / max(self.H - 1, 1))[:, None, None]
        sky = (1 - t) * SKY_TOP + t * SKY_HORIZON
        img = np.where(empty[:, :, None], np.broadcast_to(sky, img.shape), img)
        img = img.reshape(self.out_h, self.ss, self.out_w, self.ss, 3).mean((1, 3))
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def save_png(arr, path):
    from PIL import Image
    Image.fromarray(arr).save(path)
    return path
