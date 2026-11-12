"""Generalised-cylinder mesh of the branch skeleton.

Every axis (trunk, branch, twig) becomes one continuous swept tube:

* the axis polyline is resampled along a C1 cubic Hermite curve (tangents are
  the bisectors of adjacent internodes), so there are no cylinder joins;
* the radius follows a C1 monotone cubic (Fritsch & Carlson 1980) over a
  lightly smoothed copy of the pipe-model radii, so the step at each node
  does not show as a shading band (timeline.json keeps the exact radii);
* ring frames are rotation-minimising (double reflection, Wang et al. 2008,
  ACM TOG 27(1):2), so tubes do not twist;
* ring resolution follows the radius; rings with different vertex counts are
  stitched by angle;
* at each junction the child tube starts on the parent's centre line and
  swells into a short branch collar; the vertices of both tubes near the
  junction are then moved onto the smooth union (polynomial smooth-min,
  blend radius proportional to the child radius) of the two tubes' distance
  fields, which fillets the seam.

The result is a union of tubes (not a single manifold), as is usual for
real-time trees.  Per-vertex attributes: birth_year, death_year,
branch_order, radius, node_id.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class MeshSettings:
    edge_target: float = 0.012          # m, target ring edge length
    sides_allowed: tuple = (4, 6, 8, 12, 16, 24, 32)
    ring_spacing_factor: float = 3.0    # ring spacing / radius
    min_ring_spacing: float = 0.04      # m
    max_ring_spacing: float = 0.25      # m
    max_turn_deg: float = 12.0          # max tangent turn between rings
    blend_min_radius: float = 0.003     # m, junctions with thinner children are not filleted
    parent_refine_ratio: float = 0.12   # refine the parent around children at least this thick
    tip_length_factor: float = 3.0      # tip cone length / tip radius
    radius_smoothing_iters: int = 8     # visual smoothing of the pipe-model steps at nodes
    ring_attributes: bool = False       # also output each vertex's place on its tube, for texture coordinates
    stem_sides_by_radius: bool = False  # the stem's rings follow its own radius, not the thin taproot tip below it
    drop_hidden_rings: bool = False     # a branch's rings that lie wholly inside its parent are left out
    ring_tolerance: float = 0.0         # leave out a ring if its surface stays within this share of its radius (0: keep all)
    ring_tolerance_m: float = 0.0       # ... or within this many metres, whichever is more
    ring_longest_span: float = 0.5      # m, the longest run of tube without a ring, so wind can bend it
    stem_edge_by_height: tuple = ()     # ((height, edge m), ...): the stem's sides and rings as fine as this, for relief in the mesh
    stem_along_factor: float = 1.4      # rings this many edges apart: bark's furrows run up the stem
    stem_rings_under: float = 0.025     # only add rings where the edge asked for is under this
    buttress_hold_m: float = 0.0        # the stem's root ridges keep their full size down to at least this far below z = 0
    no_stem_ridges: bool = False        # no ridges, bell or fillets from roots on the stem: whoever asks shapes the foot itself
    stem_stub_share: float = 0.0        # where the old trunk runs on past a replacement leader no thicker than this share of it, the replacement is still the stem



@dataclass
class MeshData:
    vertices: np.ndarray
    faces: np.ndarray
    normals: np.ndarray
    attributes: dict = field(default_factory=dict)

    @property
    def n_vertices(self) -> int:
        return len(self.vertices)


def _normalize(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def _perp(ref, d):
    r = ref - (ref * d).sum(-1, keepdims=True) * d
    n = np.linalg.norm(r, axis=-1)
    bad = n < 1e-6
    if bad.any():
        alt = np.where(np.abs(d[bad, 0:1]) < 0.9, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
        r[bad] = alt - (alt * d[bad]).sum(-1, keepdims=True) * d[bad]
        n[bad] = np.linalg.norm(r[bad], axis=-1)
    return r / n[:, None]


def _polyline_sdf(x, c, r):
    """Signed distance from points x (M,3) to a tube with centre line c (K,3), radii r (K,)."""
    if len(c) < 2:
        return np.linalg.norm(x - c[0], axis=1) - r[0]
    a, b = c[:-1], c[1:]
    d = b - a
    dd = np.maximum((d * d).sum(1), 1e-18)
    t = np.clip(((x[:, None, :] - a[None]) * d[None]).sum(2) / dd[None], 0.0, 1.0)
    p = a[None] + t[..., None] * d[None]
    dist = np.linalg.norm(x[:, None, :] - p, axis=2) - (r[:-1][None] + t * (r[1:] - r[:-1])[None])
    return dist.min(1)


def _thin_rings(ss, X, R, tol_rel, tol_abs, fixed, longest):
    """Which rings of one axis to keep: those fixed, and whichever the rest can't be drawn without.  A
    ring goes if the tube between its neighbours passes within the tolerance of it, by centre and radius
    together (Douglas & Peucker 1973, over the rings)."""
    keep = fixed.copy()
    keep[0] = keep[-1] = True
    at = np.nonzero(keep)[0].tolist()
    stack = [(a, b) for a, b in zip(at[:-1], at[1:]) if b > a + 1]
    while stack:
        a, b = stack.pop()
        span = ss[b] - ss[a]
        t = ((ss[a + 1:b] - ss[a]) / max(span, 1e-12))[:, None]
        err = np.linalg.norm(X[a + 1:b] - (X[a] + t * (X[b] - X[a])), axis=1) + np.abs(R[a + 1:b] - (R[a] + t[:, 0] * (R[b] - R[a])))
        ratio = err / np.maximum(tol_rel * R[a + 1:b], tol_abs)
        k = int(np.argmax(ratio))
        if ratio[k] <= 1.0 and span <= longest:
            continue
        # over the longest span, the ring nearest the middle unless one is out of tolerance
        m = a + 1 + (k if ratio[k] > 1.0 else int(np.argmin(np.abs(t[:, 0] - 0.5))))
        keep[m] = True
        if m > a + 1:
            stack.append((a, m))
        if b > m + 1:
            stack.append((m, b))
    return keep


def _smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def _blend_vertices(x, n, other_c, other_r, k, iters=14):
    """Move vertices x outward along normals n onto the smooth union with
    another tube.  Vertices whose normal points into the other tube (the
    crotch) cannot reach the blend surface and are left in place: they are
    hidden inside the other tube's surface anyway."""
    d0 = _polyline_sdf(x, other_c, other_r)
    act = (d0 > 0.0) & (d0 < k)
    if not act.any():
        return x
    xa, na = x[act], n[act]

    def f(t):
        return _smin(t, _polyline_sdf(xa + t[:, None] * na, other_c, other_r), k)

    hi = np.full(len(xa), k)
    reach = f(hi) >= 0.0
    if not reach.any():
        return x
    xa, na, hi = xa[reach], na[reach], hi[reach]
    lo = np.zeros(len(xa))
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        below = _smin(mid, _polyline_sdf(xa + mid[:, None] * na, other_c, other_r), k) < 0.0
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    out = x.copy()
    idx = np.nonzero(act)[0][reach]
    out[idx] = xa + hi[:, None] * na
    return out


