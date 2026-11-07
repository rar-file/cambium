"""Game levels of detail for one tree at one age, as .glb files with PBR textures.

    lod0  every part of the mesh, one blade per model leaf, free bark strips
    lod1  thick wood only, coarse rings, alpha-masked leaf cards, inside a triangle budget
    lod2  crossed cards with the tree baked onto them

Everything here reads the finished tree; nothing goes back into growth.  Colours and sizes come
from the species file (``appearance``), so another species needs other values and no new code.
Stages of one tree stay continuous because a part's look depends on its age and size, which change
slowly, and every pattern (noise, leaf, strip) is tied to the part's place or node, not to the age.
"""
from __future__ import annotations

import numpy as np

from . import appearance as ap
from . import mesh as meshlib
from . import textures as tx
from .export import GameGLB, encode_image, validate_glb
from .look_render import Lights, View, bake_views, load_glb_primitives


def join_meshes(parts):
    parts = [p for p in parts if p is not None and len(p.faces)]
    if not parts:
        return None
    off = np.r_[0, np.cumsum([p.n_vertices for p in parts])[:-1]]
    return meshlib.MeshData(np.concatenate([p.vertices for p in parts]), np.concatenate([p.faces + o for p, o in zip(parts, off)]),
                            np.concatenate([p.normals for p in parts]), {k: np.concatenate([p.attributes[k] for p in parts]) for k in parts[0].attributes})


def crown_mesh(skel, select, radius, is_root, orig, geometry, settings, budget=400_000.0):
    """The part of the tree above ground, as one mesh with each vertex's place on its tube."""
    trunk = np.asarray(skel.axis[: skel.n]) == 0
    crowns = []
    for md in meshlib.build_mesh_chunks(skel, select, radius, geometry, settings, budget):
        crown, _ = meshlib.split_at_ground(md, is_root, orig, trunk)
        crowns.append(crown)
    return join_meshes(crowns)


def _tangents(V, N, UV, F):
    """Vertex tangents with w, by the usual sum over faces.  Bitangent = cross(N, T) w points towards
    falling v, which is +y in a glTF normal map."""
    e1, e2 = V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]
    d1, d2 = UV[F[:, 1]] - UV[F[:, 0]], UV[F[:, 2]] - UV[F[:, 0]]
    r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    r = np.where(np.abs(r) < 1e-14, 1e-14, r)[:, None]
    t = (d2[:, 1:2] * e1 - d1[:, 1:2] * e2) / r
    b = (d1[:, 0:1] * e2 - d2[:, 0:1] * e1) / r
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-12)
    T, B = np.zeros_like(V), np.zeros_like(V)
    for c in range(3):
        np.add.at(T, F[:, c], t)
        np.add.at(B, F[:, c], b)
    T = T - (T * N).sum(1, keepdims=True) * N
    n = np.linalg.norm(T, axis=1, keepdims=True)
    # where a vertex got no good sum (tips): any direction across the normal
    alt = np.cross(N, np.where(np.abs(N[:, 2:3]) < 0.9, np.array([0.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])))
    T = np.where(n > 1e-6, T / np.maximum(n, 1e-12), alt / np.maximum(np.linalg.norm(alt, axis=1, keepdims=True), 1e-12))
    w = np.sign((np.cross(N, T) * -B).sum(1))
    w = np.where(w == 0.0, 1.0, w)
    return np.c_[T, w]


def _unwrap(F, around, extra=None):
    """New vertices for the tube seam.  Each face's corners get a position around the tube in
    [0, 1 + a bit]; a corner that needs a different one than its vertex has elsewhere (the seam, a tube's
    closing tip, another atlas column in ``extra``) becomes a vertex of its own.
    Returns (faces over new vertices, old vertex of each new one, around of each new one, extra)."""
    c = around[F].astype(np.float64)
    missing = np.isnan(c)
    lo = np.nanmin(np.where(missing, np.nan, c), axis=1)
    hi = np.nanmax(np.where(missing, np.nan, c), axis=1)
    c = np.where((hi - lo)[:, None] > 0.5, np.where(c < 0.5, c + 1.0, c), c)
    filled = np.nan_to_num(c, nan=0.0)
    mean = filled.sum(1) / np.maximum((~missing).sum(1), 1)
    c = np.where(missing, mean[:, None], c)
    ex = np.zeros(len(F), np.int64) if extra is None else np.asarray(extra, np.int64)
    key = F.astype(np.int64) * (1 << 24) * 16 + np.round(c * (1 << 20)).astype(np.int64) * 16 + ex[:, None]
    uniq, first, inv = np.unique(key.ravel(), return_index=True, return_inverse=True)
    return inv.reshape(F.shape), F.ravel()[first], c.ravel()[first], np.repeat(ex, 3)[first]