def _node_cost(T, nodes, radius, s):
    """Rough vertex count of each node's internode (ring sides x rings) and
    the internode length."""
    r = radius[nodes].astype(np.float64)
    L = np.linalg.norm(T.pos[nodes] - T.pos[T.parent[nodes]], axis=1)
    allowed = np.asarray(s.sides_allowed)
    sides = allowed[np.clip(np.searchsorted(allowed, 2.0 * np.pi * r / s.edge_target), 0, len(allowed) - 1)]
    rings = L / np.clip(s.ring_spacing_factor * r, s.min_ring_spacing, s.max_ring_spacing)
    return sides * (rings + 0.1), L, sides


def estimate_vertices(T, select, radius, settings: MeshSettings | None = None) -> np.ndarray:
    """Per-node rough vertex count (for choosing a reduced-mesh radius)."""
    s = settings or MeshSettings()
    nodes = np.nonzero(np.asarray(select[: T.n], bool))[0]
    nodes = nodes[nodes > 0]
    out = np.zeros(T.n)
    out[nodes] = _node_cost(T, nodes, radius, s)[0]
    return out


def plan_chunks(T, select, radius, geometry, settings: MeshSettings | None = None, budget: float = 400_000):
    """Split the selected nodes into chunks of whole axes, about ``budget``
    vertices each, so a tree can be meshed and exported a chunk at a time.

    Axes are packed in depth-first order, so a branch usually shares a chunk
    with its offshoots.  Where a filleted junction (child at least
    ``blend_min_radius`` thick) is cut by a chunk boundary, the chunk also
    meshes the neighbour as context: the parent axis from its base to just
    past the junction, or the first part of the child axis.  Context
    vertices are dropped (``emit``), so every axis comes out exactly as in
    one pass over the whole tree.  Yields (node ids, emitted axis ids).
    """
    s = settings or MeshSettings()
    n = T.n
    sel = np.asarray(select[:n], bool).copy()
    sel[0] = False
    nodes = np.nonzero(sel)[0]
    if nodes.size == 0:
        return
    nodes = nodes[np.lexsort((T.depth[nodes], T.axis[nodes]))]
    ax = T.axis[nodes]
    starts = np.nonzero(np.r_[True, ax[1:] != ax[:-1]])[0]
    ends = np.r_[starts[1:], len(nodes)]
    A = len(starts)
    counts = ends - starts
    axis_idx = np.full(n, -1, np.int64)
    axis_idx[nodes] = np.repeat(np.arange(A), counts)
    sorted_at = np.full(n, -1, np.int64)
    sorted_at[nodes] = np.arange(len(nodes))
    cost, L, sides = _node_cost(T, nodes, radius, s)
    axis_cost = np.add.reduceat(cost, starts) + 2.0 * sides[starts]
    cl = np.cumsum(L)
    s_node = cl - np.repeat(cl[starts] - L[starts], counts)      # arc length from the axis base
    first = nodes[starts]
    b = T.parent[first]
    pa = axis_idx[b]
    rc = radius[first].astype(np.float64)
    rp = radius[b].astype(np.float64)
    kb = float(geometry.junction_blend) * rc
    thick = T.is_lateral[first].astype(bool) & (rc >= s.blend_min_radius) & (pa >= 0)

    kids = [[] for _ in range(A)]
    child = np.nonzero(pa >= 0)[0]
    for c in child[np.argsort(T.depth[b[child]], kind="stable")].tolist():
        kids[int(pa[c])].append(c)
    order = []
    stack = [a for a in range(A) if pa[a] < 0][::-1]
    while stack:
        a = stack.pop()
        order.append(a)
        stack.extend(reversed(kids[a]))

    chunks, cur, acc = [], [], 0.0
    for a in order:
        if cur and acc + axis_cost[a] > budget:
            chunks.append(cur)
            cur, acc = [], 0.0
        cur.append(a)
        acc += axis_cost[a]
    if cur:
        chunks.append(cur)

    margin = 12  # nodes past a window, so smoothing and tangents are unaffected
    in_chunk = np.zeros(A, bool)
    for C in chunks:
        in_chunk[C] = True
        need = {}
        for a in C:
            p = int(pa[a])
            if thick[a] and not in_chunk[p]:
                j = sorted_at[b[a]]
                w = rc[a] / 0.25 + 3.0 * kb[a] + rp[a] + 0.05
                seg = s_node[starts[p]:ends[p]]
                cnt = int(min(counts[p], np.searchsorted(seg, s_node[j] + w) + 1 + margin))
                need[p] = max(need.get(p, 0), cnt)
            for c in kids[a]:
                if thick[c] and not in_chunk[c]:
                    w = 4.0 * rp[c] + 4.0 * kb[c] + rc[c] + 0.05
                    seg = s_node[starts[c]:ends[c]]
                    cnt = int(min(counts[c], np.searchsorted(seg, w) + 1 + margin))
                    need[c] = max(need.get(c, 0), cnt)
        # a context axis is sampled more finely around its own thick
        # offshoots; include those too, so its rings match the one-pass mesh
        for x, cnt_x in list(need.items()):
            for c in kids[x]:
                if thick[c] and not in_chunk[c] and sorted_at[b[c]] - starts[x] < cnt_x:
                    w = 4.0 * rp[c] + 4.0 * kb[c] + rc[c] + 0.05
                    seg = s_node[starts[c]:ends[c]]
                    cnt = int(min(counts[c], np.searchsorted(seg, w) + 1 + margin))
                    need[c] = max(need.get(c, 0), cnt)
        parts = [nodes[starts[a]:ends[a]] for a in C]
        parts += [nodes[starts[c]:starts[c] + k] for c, k in need.items()]
        in_chunk[C] = False
        yield np.concatenate(parts), T.axis[first[C]]


def continue_trunk(tree, select, radius=None, stub_share: float = 0.0):
    """A view of ``tree`` for drawing, in which the stem is one tube: where
    the trunk (axis 0) ends because its leader was lost and the way to the
    top goes on in a lateral (a replacement leader), that lateral's axis is
    drawn as axis 0, without the end cap on the old trunk and the branch
    collar on the lateral.  Only where the trunk has no selected
    continuation of its own (a living fork is left as it is), or, with
    ``stub_share``, one no thicker than that share of the lateral: the lost
    leader's last thread, which is drawn as a side shoot.  A continuation is
    any selected node further along the trunk, not only the next one: among
    shed branches (``select`` = the dead nodes) the lost leader's dead end can
    lie past a stub that still lives, and the trunk has then not ended.  The
    tree itself is not changed."""
    n = tree.n
    sel = np.asarray(select[:n], bool)
    idx = np.nonzero(sel)[0]
    if idx.size == 0:
        return tree
    par = np.asarray(tree.parent[:n])
    top = int(idx[np.argmax(tree.pos[idx, 2])])
    path, k = [], top
    while k >= 0 and len(path) <= n:
        path.append(k)
        k = int(par[k])
    path = path[::-1]
    axis = np.asarray(tree.axis[:n]).copy()
    lat = np.asarray(tree.is_lateral[:n]).astype(bool).copy()
    depth = np.asarray(tree.depth[:n])
    changed = False
    for a, b in zip(path[:-1], path[1:]):
        if axis[a] == 0 and axis[b] != 0 and lat[b]:
            kids = idx[par[idx] == a]
            own = kids[axis[kids] == 0]
            if own.size and stub_share > 0.0 and np.max(radius[own]) <= stub_share * radius[b]:
                axis[(axis == 0) & (depth > depth[a])] = axis.max() + 1
                lat[own] = True
                own = own[:0]
            if not own.size and not np.any((axis[idx] == 0) & (depth[idx] > depth[a])):
                axis[axis == axis[b]] = 0
                lat[b] = False
                changed = True
    if not changed:
        return tree
    from types import SimpleNamespace
    return SimpleNamespace(n=n, pos=tree.pos, parent=tree.parent, axis=axis, is_lateral=lat, order=tree.order,
                           birth=tree.birth, death=tree.death, depth=tree.depth)