class WoodParts:
    """What the wood of one stage needs, in order to write any level: baked textures and their layout."""

    def __init__(self, look: dict, tiles: list, tree_age: int, tree_height: float, dbh_wood_cm: float | None, birth, radius_wood):
        self.look = look
        self.tiles = tiles
        self.age = int(tree_age)
        self.height = float(tree_height)
        self.dbh_ob = ap.over_bark_dbh_cm(look, dbh_wood_cm)
        self.birth = np.asarray(birth)
        self.radius_wood = np.asarray(radius_wood)
        self.stem_bake = None
        self.atlas = None
        self.stem_length = None
        self.layout_uv = None
        self.encoded = {}

    def state(self, part_age, d_wood, z):
        return ap.part_state(self.look, part_age, d_wood, z, self.height, self.dbh_ob)


def _axis_marks(wood: WoodParts, stem_md, shoot, pos: np.ndarray, age: int, radius_history) -> list:
    """(around, s, branch radius) for each branch that has left the stem, living or shed.  ``around``
    from the mesh's own ring at that height, so a mark sits where the branch is.  ``pos``: where the
    parts were at this age; they bend later."""
    n = min(shoot.n, len(radius_history[age]))
    stem_nodes = np.unique(stem_md["node"])
    on_stem = np.zeros(shoot.n, bool)
    on_stem[stem_nodes[stem_nodes < shoot.n]] = True
    idx = np.nonzero(shoot.is_lateral[:n].astype(bool) & (shoot.parent[:n] >= 0) & (shoot.birth[:n] <= age))[0]
    idx = idx[on_stem[shoot.parent[idx]]]
    if idx.size == 0:
        return []
    order = np.argsort(stem_md["s"])
    s_sorted, around_sorted, pos_sorted = stem_md["s"][order], stem_md["around"][order], stem_md["pos"][order]
    rings, ring_at = np.unique(np.round(s_sorted, 4), return_index=True)
    ring_end = np.r_[ring_at[1:], len(s_sorted)]
    out = []
    z_pr = stem_md["z_profile"]
    s_pr = stem_md["s_profile"]
    for i in idx.tolist():
        p = int(shoot.parent[i])
        pz = float(pos[p, 2])
        if pz <= 0.0:
            continue
        s_j = float(np.interp(pz, z_pr, s_pr))
        k = int(np.clip(np.searchsorted(rings, s_j), 0, len(rings) - 1))
        a, b = ring_at[k], ring_end[k]
        centre = pos_sorted[a:b].mean(0)
        d = pos[i] - pos[p]
        d = d - np.array([0.0, 0.0, d[2]])
        vd = pos_sorted[a:b] - centre
        pick = int(np.argmax(vd @ d))
        # shed branches keep the radius they had when last alive
        r = 0.0
        y = age if shoot.death[i] < 0 or shoot.death[i] > age else int(shoot.death[i]) - 1
        h = radius_history[y]
        if i < len(h):
            r = float(h[i])
        if r > 0.0:
            out.append((float(around_sorted[a:b][pick]), s_j, r))
    return out