def build_mesh_chunks(tree, select, radius, geometry, settings: MeshSettings | None = None, budget: float = 400_000):
    """Mesh the selection a chunk at a time (see ``plan_chunks``); yields
    MeshData.  Peak memory follows the chunk size, not the tree size.  A stem
    whose leader was replaced is drawn as one tube (``continue_trunk``)."""
    tree = continue_trunk(tree, select, radius, settings.stem_stub_share if settings else 0.0)
    full = np.asarray(select[: tree.n], bool).copy()
    full[0] = False
    sel = np.zeros(tree.n, bool)
    for ids, emit in plan_chunks(tree, full, radius, geometry, settings, budget):
        sel[ids] = True
        md = build_mesh(tree, sel, radius, geometry, settings, emit_axes=emit, full_select=full)
        sel[ids] = False
        if md is not None and md.n_vertices:
            yield md


def _skeleton_tangent(T, b, full_select):
    """Tangent of the axis through nodes ``b`` (bisector of the incoming and
    outgoing internodes), as the mesher computes it when the axis is meshed."""
    n = T.n
    pos = T.pos
    t_in = _normalize(pos[b].astype(np.float64) - pos[T.parent[b]].astype(np.float64))
    t_out = np.zeros_like(t_in)
    nodes = np.nonzero(np.isin(T.parent[:n], b) & full_select[:n])[0]
    nodes = nodes[T.axis[nodes] == T.axis[T.parent[nodes]]]
    if nodes.size:
        slot = {int(x): i for i, x in enumerate(b.tolist())}
        rows = np.array([slot[int(p)] for p in T.parent[nodes].tolist()])
        t_out[rows] = _normalize(pos[nodes].astype(np.float64) - pos[T.parent[nodes]].astype(np.float64))
    return _normalize(t_in + t_out)


def _buttresses(T, radius: np.ndarray, sel_all: np.ndarray, geometry):
    """Root buttresses of the stem base (geometry.root_flare_mode "buttress").

    The flare is where the main structural roots join the stem: each root
    that leaves the stem/taproot axis (axis 0) below the ground line raises a
    ridge on the stem at its own azimuth.  The ridge stands out by the root's
    radius at the ground line, spans the arc the root covers on the stem
    (Gaussian, sigma = root radius / stem radius) and fades smoothly upwards;
    the largest root's ridge reaches the height of the uppermost root collar
    (Laasasenaho 1982, birch: 0.4862 DBH[cm] + 0.4979 H[m], cm), smaller
    roots proportionally lower.  A root leaving steeply downwards (a sinker)
    makes no ridge (its share is its horizontal direction cosine).
    Returns (azimuth, ridge radius, root depth, ridge height, collar height)
    or None when no root leaves axis 0 (crown-only meshes)."""
    n = T.n
    sel = sel_all[:n]
    par = np.maximum(T.parent[:n], 0)
    roots = np.nonzero(sel & T.is_lateral[:n].astype(bool) & (T.axis[par] == 0) & (T.pos[par, 2] <= 0.0))[0]
    if roots.size == 0:
        return None
    stem = np.nonzero(sel & (T.axis[:n] == 0))[0]
    order = np.argsort(T.pos[stem, 2])
    zs, rs = T.pos[stem[order], 2].astype(float), radius[stem[order]].astype(float)
    dbh_cm = 200.0 * float(np.interp(1.3, zs, rs)) if zs.max() >= 1.3 else 0.0
    h_m = float(T.pos[sel, 2].max())
    c_d, c_h = (float(v) for v in geometry.root_collar_height_coef)
    h_collar = max((c_d * dbh_cm + c_h * h_m) / 100.0, 1e-3)
    d = T.pos[roots] - T.pos[T.parent[roots]]
    horiz = np.hypot(d[:, 0], d[:, 1])
    az = np.arctan2(d[:, 1], d[:, 0])
    share = horiz / np.maximum(np.linalg.norm(d, axis=1), 1e-12)
    r = radius[roots].astype(float) * share
    if r.max() <= 0.0:
        return None
    depth = -T.pos[T.parent[roots], 2].astype(float)
    keep_share = float(getattr(geometry, "root_flare_min_share", 0.0) or 0.0)
    if keep_share > 0.0:
        # a tree with many roots at its collar: only the thick ones raise a ridge
        big = r >= keep_share * r.max()
        az, r, depth = az[big], r[big], depth[big]
    return az, r, depth, h_collar * r / r.max(), h_collar


def _spaced_samples(gs: np.ndarray, sh: np.ndarray, sa: np.ndarray) -> np.ndarray:
    """Which ring samples to keep, each measured against the last one kept.  Where many windows overlap,
    as where a stump's roots leave it, measuring against its neighbour a dense run drops itself whole, and
    leaves a hole in the stem's rings."""
    keep = np.ones(len(gs), bool)
    at, h_at, axis_at = float(gs[0]), float(sh[0]), int(sa[0])
    for i in range(1, len(gs)):
        if int(sa[i]) == axis_at and float(gs[i]) - at < 0.3 * min(float(sh[i]), h_at):
            keep[i] = False
        else:
            at, h_at, axis_at = float(gs[i]), float(sh[i]), int(sa[i])
    return keep


def _buttress_offset(theta: np.ndarray, z: np.ndarray, r_stem: np.ndarray, bt, hold: float = 0.0, no_stack: bool = False) -> np.ndarray:
    """Radial offset of stem-surface points at azimuth ``theta`` and height
    ``z`` (ring radius ``r_stem``) from the root ridges ``bt`` (_buttresses).
    ``hold``: no ridge starts to fade above this depth."""
    az, rr, depth, hh, _ = bt
    out = np.zeros(len(theta))
    for a, r, dp, h in zip(az, rr, depth, hh):
        dth = (theta - a + np.pi) % (2.0 * np.pi) - np.pi
        sig = np.maximum(r / np.maximum(r_stem, 1e-6), 1e-3)
        if no_stack:
            sig = 0.7 * sig     # narrower: side by side they stay ridges
            h = max(h, 3.0 * r)     # and no ledge on a young stem, whose collar height is small and whose thickest root isn't
        across = np.exp(-0.5 * (dth / sig) ** 2)
        up = np.clip(z / max(h, 1e-6), 0.0, 1.0)
        down = np.clip((-z - max(dp, hold)) / max(r, 1e-6), 0.0, 1.0)
        along = np.where(z >= 0.0, 1.0 - up * up * (3.0 - 2.0 * up), 1.0 - down * down * (3.0 - 2.0 * down))
        if no_stack:
            # ridges side by side don't pile up on each other, and none stands out more than a third of the stem's radius
            out = np.maximum(out, np.minimum(r, 0.35 * np.maximum(r_stem, 1e-6)) * across * along)
        else:
            out += r * across * along
    return out


def build_mesh(tree, select: np.ndarray, radius: np.ndarray, geometry, settings: MeshSettings | None = None,
               emit_axes: np.ndarray | None = None, full_select: np.ndarray | None = None) -> MeshData | None:
    """Mesh the nodes in ``select`` (bool, per node) using per-node ``radius``.
    With ``emit_axes`` (axis ids) only those axes are returned; the others
    are context for junction fillets.  ``full_select`` is the whole
    selection when ``select`` is one chunk of it."""
    s = settings or MeshSettings()
    T = tree
    n = T.n
    sel = select[:n].copy()
    sel[0] = False
    nodes = np.nonzero(sel)[0]
    if nodes.size == 0:
        return None
    nodes = nodes[np.lexsort((T.depth[nodes], T.axis[nodes]))]
    ax = T.axis[nodes]
    first_mask = np.r_[True, ax[1:] != ax[:-1]]
    axis_first = np.nonzero(first_mask)[0]
    A = len(axis_first)
    lens = np.diff(np.r_[axis_first, len(nodes)])
    chain_axis = np.repeat(np.arange(A), lens)
    chain_local = np.arange(len(nodes)) - np.repeat(axis_first, lens)
    if not np.all(T.parent[nodes[~first_mask]] == nodes[np.nonzero(~first_mask)[0] - 1]):
        raise RuntimeError("axis chains are not contiguous")

    # --- points: axis base (on the parent's centre line) + chain nodes ----
    pt_count = lens + 1
    pt_off = np.r_[0, np.cumsum(pt_count)[:-1]]
    P = int(pt_count.sum())
    pt_node = np.empty(P, dtype=np.int64)
    pt_node[pt_off[chain_axis] + 1 + chain_local] = nodes
    first_nodes = nodes[axis_first]
    pt_node[pt_off] = T.parent[first_nodes]
    pt_axis = np.repeat(np.arange(A), pt_count)
    pt_pos = T.pos[pt_node].astype(np.float64)
    pt_r = radius[pt_node].astype(np.float64)
    pt_r[pt_off] = radius[first_nodes]
    is_base = np.zeros(P, bool)
    is_base[pt_off] = True
    is_last = np.zeros(P, bool)
    is_last[pt_off + pt_count - 1] = True

    seg_end = np.nonzero(~is_base)[0]
    seg_start = seg_end - 1
    seg_node = pt_node[seg_end]
    seg_axis = pt_axis[seg_end]
    seg_vec = pt_pos[seg_end] - pt_pos[seg_start]
    seg_len = np.linalg.norm(seg_vec, axis=1)
    seg_dir = seg_vec / np.maximum(seg_len, 1e-12)[:, None]
    S = len(seg_end)
    pt_in = np.full(P, -1)
    pt_in[seg_end] = np.arange(S)
    pt_out = np.full(P, -1)
    pt_out[seg_start] = np.arange(S)
    # The pipe model steps the radius down by a lateral's share right at the
    # node.  Smooth the profile along each axis (a positive kernel keeps the
    # taper monotone); timeline.json keeps the exact pipe radii.
    prev_pt = np.where(pt_in >= 0, seg_start[np.maximum(pt_in, 0)], np.arange(P))
    next_pt = np.where(pt_out >= 0, seg_end[np.maximum(pt_out, 0)], np.arange(P))
    for _ in range(s.radius_smoothing_iters):
        pt_r = 0.25 * pt_r[prev_pt] + 0.5 * pt_r + 0.25 * pt_r[next_pt]
    tan = np.zeros((P, 3))
    tan += np.where((pt_in >= 0)[:, None], seg_dir[np.maximum(pt_in, 0)], 0.0)
    tan += np.where((pt_out >= 0)[:, None], seg_dir[np.maximum(pt_out, 0)], 0.0)
    tan = _normalize(tan)
    cum = np.zeros(P)
    cum[seg_end] = seg_len
    cum = np.cumsum(cum)
    s_pt = cum - cum[pt_off][pt_axis]
    axis_len = s_pt[pt_off + pt_count - 1]
    axis_goff = np.r_[0.0, np.cumsum(axis_len + 1.0)[:-1]]

    # --- base samples by arc length ----------------------------------------
    # Rings are spaced by radius (and closer where the axis turns), not once
    # per node: with real-length internodes a ring per node would be far too
    # dense on twigs and on the trunk.  Each segment contributes a fractional
    # ring count; rings sit where the running count along the axis crosses an
    # integer, plus one at the start and end of every axis.
    r_avg = 0.5 * (pt_r[seg_start] + pt_r[seg_end])
    spacing = np.clip(s.ring_spacing_factor * r_avg, s.min_ring_spacing, s.max_ring_spacing)
    turn = np.arccos(np.clip((tan[seg_start] * tan[seg_end]).sum(1), -1.0, 1.0))
    cnt = np.maximum(seg_len / spacing, turn / math.radians(s.max_turn_deg))
    csum = np.cumsum(cnt)
    first_seg = np.r_[True, seg_axis[1:] != seg_axis[:-1]]
    axis_start_c = np.maximum.accumulate(np.where(first_seg, csum - cnt, 0.0))
    c0 = csum - cnt - axis_start_c
    c1 = csum - axis_start_c
    nsub = (np.floor(c1) - np.floor(c0)).astype(np.int64)
    rep = np.repeat(np.arange(S), nsub)
    k = np.floor(c0)[rep] + 1 + (np.arange(len(rep)) - np.repeat(np.r_[0, np.cumsum(nsub)[:-1]], nsub))
    u_base = np.clip((k - c0[rep]) / np.maximum(cnt[rep], 1e-12), 0.0, 1.0)
    smp_axis = [seg_axis[rep], pt_axis[pt_off], pt_axis[pt_off + pt_count - 1]]
    smp_s = [s_pt[seg_start[rep]] + u_base * seg_len[rep], np.zeros(A), axis_len]
    h_seg = seg_len / np.maximum(cnt, 1e-12)
    smp_h = [h_seg[rep], np.full(A, 1.0), np.full(A, 1.0)]

    # --- root buttresses: rings close enough to carry the ridges ------------
    bt = None
    trunk_ax = np.nonzero(T.axis[first_nodes] == 0)[0]
    if getattr(geometry, "root_flare_mode", "bell") == "buttress" and trunk_ax.size and not s.no_stem_ridges:
        bt = _buttresses(T, radius, full_select if full_select is not None else select, geometry)
    if bt is not None:
        j = int(trunk_ax[0])
        pts = np.arange(pt_off[j], pt_off[j] + pt_count[j])
        zt = pt_pos[pts, 2]
        if np.all(np.diff(zt) > 0):
            z_lo = -float(np.max(bt[2] + bt[1]))
            step = max(s.min_ring_spacing, bt[4] / 12.0)
            zq = np.arange(max(z_lo, zt[0]), min(bt[4], zt[-1]), step)
            if zq.size:
                smp_axis.append(np.full(zq.size, j))
                smp_s.append(np.interp(zq, zt, s_pt[pts]))
                smp_h.append(np.full(zq.size, step))

    # --- the stem, as fine as its surface asks for -------------------------
    if s.stem_edge_by_height and trunk_ax.size:
        j = int(trunk_ax[0])
        pts = np.arange(pt_off[j], pt_off[j] + pt_count[j])
        zt = np.maximum.accumulate(pt_pos[pts, 2])
        table = np.asarray(s.stem_edge_by_height, float)
        zq, hq = [], []
        z_at = float(zt[0])
        while z_at < float(zt[-1]):
            edge = float(np.interp(z_at, table[:, 0], table[:, 1]))
            step = edge * s.stem_along_factor
            if edge < s.stem_rings_under:
                zq.append(z_at)
                hq.append(step)
            z_at += max(step, 1e-3)
        if zq:
            smp_axis.append(np.full(len(zq), j))
            smp_s.append(np.interp(np.asarray(zq), zt, s_pt[pts]))
            smp_h.append(np.asarray(hq))

    # --- junction refinement windows --------------------------------------
    axis_of_id = {int(a): i for i, a in enumerate(T.axis[first_nodes])}
    # point index of each node within its own axis
    node_pt = np.full(n, -1)
    node_pt[pt_node[~is_base]] = np.nonzero(~is_base)[0]
    junctions = []
    fixed_windows = []          # (axis, from, to): rings the fillets will move
    # laterals whose parent axis is meshed in another chunk still get their
    # branch collar; the parent tangent comes from the skeleton
    ext_tan = {}
    if full_select is not None:
        lat_first = first_nodes[T.is_lateral[first_nodes].astype(bool)]
        bb = T.parent[lat_first]
        miss = np.unique(bb[(node_pt[bb] < 0) & (bb > 0) & full_select[bb]])
        if miss.size:
            ext_tan = dict(zip(miss.tolist(), _skeleton_tangent(T, miss, full_select)))
    for j in range(A):
        fnode = first_nodes[j]
        if not T.is_lateral[fnode]:
            continue
        b = int(T.parent[fnode])
        rc = float(radius[fnode])
        pj = axis_of_id.get(int(T.axis[b]), None)
        bp = node_pt[b] if pj is not None else -1
        if bp < 0:
            if b in ext_tan:
                rp = float(radius[b])
                cd = seg_dir[pt_in[pt_off[j] + 1]]
                sin_t = float(np.linalg.norm(np.cross(cd, ext_tan[b])))
                k = float(geometry.junction_blend) * rc
                junctions.append((j, -1, -1, rc, rp, k, rp / max(sin_t, 0.25), sin_t))
            continue
        rp = float(radius[b])
        cd = seg_dir[pt_in[pt_off[j] + 1]]
        sin_t = float(np.linalg.norm(np.cross(cd, tan[bp])))
        k = float(geometry.junction_blend) * rc
        s_exit = rp / max(sin_t, 0.25)
        junctions.append((j, pj, bp, rc, rp, k, s_exit, sin_t))
        if rc < s.blend_min_radius:
            continue
        h = max(0.6 * k, 0.0015)
        lo, hi = max(0.0, s_exit - 2.0 * rc - 2.0 * k), min(axis_len[j], s_exit + 2.0 * k + rc)
        fixed_windows.append((j, lo, hi))
        cnt = int(min(40, max(0, math.ceil((hi - lo) / h))))
        if cnt > 0:
            smp_axis.append(np.full(cnt, j))
            smp_s.append(lo + (np.arange(cnt) + 0.5) * (hi - lo) / cnt)
            smp_h.append(np.full(cnt, (hi - lo) / cnt))
        if rc >= s.parent_refine_ratio * rp:
            w = rc / max(sin_t, 0.25) + 2.0 * k
            hp = max(0.6 * k, 0.003)
            lo, hi = max(0.0, s_pt[bp] - w), min(axis_len[pj], s_pt[bp] + w)
            fixed_windows.append((pj, lo, hi))
            cnt = int(min(40, max(0, math.ceil((hi - lo) / hp))))
            if cnt > 0:
                smp_axis.append(np.full(cnt, pj))
                smp_s.append(lo + (np.arange(cnt) + 0.5) * (hi - lo) / cnt)
                smp_h.append(np.full(cnt, (hi - lo) / cnt))

    sa = np.concatenate(smp_axis)
    ss = np.concatenate(smp_s)
    sh = np.concatenate(smp_h)
    gs = axis_goff[sa] + ss
    order = np.argsort(gs, kind="stable")
    sa, ss, sh, gs = sa[order], ss[order], sh[order], gs[order]
    gap = np.diff(gs)
    keep = np.r_[True, ~((gap < 0.3 * np.minimum(sh[1:], sh[:-1])) & (sa[1:] == sa[:-1]))]
    if s.stem_edge_by_height:
        keep = _spaced_samples(gs, sh, sa)
    # never drop the first sample of an axis or the axis end
    keep |= np.r_[True, sa[1:] != sa[:-1]]
    keep |= np.r_[sa[:-1] != sa[1:], True]
    sa, ss, gs = sa[keep], ss[keep], gs[keep]

    # --- evaluate the Hermite curve ---------------------------------------
    seg_g = axis_goff[seg_axis] + s_pt[seg_start]
    si = np.clip(np.searchsorted(seg_g, gs, side="right") - 1, 0, S - 1)
    u = np.clip((gs - seg_g[si]) / np.maximum(seg_len[si], 1e-12), 0.0, 1.0)
    p0, p1 = pt_pos[seg_start[si]], pt_pos[seg_end[si]]
    L = seg_len[si][:, None]
    m0, m1 = tan[seg_start[si]] * L, tan[seg_end[si]] * L
    u1 = u[:, None]
    u2, u3 = u1 * u1, u1 * u1 * u1
    X = (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u1) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1
    dX = (6 * u2 - 6 * u1) * p0 + (3 * u2 - 4 * u1 + 1) * m0 + (-6 * u2 + 6 * u1) * p1 + (3 * u2 - 2 * u1) * m1
    Tn = _normalize(dX)
    # radius: C1 monotone cubic along the axis (Fritsch & Carlson 1980), so
    # nodes with a big lateral do not leave a slope kink in the shading
    seg_slope = (pt_r[seg_end] - pt_r[seg_start]) / np.maximum(seg_len, 1e-12)
    m_in = np.where(pt_in >= 0, seg_slope[np.maximum(pt_in, 0)], np.nan)
    m_out = np.where(pt_out >= 0, seg_slope[np.maximum(pt_out, 0)], np.nan)
    pt_m = np.where(np.isnan(m_in), m_out, np.where(np.isnan(m_out), m_in, 0.5 * (m_in + m_out)))
    pt_m = np.where(~np.isnan(m_in) & ~np.isnan(m_out) & (m_in * m_out <= 0), 0.0, pt_m)
    pt_m = np.nan_to_num(pt_m)
    r0, r1 = pt_r[seg_start[si]], pt_r[seg_end[si]]
    Ls = seg_len[si]
    lim = 3.0 * np.abs(r1 - r0) / np.maximum(Ls, 1e-12)
    ms0 = np.clip(pt_m[seg_start[si]], -lim, lim)
    ms1 = np.clip(pt_m[seg_end[si]], -lim, lim)
    uu = u
    R = ((2 * uu**3 - 3 * uu**2 + 1) * r0 + (uu**3 - 2 * uu**2 + uu) * Ls * ms0
         + (-2 * uu**3 + 3 * uu**2) * r1 + (uu**3 - uu**2) * Ls * ms1)
    R = np.clip(R, np.minimum(r0, r1), np.maximum(r0, r1))
    trunk = T.axis[first_nodes[sa]] == 0
    if np.any(trunk) and bt is None and not s.no_stem_ridges:
        # root flare without roots to follow: a smooth (Gaussian) swelling
        # centred on the ground line, so the stem runs into the root collar
        # without a crease
        R[trunk] *= 1.0 + float(geometry.root_flare_extra) * np.exp(-(X[trunk, 2] / float(geometry.root_flare_height)) ** 2)
    # branch collar: a lateral swells where it leaves its parent, so the two
    # surfaces meet at a shallow angle before the fillet smooths the seam
    collar = float(geometry.collar_extra)
    if collar > 0.0 and junctions:
        jx = np.array([j[0] for j in junctions])
        jexit = np.full(A, np.nan)
        jrc = np.zeros(A)
        jexit[jx] = [j[6] for j in junctions]
        jrc[jx] = [j[3] for j in junctions]
        # the collar is the swelling of a branch thinner than its parent; a
        # co-dominant one (a fork, a lateral that replaced a lost leader)
        # carries the parent's wood on and has none
        jsize = np.ones(A)
        jsize[jx] = [max(0.0, 1.0 - j[3] / max(j[4], 1e-9)) for j in junctions]
        on = ~np.isnan(jexit[sa])
        if on.any():
            x = np.clip((ss[on] - jexit[sa[on]]) / (float(geometry.collar_length) * jrc[sa[on]]), 0.0, 1.0)
            R[on] *= 1.0 + collar * jsize[sa[on]] * (1.0 - x * x * (3.0 - 2.0 * x))  # C1 smoothstep falloff
    # --- rings that add nothing ------------------------------------------
    if s.drop_hidden_rings or s.ring_tolerance > 0.0 or s.ring_tolerance_m > 0.0:
        ring_keep = np.ones(len(X), bool)
        first = np.nonzero(np.r_[True, sa[1:] != sa[:-1]])[0]
        last = np.r_[first[1:], len(sa)]
        where = {int(sa[a]): (int(a), int(b)) for a, b in zip(first, last)}
        if s.drop_hidden_rings:
            # a branch starts on its parent's centre line, and its surface comes out no sooner than
            # the fillet's window starts; of the rings before that only the last is needed
            for (j, pj, bp, rc, rp, k, s_exit, sin_t) in junctions:
                a, b = where[int(j)]
                hidden = int(np.searchsorted(ss[a:b], 0.85 * s_exit - 2.0 * rc - 2.0 * k, side="right")) - 1
                if 0 < hidden <= b - a - 2:
                    ring_keep[a:a + hidden] = False
        if s.ring_tolerance > 0.0 or s.ring_tolerance_m > 0.0:
            fixed = np.zeros(len(X), bool)
            for (j, lo, hi) in fixed_windows:
                a, b = where[int(j)]
                fixed[a:b] |= (ss[a:b] >= lo) & (ss[a:b] <= hi)
            # the stem keeps all its rings: they carry the buttress ridges and the bark's relief
            fixed |= trunk
            for a, b in zip(first.tolist(), last.tolist()):
                live = np.nonzero(ring_keep[a:b])[0] + a
                if len(live) > 2:
                    ring_keep[live] = _thin_rings(ss[live], X[live], R[live], s.ring_tolerance, s.ring_tolerance_m, fixed[live], s.ring_longest_span)
        X, Tn, R, si, sa, ss, trunk = X[ring_keep], Tn[ring_keep], R[ring_keep], si[ring_keep], sa[ring_keep], ss[ring_keep], trunk[ring_keep]
    ring_node = seg_node[si]
    NR = len(X)

    # --- rotation-minimising frames, all axes in lockstep -----------------
    ring_first = np.nonzero(np.r_[True, sa[1:] != sa[:-1]])[0]
    ring_count = np.diff(np.r_[ring_first, NR])
    ring_axis_rank = np.repeat(np.arange(len(ring_first)), ring_count)
    fa = sa[ring_first]
    ref = np.tile(np.array([1.0, 0.0, 0.0]), (len(fa), 1))
    lat_axes = T.is_lateral[first_nodes[fa]]
    if lat_axes.any():
        par_nodes = T.parent[first_nodes[fa[lat_axes]]]
        pidx = node_pt[par_nodes]
        ref_l = np.where((pidx >= 0)[:, None], tan[np.maximum(pidx, 0)], ref[lat_axes])
        if full_select is not None:
            # parent axis meshed in another chunk: its tangent from the skeleton
            miss = (pidx < 0) & (par_nodes > 0) & full_select[par_nodes]
            if miss.any():
                ref_l[miss] = _skeleton_tangent(T, par_nodes[miss], full_select)
        ref[lat_axes] = ref_l
    Nf = np.zeros((NR, 3))
    Nf[ring_first] = _perp(ref, Tn[ring_first])
    by_len = np.argsort(-ring_count, kind="stable")
    cnt_sorted = ring_count[by_len]
    starts_sorted = ring_first[by_len]
    for i in range(int(ring_count.max()) - 1):
        k_act = int(np.searchsorted(-cnt_sorted, -(i + 2), side="right"))
        if k_act == 0:
            break
        a = starts_sorted[:k_act] + i
        b = a + 1
        v1 = X[b] - X[a]
        c1 = (v1 * v1).sum(1, keepdims=True)
        okc = c1 > 1e-18
        c1s = np.where(okc, c1, 1.0)
        rL = Nf[a] - (2.0 / c1s) * (v1 * Nf[a]).sum(1, keepdims=True) * v1
        tL = Tn[a] - (2.0 / c1s) * (v1 * Tn[a]).sum(1, keepdims=True) * v1
        v2 = Tn[b] - tL
        c2 = (v2 * v2).sum(1, keepdims=True)
        ok2 = c2 > 1e-18
        c2s = np.where(ok2, c2, 1.0)
        nb = np.where(ok2, rL - (2.0 / c2s) * (v2 * rL).sum(1, keepdims=True) * v2, rL)
        Nf[b] = np.where(okc, nb, Nf[a])
    Nf = _perp(Nf, Tn)
    Bf = np.cross(Tn, Nf)

    # --- ring resolution -------------------------------------------------
    allowed = np.asarray(s.sides_allowed)
    want = 2.0 * np.pi * R / s.edge_target
    sides = allowed[np.clip(np.searchsorted(allowed, want), 0, len(allowed) - 1)]
    big = 1000
    raw_sides = sides
    sides = np.minimum.accumulate(sides - ring_axis_rank * big) + ring_axis_rank * big
    if s.stem_sides_by_radius and trunk.any():
        # axis 0 starts at the tip of the taproot, and a running minimum from there would hold the
        # whole stem at the tip's few sides: let its rings grow to its thickest point, then thin
        tr = np.nonzero(trunk)[0]
        peak = int(np.argmax(R[tr]))
        sides[tr[: peak + 1]] = np.maximum.accumulate(raw_sides[tr[: peak + 1]])
        sides[tr[peak:]] = np.minimum.accumulate(raw_sides[tr[peak:]])
    if s.stem_edge_by_height and trunk.any():
        table = np.asarray(s.stem_edge_by_height, float)
        tr = np.nonzero(trunk)[0]
        fine = np.asarray(sorted(set(s.sides_allowed) | {64, 96, 128, 192, 256, 384, 512, 768, 1024}))
        asked = fine[np.clip(np.searchsorted(fine, 2.0 * np.pi * R[tr] / np.interp(X[tr, 2], table[:, 0], table[:, 1])), 0, len(fine) - 1)]
        sides[tr] = np.maximum(sides[tr], asked)
    voff = np.r_[0, np.cumsum(sides)[:-1]]
    NV_ring = int(sides.sum())
    vr = np.repeat(np.arange(NR), sides)
    vj = np.arange(NV_ring) - voff[vr]
    th = 2.0 * np.pi * vj / sides[vr]
    radial = np.cos(th)[:, None] * Nf[vr] + np.sin(th)[:, None] * Bf[vr]
    V = X[vr] + R[vr, None] * radial
    if bt is not None:
        # the stem surface rises in ridges over the main roots
        zone = trunk[vr] & (X[vr, 2] < bt[4]) & (X[vr, 2] > -float(np.max(np.maximum(bt[2], s.buttress_hold_m) + bt[1])))
        if zone.any():
            vz = np.nonzero(zone)[0]
            off = _buttress_offset(np.arctan2(radial[vz, 1], radial[vz, 0]), X[vr[vz], 2], R[vr[vz]], bt, s.buttress_hold_m,
                                   bool(getattr(geometry, "root_flare_min_share", 0.0)))
            V[vz] += off[:, None] * radial[vz]

    # --- faces between consecutive rings ---------------------------------
    faces = []
    pair_a = np.nonzero(np.r_[sa[1:] == sa[:-1], False])[0]
    pair_b = pair_a + 1
    na, nb_ = sides[pair_a], sides[pair_b]
    eq = na == nb_
    for nsd in np.unique(na[eq]):
        selp = eq & (na == nsd)
        oa, ob = voff[pair_a[selp]][:, None], voff[pair_b[selp]][:, None]
        j = np.arange(nsd)[None, :]
        j1 = (j + 1) % nsd
        a0, a1, b0, b1 = oa + j, oa + j1, ob + j, ob + j1
        faces.append(np.stack([a0, a1, b0], -1).reshape(-1, 3))
        faces.append(np.stack([a1, b1, b0], -1).reshape(-1, 3))
    tri = []
    for ra, rb in zip(pair_a[~eq].tolist(), pair_b[~eq].tolist()):
        m_, n_ = int(sides[ra]), int(sides[rb])
        oa, ob = int(voff[ra]), int(voff[rb])
        i = j = 0
        while i < m_ or j < n_:
            if j >= n_ or (i < m_ and (i + 1) * n_ <= (j + 1) * m_):
                tri.append((oa + i, oa + (i + 1) % m_, ob + j % n_))
                i += 1
            else:
                tri.append((oa + i % m_, ob + (j + 1) % n_, ob + j))
                j += 1
    if tri:
        faces.append(np.array(tri, dtype=np.int64))

    # tips: a short cone closing every axis
    ring_last = ring_first + ring_count - 1
    tip_pos = X[ring_last] + Tn[ring_last] * (s.tip_length_factor * R[ring_last])[:, None]
    tip_v = NV_ring + np.arange(len(ring_last))
    for nsd in np.unique(sides[ring_last]):
        selr = sides[ring_last] == nsd
        o = voff[ring_last[selr]][:, None]
        j = np.arange(nsd)[None, :]
        faces.append(np.stack([o + j, o + (j + 1) % nsd, np.repeat(tip_v[selr][:, None], nsd, 1)], -1).reshape(-1, 3))
    # trunk base cap
    extra_pos = [tip_pos]
    extra_ring = [ring_last]
    trunk_rings = np.nonzero(~T.is_lateral[first_nodes[fa]])[0]
    base_v = NV_ring + len(ring_last)
    for tr in trunk_rings.tolist():
        r0 = ring_first[tr]
        nsd = int(sides[r0])
        o = int(voff[r0])
        cv = base_v
        base_v += 1
        extra_pos.append(X[r0][None])
        extra_ring.append(np.array([r0]))
        j = np.arange(nsd)
        faces.append(np.stack([o + (j + 1) % nsd, o + j, np.full(nsd, cv)], -1))

    V = np.concatenate([V] + extra_pos)
    vring = np.concatenate([vr] + extra_ring)
    F = np.concatenate(faces).astype(np.int64)
    around = None
    if s.ring_attributes:
        # share of the way around its ring; NaN for the points that close a tube (tips, base cap)
        around = np.full(len(V), np.nan, np.float32)
        around[:NV_ring] = (vj / sides[vr]).astype(np.float32)

    # --- junction fillets -------------------------------------------------
    ring_s = ss
    for (j, pj, bp, rc, rp, k, s_exit, sin_t) in junctions:
        if rc < s.blend_min_radius or pj < 0:
            continue
        # rings of the child axis j and the parent axis pj
        rj = np.searchsorted(fa, j)
        rp_i = np.searchsorted(fa, pj)
        c_lo, c_n = ring_first[rj], ring_count[rj]
        p_lo, p_n = ring_first[rp_i], ring_count[rp_i]
        c_s = ring_s[c_lo:c_lo + c_n]
        p_s = ring_s[p_lo:p_lo + p_n]
        sj = s_pt[bp]
        w = rc / max(sin_t, 0.25) + 3.0 * k
        # distance fields from ring centre lines
        pr = np.nonzero(np.abs(p_s - sj) <= w + rp)[0]
        if pr.size < 2:
            pr = np.arange(max(0, np.searchsorted(p_s, sj) - 1), min(p_n, np.searchsorted(p_s, sj) + 1))
        if pr.size < 2:
            continue
        p_c, p_r = X[p_lo + pr], R[p_lo + pr]
        cr = np.nonzero(c_s <= s_exit + 4.0 * k + rc)[0]
        if cr.size < 2:
            cr = np.arange(min(2, c_n))
        if cr.size < 2:
            continue
        c_c, c_r = X[c_lo + cr], R[c_lo + cr]
        # child vertices near the parent surface
        r0, r1 = c_lo + cr[0], c_lo + cr[-1] + 1
        v0, v1 = voff[r0], voff[r1 - 1] + sides[r1 - 1]
        x = V[v0:v1]
        nrm = _normalize(x - X[vring[v0:v1]])
        V[v0:v1] = _blend_vertices(x, nrm, p_c, p_r, k)
        if s.no_stem_ridges and T.axis[first_nodes[pj]] == 0 and float(X[p_lo + np.searchsorted(p_s, sj) - 1, 2]) < 0.0:
            # a root off the stem's foot: the stem's surface stays as it is here
            continue
        # parent vertices near the child surface
        r0, r1 = p_lo + pr[0], p_lo + pr[-1] + 1
        v0, v1 = voff[r0], voff[r1 - 1] + sides[r1 - 1]
        x = V[v0:v1]
        nrm = _normalize(x - X[vring[v0:v1]])
        V[v0:v1] = _blend_vertices(x, nrm, c_c, c_r, k)

    # --- keep only the emitted axes (faces never span two axes) ------------
    if emit_axes is not None:
        vkeep = np.isin(T.axis[first_nodes[sa]], emit_axes)[vring]
        if not vkeep.all():
            remap = np.cumsum(vkeep) - 1
            F = remap[F[vkeep[F[:, 0]]]]
            V, vring = V[vkeep], vring[vkeep]
            if around is not None:
                around = around[vkeep]
        if not len(F):
            return None

    # --- normals and attributes ------------------------------------------
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for c in range(3):
        np.add.at(vn, F[:, c], fn)
    vn = _normalize(vn)
    node = ring_node[vring]
    attrs = {
        "birth_year": T.birth[node].astype(np.int32),
        "death_year": T.death[node].astype(np.int32),
        "branch_order": T.order[node].astype(np.int32),
        "radius": R[vring].astype(np.float32),
        "node_id": node.astype(np.int32),
    }
    if s.ring_attributes:
        attrs["ring_around"] = around                               # 0-1 around the tube
        attrs["ring_along"] = ss[vring].astype(np.float32)          # m along the axis from its base
        attrs["axis_id"] = T.axis[node].astype(np.int32)            # 0 = the stem
    return MeshData(vertices=V, faces=F, normals=vn, attributes=attrs)