def bake_wood(wood: WoodParts, crown, shoot, pos: np.ndarray, radius_history) -> None:
    """Bake the stem's texture and the branch atlas from the full mesh of this age."""
    look = wood.look
    ax = crown.attributes["axis_id"]
    node = crown.attributes["node_id"].astype(np.int64)
    is_stem = ax == 0
    s_raw = crown.attributes["ring_along"].astype(np.float64)
    s0 = float(s_raw[is_stem].min()) if is_stem.any() else 0.0
    wood.s0 = s0
    # the stem's profile, ring by ring
    s = s_raw[is_stem] - s0
    uniq, inv = np.unique(np.round(s, 4), return_inverse=True)
    count = np.bincount(inv)
    rad = crown.attributes["radius"][is_stem]
    z = crown.vertices[is_stem, 2]
    nd = node[is_stem]
    r_p = np.bincount(inv, rad) / count
    z_p = np.bincount(inv, z) / count
    # a ring's node has one birth year; take the first
    first = np.zeros(len(uniq), np.int64)
    first[inv[::-1]] = np.nonzero(is_stem)[0][::-1]
    part_age = wood.age - wood.birth[node[first]]
    d_wood = 2.0 * wood.radius_wood[node[first]]
    wood.stem_length = float(uniq[-1])
    prof = tx.StemProfile(uniq, r_p, part_age.astype(np.float64), d_wood.astype(np.float64), z_p)
    stem_md = {"node": nd, "s": s, "around": np.nan_to_num(crown.attributes["ring_around"][is_stem], nan=0.0), "pos": crown.vertices[is_stem],
               "z_profile": np.maximum.accumulate(z_p), "s_profile": uniq}
    marks = _axis_marks(wood, stem_md, shoot, pos, wood.age, radius_history)
    wood.stem_bake = tx.bake_stem(look, wood.tiles, prof, wood.state, marks)
    wood.marks = marks
    wood.profile = prof
    # branch classes: the mean state of the parts in each, by surface area
    bark = look["bark"]
    classes = np.asarray(bark["branch_circumference_m"], float)
    F = crown.faces
    branch_faces = F[~is_stem[F[:, 0]]]
    states = [None] * len(classes)
    wood.class_state = states
    if len(branch_faces):
        cl = _face_class(crown.attributes["radius"], branch_faces, classes)
        V = crown.vertices
        area = 0.5 * np.linalg.norm(np.cross(V[branch_faces[:, 1]] - V[branch_faces[:, 0]], V[branch_faces[:, 2]] - V[branch_faces[:, 0]]), axis=1)
        vstate = wood.state(wood.age - wood.birth[node], 2.0 * wood.radius_wood[node], V[:, 2])
        for k in range(len(classes)):
            sel = cl == k
            if not sel.any():
                continue
            v0 = branch_faces[sel, 0]
            wts = area[sel] / max(area[sel].sum(), 1e-12)
            states[k] = {"weights": (vstate["weights"][:, v0] * wts).sum(1), "peel": float((vstate["peel"][v0] * wts).sum()),
                         "grime": float((vstate["grime"][v0] * wts).sum()), "fissure_m": float((vstate["fissure_m"][v0] * wts).sum())}
    wood.atlas = tx.bake_branch_atlas(look, wood.tiles, states)
    wood.stage_means = np.array([t.mean_colour for t in wood.tiles])
    W, H = bark["atlas_px"]
    wood.layout_uv = [(x0 / W, x1 / W, c) for x0, x1, c in wood.atlas["layout"]]


def _face_class(radius_attr, faces, classes):
    c = 2.0 * np.pi * radius_attr[faces].mean(1)
    edges = np.sqrt(classes[1:] * classes[:-1])
    return np.searchsorted(edges, c)


def _relief(wood: WoodParts, u, v) -> np.ndarray:
    """How far (m) the stem's surface stands out or sinks here, from the baked height with the fine
    detail taken out: mesh rings can hold plates and furrows, not cracks.  Zero where it's smooth."""
    if getattr(wood, "relief_map", None) is None:
        h = wood.stem_bake["height"]
        blur = tx._box_v(tx._box_u(h, 14), 24)
        wood.relief_map = blur - blur.mean(1, keepdims=True)
    m = wood.relief_map
    H, W = m.shape
    rows = np.clip((np.asarray(v) * H).astype(np.int64), 0, H - 1)
    cols = (np.asarray(u) * W).astype(np.int64) % W
    return m[rows, cols]