def combine_with_roots(shoot, roots, r_shoot, r_root, sel_shoot, sel_root):
    """One skeleton for crown and roots, so the stem flares into the root
    system as one continuous surface.

    The living taproot chain is re-rooted: its deepest node becomes the base,
    the chain runs up to the root collar (the stem base) and continues as the
    stem, so taproot and stem are one tube through the ground line.  Main
    roots are laterals of that tube and get the usual collar swelling and
    fillets.  Returns (skeleton, is_root, original_id) per combined node.
    """
    ns, nr = shoot.n, roots.n
    salive = sel_shoot[:ns].copy()
    salive[0] = True
    ralive = sel_root[:nr].copy()
    chain = []
    c = 0
    while roots.main_child[c] >= 0 and ralive[roots.main_child[c]]:
        c = int(roots.main_child[c])
        chain.append(c)
    k = len(chain)
    # new order: deepest taproot node first, chain upwards, then the shoot,
    # then the rest of the roots
    other_roots = np.array([j for j in np.nonzero(ralive)[0].tolist() if j != 0 and j not in set(chain)], dtype=np.int64)
    shoot_ids = np.nonzero(salive)[0]
    chain_ids = np.array(chain[::-1], dtype=np.int64)
    N = k + shoot_ids.size + other_roots.size
    rmap = np.full(nr, -1, dtype=np.int64)
    smap = np.full(ns, -1, dtype=np.int64)
    rmap[chain_ids] = np.arange(k)
    smap[shoot_ids] = k + np.arange(shoot_ids.size)
    rmap[other_roots] = k + shoot_ids.size + np.arange(other_roots.size)
    rmap[0] = smap[0]
    is_root = np.zeros(N, bool)
    is_root[:k] = True
    is_root[k + shoot_ids.size:] = True
    orig = np.concatenate([chain_ids, shoot_ids, other_roots])

    pos = np.concatenate([roots.pos[chain_ids], shoot.pos[shoot_ids], roots.pos[other_roots]])
    radius = np.concatenate([r_root[chain_ids], r_shoot[shoot_ids], r_root[other_roots]])
    parent = np.concatenate([np.full(k, -1), smap[shoot.parent[shoot_ids].clip(0)], rmap[roots.parent[other_roots]]]).astype(np.int64)
    if k:
        parent[: k - 1] = -1
        parent[1:k] = np.arange(k - 1)          # chain[i] hangs below chain[i+1]: reversed
        parent[0] = -1
        parent[smap[0]] = k - 1
    else:
        parent[smap[0]] = -1
    shoot_axis_max = int(shoot.axis[shoot_ids].max()) if shoot_ids.size else 0
    axis = np.concatenate([np.zeros(k, np.int64), shoot.axis[shoot_ids].astype(np.int64),
                           roots.axis[other_roots].astype(np.int64) + shoot_axis_max + 1])
    is_lat = np.concatenate([np.zeros(k, bool), shoot.is_lateral[shoot_ids], roots.is_lateral[other_roots]])
    is_lat[smap[0]] = False
    order = np.concatenate([np.zeros(k, np.int64), shoot.order[shoot_ids], roots.order[other_roots]])
    birth = np.concatenate([roots.birth[chain_ids], shoot.birth[shoot_ids], roots.birth[other_roots]])
    death = np.concatenate([roots.death[chain_ids], shoot.death[shoot_ids], roots.death[other_roots]])
    # depth from the new base, parents first: chain, then shoot and roots
    depth = np.zeros(N, np.int64)
    depth[:k] = np.arange(k)
    depth[k:k + shoot_ids.size] = shoot.depth[shoot_ids] + k
    # root nodes off the chain: depth of the chain node they hang from plus
    # their own distance from it
    attach = np.full(nr, -1, dtype=np.int64)
    attach[0] = 0
    attach[chain_ids] = chain_ids
    rd = roots.depth[:nr]
    order_r = other_roots[np.argsort(rd[other_roots], kind="stable")]
    for j in order_r.tolist():
        attach[j] = attach[roots.parent[j]]
    a = attach[other_roots]
    a_new = np.where(a == 0, depth[smap[0]], depth[np.maximum(rmap[np.maximum(a, 0)], 0)])
    depth[k + shoot_ids.size:] = a_new + (rd[other_roots] - rd[np.maximum(a, 0)])
    if k:
        # with the chain reversed, a node's depth grows upwards along it
        depth[:k] = np.arange(k)
    from types import SimpleNamespace
    skel = SimpleNamespace(n=N, pos=pos, parent=parent, axis=axis, is_lateral=is_lat, order=order,
                           birth=birth, death=death, depth=depth)
    return skel, radius, is_root, orig, k


def split_at_ground(md: MeshData, is_root_node, orig_ids, trunk_node=None):
    """Split a combined mesh into crown and root meshes.  The stem/taproot
    tube (``trunk_node``: combined nodes on axis 0) is cut at the ground
    plane: its faces below ground go to the roots, and the shared ring keeps
    one normal, so the two meshes meet without a seam.  Every other face
    goes with its own part, so a shallow root whose top shows above ground
    stays in the root mesh."""
    V, F = md.vertices, md.faces
    below = V[F].mean(1)[:, 2] < 0.0
    if trunk_node is not None:
        fnode = md.attributes["node_id"][F[:, 0]].astype(np.int64)
        below = np.where(trunk_node[fnode], below, is_root_node[fnode])
    out = []
    for mask, root_part in ((~below, False), (below, True)):
        f = F[mask]
        used = np.unique(f)
        remap = np.full(len(V), -1, dtype=np.int64)
        remap[used] = np.arange(used.size)
        attrs = {k: v[used] for k, v in md.attributes.items()}
        comb = attrs["node_id"].astype(np.int64)
        ids = orig_ids[comb]
        if root_part:
            ids = np.where(is_root_node[comb], ids, 0)          # the collar is root node 0
            attrs["depth_below_ground"] = np.maximum(-V[used, 2], 0.0).astype(np.float32)
        else:
            ids = np.where(is_root_node[comb], 0, ids)          # stem base below the collar
        attrs["node_id"] = ids.astype(np.int32)
        out.append(MeshData(vertices=V[used], faces=remap[f], normals=md.normals[used], attributes=attrs))
    return out[0], out[1]