def wood_arrays(wood: WoodParts, md, relief: bool = False) -> dict:
    """The stem and the branches of one level's mesh, with texture coordinates over this stage's bakes.
    With ``relief`` the stem's rings follow the rough bark, so its outline isn't a smooth tube."""
    look = wood.look
    bark = look["bark"]
    ax = md.attributes["axis_id"]
    node = md.attributes["node_id"].astype(np.int64)
    around = md.attributes["ring_around"]
    along = md.attributes["ring_along"].astype(np.float64)
    F = md.faces
    stem_f = ax[F[:, 0]] == 0
    out = {}
    # the stem: once around, once along
    if stem_f.any():
        f = F[stem_f]
        nf, old, u, _ = _unwrap(f, around)
        V, N = md.vertices[old], md.normals[old]
        s = along[old] - wood.s0
        v = tx.stem_v(look, s, wood.stem_length)
        UV = np.stack([u, v], 1)
        if relief:
            V = V + N * _relief(wood, u, v)[:, None]
        T = _tangents(V, N, UV, nf)
        out["stem"] = {"V": V, "N": N, "F": nf, "UV": UV, "T": T, "node": node[old], "radius": md.attributes["radius"][old], "around": u, "along": s}
    if (~stem_f).any():
        f = F[~stem_f]
        classes = np.asarray(bark["branch_circumference_m"], float)
        cl = _face_class(md.attributes["radius"], f, classes)
        nf, old, u, col = _unwrap(f, around, cl)
        V, N = md.vertices[old], md.normals[old]
        lay = wood.layout_uv
        x0 = np.array([a for a, b, c in lay])[col]
        x1 = np.array([b for a, b, c in lay])[col]
        v = along[old] / float(bark["tile_size_m"])
        UV = np.stack([x0 + (x1 - x0) * np.minimum(u, 1.0), v], 1)
        T = _tangents(V, N, UV, nf)
        st = wood.state(wood.age - wood.birth[node[old]], 2.0 * wood.radius_wood[node[old]], V[:, 2])
        want = ap.state_colour(wood.stage_means, st["weights"])
        have = np.array([ap.state_colour(wood.stage_means, np.asarray((wood.class_state[k] or {"weights": st["weights"][:, 0]})["weights"])[:, None])[0]
                         for k in range(len(classes))])
        tint = want / np.maximum(have[col], 1e-4)
        out["branch"] = {"V": V, "N": N, "F": nf, "UV": UV, "T": T, "node": node[old], "radius": md.attributes["radius"][old], "tint": tint, "col": col,
                         "around": u, "along": along[old]}
    return out


def _encoded_bark(wood: WoodParts, bake: dict, key, jpeg: int, scale: float) -> dict:
    """A bake's maps as image files, once only: the seasons of a stage share their wood."""
    done = wood.encoded.get(key)
    if done is not None:
        return done
    alb, rough, ao, nrm, hgt = bake["albedo"], bake["rough"], bake["ao"], bake["normal"], bake["height"]
    if scale != 1.0:
        k = int(round(1.0 / scale))
        alb, rough, ao, nrm, hgt = (_down(a, k) for a in (alb, rough, ao, nrm, hgt))
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
    lo, hi = float(hgt.min()), float(hgt.max())
    span = max(hi - lo, 1e-6)
    done = {"base": encode_image(ap.linear_to_srgb(alb), kind="jpeg", quality=jpeg),
            "orm": encode_image(np.stack([ao, rough, np.zeros_like(ao)], -1), kind="jpeg_full", quality=jpeg),
            "normal": encode_image(nrm * 0.5 + 0.5, kind="jpeg_full", quality=min(jpeg + 6, 98)),
            "height": encode_image((hgt - lo) / span, kind="jpeg_full", quality=jpeg),
            "range": [lo, hi]}
    wood.encoded[key] = done
    return done


def _bark_material(glb: GameGLB, images: dict, name: str, wrap_s: int, wrap_t: int) -> int:
    base = glb.add_texture(*images["base"], wrap_s, wrap_t, name + "_base")
    orm = glb.add_texture(*images["orm"], wrap_s, wrap_t, name + "_orm")
    normal = glb.add_texture(*images["normal"], wrap_s, wrap_t, name + "_normal")
    height = glb.add_texture(*images["height"], wrap_s, wrap_t, name + "_height")
    return glb.add_material({
        "name": name,
        "pbrMetallicRoughness": {"baseColorTexture": {"index": base}, "metallicRoughnessTexture": {"index": orm}, "metallicFactor": 0.0, "roughnessFactor": 1.0},
        "normalTexture": {"index": normal},
        "occlusionTexture": {"index": orm},
        "extras": {"heightTexture": {"index": height}, "heightRange_m": images["range"]},
    })


def _down(a, k):
    if k <= 1:
        return a
    h, w = a.shape[:2]
    h, w = (h // k) * k, (w // k) * k
    b = a[:h, :w]
    shape = (h // k, k, w // k, k) + a.shape[2:]
    return b.reshape(shape).mean((1, 3))


def add_wood(glb: GameGLB, wood: WoodParts, arrays: dict, jpeg: int, stem_scale: float, atlas_scale: float) -> None:
    if "stem" in arrays:
        m = _bark_material(glb, _encoded_bark(wood, wood.stem_bake, ("stem", stem_scale), jpeg, stem_scale), "bark_stem", 10497, 33071)
        a = arrays["stem"]
        glb.add_mesh("stem", m, a["V"], a["N"], a["F"], a["UV"], a["T"], attributes={"NODE_ID": a["node"], "RADIUS": a["radius"]})
    if "branch" in arrays:
        a = arrays["branch"]
        # each column's colour is raised as far as its parts' tints need, so tints fit in 0-1
        atlas = dict(wood.atlas)
        scale = np.ones((len(wood.layout_uv), 3))
        for k in range(len(wood.layout_uv)):
            sel = a["col"] == k
            if sel.any():
                scale[k] = np.maximum(np.percentile(a["tint"][sel], 99.5, axis=0), 1.0)
        alb = atlas["albedo"].copy()
        W = alb.shape[1]
        for k, (x0, x1, c) in enumerate(atlas["layout"]):
            alb[:, max(x0 - 4, 0):min(x1 + 4, W)] = np.minimum(alb[:, max(x0 - 4, 0):min(x1 + 4, W)] * scale[k].astype(np.float32), 1.0)
        atlas["albedo"] = alb
        m = _bark_material(glb, _encoded_bark(wood, atlas, ("atlas", atlas_scale, id(arrays)), jpeg, atlas_scale), "bark_branch", 33071, 10497)
        colour = np.c_[np.clip(a["tint"] / scale[a["col"]], 0.0, 1.0), np.ones(len(a["V"]))]
        glb.add_mesh("branches", m, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=colour, attributes={"NODE_ID": a["node"], "RADIUS": a["radius"]})


# -- leaves ---------------------------------------------------------------------------------------
LUM = np.array([0.2126, 0.7152, 0.0722])


def leaf_look(look: dict, leaves: ap.LeafInstances, day: float) -> dict:
    """Colours of these leaves on a day of the year, measured reflectance and transmittance, split into
    the numbers a PBR material with diffuse transmission wants: base colour R / (1 - f), transmission
    colour T / f, f the share of light going through.  Without the extension the base colour alone is
    R + T near enough, the brightness of a leaf lit from both sides."""
    chl = ap.chlorophyll_at(look, day, leaves.sun, leaves.delay)
    R, T = ap.leaf_colours(look, chl)
    r, t = (R @ LUM).mean(), (T @ LUM).mean()
    f = float(np.clip(t / max(r + t, 1e-6), 0.05, 0.75))
    base = np.clip(R / (1.0 - f), 0.0, 1.0)
    trans = np.clip(T.mean(0) / f, 0.0, 1.0)
    scale = np.maximum(base.max(0), 1e-3)
    return {"chlorophyll": chl, "mean_chlorophyll": float(chl.mean()), "tint": base / scale, "scale": scale, "base": base, "dt_factor": f, "dt_colour": trans}


def _turning(mean_chl: float, lead: float) -> float:
    """How far yellow has gone between the veins: nothing when all green or all yellow."""
    m = float(np.clip(mean_chl, 0.0, 1.0))
    return float(lead) * 4.0 * m * (1.0 - m)


def _leaf_material(glb: GameGLB, name, tex: dict, ll: dict, jpeg: int) -> int:
    srgb = ap.linear_to_srgb(tex["rgb"])
    t_base = glb.add_texture(*encode_image(srgb, tex["alpha"]), 10497, 10497, name + "_base")
    mean = np.maximum((tex["rgb"] * tex["alpha"][..., None]).reshape(-1, 3).sum(0) / max(float(tex["alpha"].sum()), 1.0), 1e-3)
    factor = np.minimum(ll["scale"] / mean, 1.0)
    mat = {
        "name": name,
        "alphaMode": "MASK",
        "alphaCutoff": 0.5,
        "doubleSided": True,
        "pbrMetallicRoughness": {"baseColorTexture": {"index": t_base}, "baseColorFactor": [float(x) for x in factor] + [1.0], "metallicFactor": 0.0, "roughnessFactor": 0.5},
        "extensions": {"KHR_materials_diffuse_transmission": {"diffuseTransmissionFactor": ll["dt_factor"], "diffuseTransmissionColorFactor": [float(x) for x in ll["dt_colour"]]}},
    }
    if "normal" in tex:
        n = glb.add_texture(*encode_image(tex["normal"] * 0.5 + 0.5, kind="jpeg_full", quality=jpeg + 4), 10497, 10497, name + "_normal")
        mat["normalTexture"] = {"index": n}
    return glb.add_material(mat)


def blades_arrays(look: dict, leaves: ap.LeafInstances, ll: dict) -> dict:
    """One blade each: four vertices, two triangles, folded along the midrib."""
    lv = look["leaves"]
    n = len(leaves.node)
    w0 = float(lv["shape"]["widest_at"])
    fold = np.radians(float(lv["fold_deg"]))
    a, c = leaves.along, leaves.across
    nrm = np.cross(a, c)
    L, W = leaves.length[:, None], leaves.width[:, None]
    side_out = 0.5 * W * np.cos(fold)
    side_down = 0.5 * W * np.sin(fold)
    mid = leaves.base + a * (w0 * L)
    V = np.stack([leaves.base, mid + c * side_out - nrm * side_down, leaves.base + a * L, mid - c * side_out - nrm * side_down], 1).reshape(-1, 3)
    # normals lean out over the fold, so a blade isn't flat-lit
    N = np.stack([nrm - a * 0.25, nrm + c * 0.45, nrm + a * 0.25, nrm - c * 0.45], 1).reshape(-1, 3)
    i = np.arange(n) * 4
    F = np.concatenate([np.stack([i, i + 3, i + 2], 1), np.stack([i, i + 2, i + 1], 1)])
    uv = np.array([[0.5, 1.0], [1.0, 1.0 - w0], [0.5, 0.0], [0.0, 1.0 - w0]])
    UV = np.tile(uv, (n, 1))
    T = np.tile(c, (1, 4)).reshape(-1, 3)
    # u runs with +across; bitangent along the blade towards the tip, which is v falling
    w = np.sign((np.cross(N, T) * np.repeat(a, 4, axis=0)).sum(1))
    T = T - (T * N).sum(1, keepdims=True) * N / np.maximum((N * N).sum(1, keepdims=True), 1e-9)
    colour = np.c_[np.repeat(ll["tint"], 4, axis=0), np.ones(4 * n)]
    return {"V": V, "N": N, "F": F, "UV": UV, "T": np.c_[T, np.where(w == 0, 1.0, w)], "colour": colour,
            "node": np.repeat(leaves.node, 4), "sun": np.repeat(leaves.sun, 4), "turn": np.repeat(leaves.delay, 4)}


def leaf_cards(look: dict, leaves: ap.LeafInstances, ll: dict, target: int, coverage: list, grid: int, centre: np.ndarray, return_groups: bool = False) -> dict:
    """Leaves gathered into alpha-masked cards by a grid over the crown, with the grid's cell size
    searched so the count meets ``target``.  Each card is sized so its opaque area is the leaf area
    it stands for, which keeps the crown's shade."""
    if len(leaves.node) == 0 or target < 1:
        return None
    P = leaves.base + 0.5 * leaves.along * leaves.length[:, None]

    def group(cell):
        q = np.floor(P / cell).astype(np.int64)
        q -= q.min(0)
        m = q.max(0) + 1
        key = q[:, 0] * m[1] * m[2] + q[:, 1] * m[2] + q[:, 2]
        return np.unique(key, return_inverse=True)

    lo, hi = 0.02, float(np.ptp(P, axis=0).max()) + 0.1
    for _ in range(24):
        cell = np.sqrt(lo * hi)
        uniq, inv = group(cell)
        if len(uniq) > target:
            lo = cell
        else:
            hi = cell
    uniq, inv = group(hi)
    m = len(uniq)
    area = np.bincount(inv, leaves.area, m)
    centre_c = np.stack([np.bincount(inv, P[:, k], m) / np.bincount(inv, minlength=m) for k in range(3)], 1)
    tint = np.stack([np.bincount(inv, ll["tint"][:, k] * leaves.area, m) / area for k in range(3)], 1)
    key = uniq.astype(np.int64)
    variant = np.minimum((ap.hash01(key, 41) * len(coverage)).astype(np.int64), len(coverage) - 1)
    cov = np.asarray(coverage)[variant]
    side = np.sqrt(area / np.maximum(cov, 1e-3))
    az = ap.hash01(key, 42) * 2.0 * np.pi
    tilt = np.radians(25.0 + 45.0 * ap.hash01(key, 43))
    # the plane of a card leans like the leaves do
    u = np.stack([-np.sin(az), np.cos(az), np.zeros(m)], 1)
    w = np.stack([np.cos(az) * np.cos(tilt), np.sin(az) * np.cos(tilt), -np.sin(tilt)], 1)
    n = np.cross(w, u)
    corners = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    V = (centre_c[:, None, :] + side[:, None, None] * (corners[None, :, 0, None] * u[:, None, :] + corners[None, :, 1, None] * w[:, None, :])).reshape(-1, 3)
    # normals lean outward from the crown, so it shades as a mass
    out = V - centre
    out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-6)
    N = 0.45 * np.repeat(n, 4, axis=0) + 0.55 * out
    i = np.arange(m) * 4
    F = np.concatenate([np.stack([i, i + 2, i + 1], 1), np.stack([i, i + 3, i + 2], 1)])
    gx = (variant % grid).astype(np.float64)
    gy = (variant // grid).astype(np.float64)
    uv = np.stack([(gx[:, None] + corners[None, :, 0] + 0.5) / grid, (gy[:, None] + 1.0 - (corners[None, :, 1] + 0.5)) / grid], -1).reshape(-1, 2)
    T = np.repeat(u, 4, axis=0)
    T = T - (T * N).sum(1, keepdims=True) * N / np.maximum((N * N).sum(1, keepdims=True), 1e-9)
    wt = np.sign((np.cross(N, T) * np.repeat(w, 4, axis=0)).sum(1))
    colour = np.c_[np.repeat(tint, 4, axis=0), np.ones(4 * m)]
    out = {"V": V, "N": N, "F": F, "UV": uv, "T": np.c_[T, np.where(wt == 0, 1.0, wt)], "colour": colour, "represented_area": float((side * side * cov).sum())}
    if return_groups:
        out.update(groups=inv, count=m)
    return out


# -- bark strips ----------------------------------------------------------------------------------
def add_strips(glb: GameGLB, look: dict, strips: ap.PeelStrips, tex: dict) -> None:
    t = glb.add_texture(*encode_image(ap.linear_to_srgb(tex["rgb"]), tex["alpha"]), 33071, 33071, "bark_strip_base")
    m = glb.add_material({"name": "bark_strip", "alphaMode": "MASK", "alphaCutoff": 0.5, "pbrMetallicRoughness": {"baseColorTexture": {"index": t}, "metallicFactor": 0.0, "roughnessFactor": 0.7}})
    glb.add_mesh("bark_strips", m, strips.vertices, strips.normals, strips.faces, strips.uv, _tangents(strips.vertices, strips.normals, strips.uv, strips.faces), colour=strips.colour)


# -- far level ------------------------------------------------------------------------------------
def _dilate(rgb, cover, it=10):
    """Carry colour past the edge of the opaque part, so distant mips don't darken at the rim."""
    out = rgb.copy()
    have = (cover > 0.02).astype(np.float32)
    for _ in range(it):
        w = sum(np.roll(np.roll(have, dy, 0), dx, 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c = sum(np.roll(np.roll(out * have[..., None], dy, 0), dx, 1) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        new = (have == 0) & (w > 0)
        out[new] = c[new] / w[new, None]
        have = np.where(new, 1.0, have)
    return out


def far_sheets(near_path, cfg: dict) -> dict:
    """Crossed cards with the tree baked on, from the near level's file: colour, normal and coverage,
    with no lighting in them.  Each card is two one-sided sheets back to back, each with its own view,
    so the lighting holds from either side, where a two-sided card would turn its normals over.  The
    same directions at every age, so stages line up."""
    prims = load_glb_primitives(near_path)
    V = np.concatenate([p.V for p in prims])
    hi = V.max(0)
    centre = np.array([0.0, 0.0, 0.5 * max(hi[2], 0.5)])
    half_h = 0.5 * max(hi[2], 0.5) * 1.03
    half_w = float(max(np.abs(V[:, :2]).max(), 0.05 * half_h)) * 1.03
    cards = int(cfg["cards"])
    views = 2 * cards
    px = int(cfg["texture_px"])
    cell_w = min(max(int(round(px * half_w / half_h)), 16), px)
    frame_h = half_w * px / cell_w
    alb_sheet = np.zeros((px, cell_w * views, 3), np.float32)
    nrm_sheet = np.zeros((px, cell_w * views, 3), np.float32)
    cov_sheet = np.zeros((px, cell_w * views), np.float32)
    verts, norms, faces, uvs, tans = [], [], [], [], []
    shade = Lights(prims, (0.0, 0.0, 1.0), res=16, sky_res=512, sky_dirs=6)
    for k in range(views):
        az = np.pi * k / cards
        d = np.array([np.cos(az), np.sin(az), 0.0])
        view = View(centre + d * 100.0, centre, cell_w, px, ortho_half_h=frame_h)
        b = bake_views(prims, view, lights=shade)
        cov = b["coverage"]
        col = _dilate(b["albedo"], cov)
        # normals into the card's own frame: +x right, +y up, +z towards the viewer
        n = b["normal"]
        nrm = np.stack([n @ view.right.astype(np.float32), n @ view.up.astype(np.float32), np.maximum(n @ (-view.fwd).astype(np.float32), 0.05)], -1)
        nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
        nrm = np.where((cov > 0.0)[..., None], nrm, np.array([0.0, 0.0, 1.0], np.float32))
        x0 = k * cell_w
        alb_sheet[:, x0:x0 + cell_w] = col
        nrm_sheet[:, x0:x0 + cell_w] = nrm
        cov_sheet[:, x0:x0 + cell_w] = cov
        r, u_ = view.right, view.up
        verts.append(np.stack([centre - r * half_w - u_ * half_h, centre + r * half_w - u_ * half_h, centre + r * half_w + u_ * half_h, centre - r * half_w + u_ * half_h]))
        norms.append(np.tile(-view.fwd, (4, 1)))
        # the bake's frame may be taller than the card
        rel = half_h / frame_h
        v_lo, v_hi = 0.5 + 0.5 * rel, 0.5 - 0.5 * rel
        uvs.append(np.array([[k / views, v_lo], [(k + 1) / views, v_lo], [(k + 1) / views, v_hi], [k / views, v_hi]]))
        tans.append(np.tile(np.r_[r, 1.0], (4, 1)))
        i = 4 * k
        faces.append(np.array([[i, i + 1, i + 2], [i, i + 2, i + 3]]))
    return {"albedo": alb_sheet, "normal": nrm_sheet, "coverage": cov_sheet, "V": np.concatenate(verts), "N": np.concatenate(norms), "F": np.concatenate(faces),
            "UV": np.concatenate(uvs), "T": np.concatenate(tans)}


def far_cards(look: dict, near_path, cfg: dict, glb: GameGLB, jpeg: int) -> None:
    """The far level, written into ``glb``."""
    f = far_sheets(near_path, cfg)
    alpha = np.clip(f["coverage"] ** 0.6 * 1.25, 0.0, 1.0)
    tb = glb.add_texture(*encode_image(ap.linear_to_srgb(f["albedo"]), alpha), 33071, 33071, "far_base")
    tn = glb.add_texture(*encode_image(f["normal"] * 0.5 + 0.5, kind="jpeg_full", quality=jpeg + 4), 33071, 33071, "far_normal")
    m = glb.add_material({"name": "far_card", "alphaMode": "MASK", "alphaCutoff": 0.5,
                          "pbrMetallicRoughness": {"baseColorTexture": {"index": tb}, "metallicFactor": 0.0, "roughnessFactor": 0.8}, "normalTexture": {"index": tn}})
    glb.add_mesh("far_cards", m, f["V"], f["N"], f["F"], f["UV"], f["T"])


def reduced_selection(skel, rad_ob, thr: float) -> np.ndarray:
    """The wood a reduced level keeps: the stem, and all wood at least ``thr`` thick that hangs from
    wood it keeps.  A part thicker than the part below it (the pipe model allows that) goes with it,
    so every axis stays one unbroken tube, as the mesher needs."""
    n = skel.n
    r = np.asarray(rad_ob[:n])
    parent = np.asarray(skel.parent[:n])
    trunk = np.asarray(skel.axis[:n]) == 0
    keep = (r >= thr) | trunk
    order = np.argsort(np.asarray(skel.depth[:n]), kind="stable")
    good = keep.tolist()
    par = parent.tolist()
    for i in order.tolist():
        p = par[i]
        if p >= 0 and not good[p]:
            good[i] = False
    return np.asarray(good) | trunk


def reduced_radius_threshold(skel, rad_ob, is_root, orig, geometry, settings, wood_budget: int, budget: float = 400_000.0) -> float:
    """The thinnest wood the reduced level keeps, so it fits its share of the budget: bisected over dry
    runs of the mesh.  The stem is always kept."""
    r = np.asarray(rad_ob[: skel.n])
    lo, hi = float(np.percentile(r, 1)), float(r.max())

    def tris(thr):
        md = crown_mesh(skel, reduced_selection(skel, rad_ob, thr), rad_ob, is_root, orig, geometry, settings, budget)
        return 0 if md is None else len(md.faces)

    if tris(lo) <= wood_budget:
        return lo
    for _ in range(9):
        mid = np.sqrt(lo * hi)
        if tris(mid) > wood_budget:
            lo = mid
        else:
            hi = mid
    return hi


__all__ = ["WoodParts", "add_strips", "add_wood", "bake_wood", "blades_arrays", "crown_mesh", "far_cards", "leaf_cards", "leaf_look",
           "reduced_radius_threshold", "reduced_selection", "validate_glb", "wood_arrays"]
