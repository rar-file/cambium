"""One tree at one age for the game in Unreal 5.8 (`tools/game_export.py export --target unreal`).

The plain export (treegen/game.py) writes a self-contained .glb for any engine.  This one writes what
the game's own pipeline reads, and nothing it would lose on the way in:

* folders laid out as the game's trees are: SourceArt/PolyHaven_split/<asset>/<variant>.gltf (and
  .bin), SourceArt/PolyHaven/<asset>/textures/<slot>_<kind>_2k.png, 8-bit;
* material slots named so ``build_materials.py`` finds their maps and picks the master: bark on
  M_Surface (no alpha in its colour map), leaves and strips on M_Foliage (alpha in its colour map);
* COLOR_0 as the game's plants carry it, for its wind: R flex by path length, G one phase for the
  whole tree, B 1 on leaves, A a leaf id (255 off leaves).  Nothing else goes in vertex colour;
* what Unreal's glTF import throws away (any attribute of our own) in UV channels, at most 4 of them,
  Nanite's limit.  Which channel holds what: ``UV_LAYOUT``, and docs/unreal.md.

Colour that the plain export gave per vertex now lives in textures, so an unmodified M_Surface and
M_Foliage show it: a leaf's UV picks the column of its chlorophyll level in a leaf atlas.

Reads only; nothing goes back into growth, and the plain export is untouched.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np

from . import appearance as ap
from . import game, mesh as meshlib
from . import textures as tx
from .export import GameGLB
from .textures import ALB

CLAMP, REPEAT = 33071, 10497

UV_LAYOUT = {
    "bark": {"UV0": "colour, normal and roughness maps", "UV1": "bark wrap: a whole number of tile widths round the part, tile widths along it",
             "UV2": "x: birth year of the part (part age = stage age - x); y: wood radius, cm",
             "UV3": "x: how white (0-1); y: how rough (0-1)"},
    "leaf": {"UV0": "leaf atlas: the column is the leaf's chlorophyll level on the export's day, the row and the rest of x the blade",
             "UV1": "x + 1024 y: node id", "UV2": "x: days later (+) or earlier (-) than the tree's average to colour; y: light, 0 shade to 1 sun",
             "UV3": "x: chlorophyll fraction on the export's day, before the level is rounded; y: leaf area, cm2"},
    "strip": {"UV0": "strip atlas: the column is the strip's opacity level", "UV1": "x + 1024 y: node id", "UV2": "x: birth year of the part; y: wood radius, cm",
              "UV3": "x: opacity (0-1); y: unused"},
    "card": {"UV0": "card atlas: the column is the card's chlorophyll level", "UV1": "unused",
             "UV2": "x: mean days later or earlier to colour; y: mean light", "UV3": "x: mean chlorophyll on the export's day; y: leaf area the card stands for, cm2"},
    "far": {"UV0": "the card's baked view", "UV1": "unused", "UV2": "unused", "UV3": "unused"},
    "roots": {"UV0": "root atlas: a column by circumference, repeating along", "UV1": "bark wrap, as bark", "UV2": "x: birth year of the root; y: wood radius, cm", "UV3": "x: 0; y: how rough (0-1)"},
}
COLOR0 = "R flex by path length (0 ground, 1 farthest tip), G one phase for the whole tree, B 1 on leaves, A leaf id 0-254 on leaves, 255 elsewhere"


def unreal_look(look: dict) -> dict:
    """The look with the game's numbers where it has its own: its season table."""
    out = copy.deepcopy(look)
    u = look["game"]["unreal"]
    out["leaves"]["season"] = {"chlorophyll_by_day": u["chlorophyll_by_day"], "days": u["days"]}
    return out


def scale_tiles_to_albedo(look: dict, tiles: list) -> dict:
    """White bark at its measured brightness: the game holds all bark to measured albedo.  Each named
    stage's tile is scaled to the mean linear luminance asked for; returns the gains."""
    gains = {}
    y = np.array([0.2126, 0.7152, 0.0722])
    for t in tiles:
        want = (look["game"]["unreal"].get("bark_mean_y") or {}).get(t.name)
        if want is None:
            continue
        gain = float(want) / max(float(t.mean_colour @ y), 1e-6)
        for mip in t.mips:
            mip[..., ALB] *= gain
        t.under = t.under * gain
        gains[t.name] = round(gain, 3)
    return gains


def wind_flex(pos: np.ndarray, parent: np.ndarray, select: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """How far along its stems each node is: path length from the ground over the farthest tip's."""
    n = len(pos)
    path = np.zeros(n)
    step = np.linalg.norm(pos - pos[np.maximum(parent, 0)], axis=1)
    par = parent.tolist()
    stp = step.tolist()
    out = path.tolist()
    for i in np.argsort(depth, kind="stable").tolist():
        p = par[i]
        if p >= 0:
            out[i] = out[p] + stp[i]
    path = np.asarray(out)
    far = float(path[select].max()) if select.any() else 1.0
    return np.clip(path / max(far, 1e-6), 0.0, 1.0)


def _write_png(path: Path, rgb: np.ndarray, alpha: np.ndarray | None = None) -> str:
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.clip(np.asarray(rgb, np.float32), 0.0, 1.0)
    if alpha is not None:
        a = np.concatenate([a, np.clip(np.asarray(alpha, np.float32), 0.0, 1.0)[..., None]], axis=-1)
    Image.fromarray((a * 255.0 + 0.5).astype(np.uint8)).save(path, compress_level=6)
    return path.name


class Maps:
    """Writes a slot's textures, named as the game's material stage looks for them, and adds its material."""

    def __init__(self, out: Path, asset: str):
        self.folder = out / "SourceArt" / "PolyHaven" / asset / "textures"
        self.asset = asset

    def uri(self, name: str) -> str:
        return f"../../PolyHaven/{self.asset}/textures/{name}"

    def write(self, slot: str, colour: np.ndarray, normal: np.ndarray, rough: np.ndarray, alpha: np.ndarray | None = None, height: np.ndarray | None = None,
              cavity: np.ndarray | None = None) -> dict:
        """Colour is linear.  Roughness in red (what M_Surface and M_Foliage read), height in green,
        cavity in blue, as the game's plant masks.  Alpha in the colour map's own alpha."""
        d = {}
        d["diff"] = _write_png(self.folder / f"{slot}_diff_2k.png", ap.linear_to_srgb(colour), alpha)
        d["nor"] = _write_png(self.folder / f"{slot}_nor_gl_2k.png", normal * 0.5 + 0.5)
        zero = np.zeros(rough.shape, np.float32)
        d["rough"] = _write_png(self.folder / f"{slot}_rough_2k.png", np.stack([rough, zero if height is None else height, zero if cavity is None else cavity], -1))
        return d

    def material(self, glb: GameGLB, slot: str, files: dict, wrap_s: int, wrap_t: int, alpha_clip: float | None = None, two_sided: bool = False, extras: dict | None = None) -> int:
        tb = glb.add_texture_uri(self.uri(files["diff"]), wrap_s, wrap_t, files["diff"][:-4])
        tn = glb.add_texture_uri(self.uri(files["nor"]), wrap_s, wrap_t, files["nor"][:-4])
        tr = glb.add_texture_uri(self.uri(files["rough"]), wrap_s, wrap_t, files["rough"][:-4])
        mat = {"name": slot, "pbrMetallicRoughness": {"baseColorTexture": {"index": tb}, "metallicFactor": 0.0, "roughnessFactor": 0.6},
               "normalTexture": {"index": tn}, "extras": {"color0": "wind", "rough_map": {"index": tr}, **(extras or {})}}
        if alpha_clip is not None:
            mat.update(alphaMode="MASK", alphaCutoff=float(alpha_clip))
        if two_sided:
            mat["doubleSided"] = True
        return glb.add_material(mat)


def _colour0(flex, phase, flutter, leaf_id) -> np.ndarray:
    n = len(flex)
    return np.stack([flex, np.full(n, phase), np.full(n, flutter), leaf_id], 1)


def _node_uv(node) -> np.ndarray:
    """A node id as two numbers that come through 16-bit UVs and Nanite's 14-bit ones exactly."""
    node = np.asarray(node, np.int64)
    return np.stack([node % 1024, node // 1024], 1).astype(np.float32)


# -- bark -------------------------------------------------------------------------------------------
def _bark_maps(maps: Maps, slot: str, bake: dict, scale: float = 1.0) -> dict:
    alb, rough, ao, nrm, hgt = bake["albedo"], bake["rough"], bake["ao"], bake["normal"], bake["height"]
    if scale != 1.0:
        k = int(round(1.0 / scale))
        alb, rough, ao, nrm, hgt = (game._down(a, k) for a in (alb, rough, ao, nrm, hgt))
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
    lo, hi = float(hgt.min()), float(hgt.max())
    files = maps.write(slot, alb, nrm, rough, height=(hgt - lo) / max(hi - lo, 1e-6), cavity=ao)
    return {**files, "height_range_m": [lo, hi]}


def _bark_mesh(glb: GameGLB, wood: game.WoodParts, a: dict, name: str, material: int, flex: np.ndarray, phase: float, turns, tile_m: float) -> None:
    node = a["node"]
    birth = wood.birth[node].astype(np.float64)
    st = wood.state(wood.age - birth, 2.0 * wood.radius_wood[node], a["V"][:, 2])
    k = st["weights"]
    white = k[1] if len(k) > 1 else np.zeros(len(node))
    rough = k[2] if len(k) > 2 else np.zeros(len(node))
    uv1 = np.stack([a["around"] * turns, a["along"] / tile_m], 1)
    uv2 = np.stack([birth, wood.radius_wood[node] * 100.0], 1)
    uv3 = np.stack([white, rough], 1)
    colour = _colour0(flex[node], phase, 0.0, np.ones(len(node)))
    glb.add_mesh(name, material, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=colour, colour_8bit=True, extra_uv=[uv1, uv2, uv3], attributes={"NODE_ID": node})


# -- roots ------------------------------------------------------------------------------------------
def tree_meshes(skel, select, radius, is_root, orig, geometry, settings, budget: float = 400_000.0) -> tuple:
    """The tree above ground and its roots, from one pass of the mesher, so they meet ring for ring."""
    trunk = np.asarray(skel.axis[: skel.n]) == 0
    crowns, roots = [], []
    for md in meshlib.build_mesh_chunks(skel, select, radius, geometry, settings, budget):
        crown, root = meshlib.split_at_ground(md, is_root, orig, trunk)
        crowns.append(crown)
        roots.append(root)
    return game.join_meshes(crowns), game.join_meshes(roots)


def _face_subset(md: meshlib.MeshData, mask: np.ndarray) -> meshlib.MeshData | None:
    f = md.faces[mask]
    if not len(f):
        return None
    used = np.unique(f)
    remap = np.full(len(md.vertices), -1, np.int64)
    remap[used] = np.arange(len(used))
    return meshlib.MeshData(md.vertices[used], remap[f], md.normals[used], {k: v[used] for k, v in md.attributes.items()})


def ground_line(model, age: int, cfg: dict) -> float:
    """Where the game's ground should meet the tree, in the model's frame: below its z = 0 by a share of
    the root collar's radius, so the model's own thick roots break it.  Its z = 0 itself has almost none
    above it (``root_table``)."""
    collar = float(np.asarray(model.roots.radius_history[age], float).max())
    return -min(float(cfg["ground_line_max_m"]), float(cfg["ground_line_radii"]) * collar)


def split_roots(md: meshlib.MeshData | None, cfg: dict, line: float) -> tuple:
    """The roots as three parts: the stem's foot and the thick roots, which go with the tree, down to a
    little below the ground line so uneven ground meets them without a gap, and everything else, which
    is under ground.  They share their rings' vertices, so no seam.  Thin roots stay in the last part
    even if they're shallow: drawn, they'd hang as threads over the ground, because the model's run
    just under its z = 0, above the ground line."""
    if md is None:
        return None, None, None
    z = md.vertices[md.faces][..., 2]
    radius = md.attributes["radius"][md.faces].mean(1)
    stem = md.attributes["axis_id"][md.faces[:, 0]] == 0
    near = z.min(1) >= line - float(cfg["surface_depth_m"])
    foot = near & stem
    surface = near & ~stem & (radius >= float(cfg["surface_min_radius_m"]))
    return _face_subset(md, foot), _face_subset(md, surface), _face_subset(md, ~(foot | surface))


def root_radii(look: dict, model, age: int, rad_ob: np.ndarray, skel, is_root: np.ndarray, line: float, cfg: dict, dbh_ob: float) -> np.ndarray:
    """Radii for meshing roots that can be seen: the model's are wood.  Thick roots get their bark; the
    taproot's top keeps the stem's thickness down to the ground line, where the model's wood radius would
    otherwise make a step in from the stem's bark.  Reads the model's shape; changes nothing in it."""
    out = np.asarray(rad_ob, float).copy()
    n = skel.n
    root = np.asarray(is_root[:n], bool)
    z = np.asarray(skel.pos[:n, 2], float)
    r = out[:n]
    wall = ap.bark_wall_m(look, 2.0 * r, dbh_ob)
    grow = np.clip((r - 0.005) / 0.01, 0.0, 1.0)
    out[:n] = np.where(root, r + wall * grow, r)
    axis0 = np.asarray(skel.axis[:n]) == 0
    stem = np.nonzero(axis0 & ~root)[0]
    if len(stem):
        foot_r = float(rad_ob[stem[np.argmin(z[stem])]])
        chain = axis0 & root
        fade = float(cfg["foot_fade_m"])
        t = np.clip((line - z) / max(fade, 1e-6), 0.0, 1.0)
        want = foot_r + (out[:n] - foot_r) * (t * t * (3.0 - 2.0 * t))
        out[:n] = np.where(chain, np.maximum(out[:n], want), out[:n])
    return out


def foot_arrays(look: dict, wood: game.WoodParts, md: meshlib.MeshData | None, stem_node: int) -> dict | None:
    """The stem below the model's z = 0, down to where the ground can reach, in the stem's own bake:
    its texture rows mirrored at z = 0 and its relief carried on, so no line shows where it joins."""
    if md is None:
        return None
    nf, old, u, _ = game._unwrap(md.faces, md.attributes["ring_around"])
    V, N = md.vertices[old], md.normals[old]
    s = np.abs(md.attributes["ring_along"][old].astype(np.float64) - wood.s0)
    v = tx.stem_v(look, s, wood.stem_length)
    UV = np.stack([u, v], 1)
    V = V + N * game._relief(wood, u, v)[:, None]
    return {"V": V, "N": N, "F": nf, "UV": UV, "T": game._tangents(V, N, UV, nf), "node": np.full(len(V), stem_node, np.int64), "around": u, "along": s}


def root_state(wood: game.WoodParts, part_age, d_wood) -> dict:
    """A root's bark, the stem's rough stage whatever its age: no root shows a shoot's red or a stem's
    white under the soil.  TUNED."""
    st = wood.state(part_age, d_wood, np.zeros(len(np.atleast_1d(part_age))))
    w = np.zeros_like(np.asarray(st["weights"], float))
    w[0] = 1.0
    w[-1] = 1.0
    return {**st, "weights": w, "peel": np.zeros_like(st["peel"])}


def root_atlas(look: dict, wood: game.WoodParts, tiles: list, md: meshlib.MeshData, birth: np.ndarray, radius_now: np.ndarray, cfg: dict) -> dict:
    """The branch atlas's layout, baked with what the roots are, stained by the soil."""
    classes = np.asarray(look["bark"]["branch_circumference_m"], float)
    node = md.attributes["node_id"].astype(np.int64)
    F = md.faces
    V = md.vertices
    cl = game._face_class(md.attributes["radius"], F, classes)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    st = root_state(wood, wood.age - birth[node], 2.0 * radius_now[node])
    states = [None] * len(classes)
    for k in range(len(classes)):
        sel = cl == k
        if sel.any():
            v0 = F[sel, 0]
            wts = area[sel] / max(area[sel].sum(), 1e-12)
            states[k] = {"weights": (st["weights"][:, v0] * wts).sum(1), "peel": 0.0, "grime": float((st["grime"][v0] * wts).sum()), "fissure_m": float((st["fissure_m"][v0] * wts).sum())}
    atlas = tx.bake_branch_atlas(look, tiles, states)
    atlas["albedo"] = atlas["albedo"] * np.asarray(cfg["soil_tint"], np.float32)
    W = look["bark"]["atlas_px"][0]
    atlas["layout_uv"] = [(x0 / W, x1 / W, c) for x0, x1, c in atlas["layout"]]
    return atlas


def root_arrays(look: dict, wood: game.WoodParts, md: meshlib.MeshData | None, atlas: dict, birth: np.ndarray, radius_now: np.ndarray) -> dict | None:
    """As ``game.wood_arrays`` does a branch: a turn round each root is a column of the atlas."""
    if md is None:
        return None
    classes = np.asarray(look["bark"]["branch_circumference_m"], float)
    cl = game._face_class(md.attributes["radius"], md.faces, classes)
    nf, old, u, col = game._unwrap(md.faces, md.attributes["ring_around"], cl)
    V, N = md.vertices[old], md.normals[old]
    lay = atlas["layout_uv"]
    x0 = np.array([a for a, b, c in lay])[col]
    x1 = np.array([b for a, b, c in lay])[col]
    along = md.attributes["ring_along"][old].astype(np.float64)
    UV = np.stack([x0 + (x1 - x0) * np.minimum(u, 1.0), along / float(look["bark"]["tile_size_m"])], 1)
    node = np.minimum(md.attributes["node_id"][old].astype(np.int64), len(radius_now) - 1)
    return {"V": V, "N": N, "F": nf, "UV": UV, "T": game._tangents(V, N, UV, nf), "node": node, "around": u, "along": along, "col": col}


def _root_mesh(glb: GameGLB, wood: game.WoodParts, a: dict, name: str, material: int, birth: np.ndarray, radius_now: np.ndarray, phase: float, tile_m: float) -> None:
    """Roots don't sway: flex 0 everywhere, so a wind that reads COLOR_0 leaves them still."""
    node = a["node"]
    st = root_state(wood, wood.age - birth[node].astype(np.float64), 2.0 * radius_now[node])
    k = st["weights"]
    turns = _column_turns(wood.look, a["col"], tile_m)
    uv1 = np.stack([a["around"] * turns, a["along"] / tile_m], 1)
    uv2 = np.stack([birth[node].astype(np.float64), radius_now[node] * 100.0], 1)
    uv3 = np.stack([k[1] if len(k) > 1 else np.zeros(len(node)), k[2] if len(k) > 2 else np.zeros(len(node))], 1)
    glb.add_mesh(name, material, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=_colour0(np.zeros(len(node)), phase, 0.0, np.ones(len(node))), colour_8bit=True, extra_uv=[uv1, uv2, uv3])


def _column_turns(look: dict, col: np.ndarray, tile_m: float) -> np.ndarray:
    """A whole number of bark tiles round a part of each circumference class, so a wrapped scan closes."""
    c = np.asarray(look["bark"]["branch_circumference_m"], float)
    return np.maximum(np.round(c / tile_m), 1.0)[col]


def root_table(model, age: int) -> dict:
    """What the model's roots are at this age."""
    R = model.roots.tree
    h = model.roots.radius_history[age]
    m = len(h)
    alive = (R.birth[:m] <= age) & ((R.death[:m] < 0) | (R.death[:m] > age))
    idx = np.nonzero(alive)[0]
    idx = idx[idx > 0]
    z = R.pos[idx, 2]
    r = h[idx]
    seg = np.linalg.norm(R.pos[idx] - R.pos[R.parent[idx]], axis=1)
    top = z + r
    return {"length_m": round(float(seg.sum()), 1), "max_radius_cm": round(float(r.max()) * 100.0, 1), "deepest_m": round(float(-z.min()), 3),
            "spread_m": round(float(np.hypot(R.pos[idx, 0], R.pos[idx, 1]).max()), 2), "top_above_ground_m": round(float(seg[top > 0].sum()), 2),
            "highest_top_cm": round(float(top.max()) * 100.0, 1)}


def thick_breaking(model, age: int, line: float) -> dict:
    """The roots of 1 cm or more that break the ground at this line."""
    R = model.roots.tree
    h = np.asarray(model.roots.radius_history[age], float)
    m = len(h)
    idx = np.nonzero((R.birth[:m] <= age) & ((R.death[:m] < 0) | (R.death[:m] > age)))[0]
    idx = idx[(idx > 0) & (R.pos[idx, 2] + h[idx] > line) & (h[idx] > 0.01)]
    if not len(idx):
        return {"length_m": 0.0, "reach_m": 0.0}
    seg = np.linalg.norm(R.pos[idx] - R.pos[R.parent[idx]], axis=1)
    return {"length_m": round(float(seg.sum()), 2), "reach_m": round(float(np.hypot(R.pos[idx, 0], R.pos[idx, 1]).max()), 2)}


def black_zone(wood: game.WoodParts) -> dict:
    """Up the stem, where the rough base gives way to what's above it: BarkStartCm and BarkBlendCm for
    M_Surface's UpperBark, which fades from the colour map to a tiled scan."""
    prof = wood.profile
    w = wood.state(prof.part_age, prof.d_wood, prof.z)["weights"]
    rough = w[2] if len(w) > 2 else np.zeros(len(prof.z))
    z = np.maximum.accumulate(prof.z)
    hi = z[rough >= 0.9]
    lo = z[rough >= 0.1]
    start = float(hi.max()) if len(hi) else 0.0
    end = float(lo.max()) if len(lo) else start
    return {"bark_start_cm": round(start * 100.0, 1), "bark_blend_cm": round(max(end - start, 0.05) * 100.0, 1)}


# -- leaves -----------------------------------------------------------------------------------------
def leaf_atlas(look: dict, seed: int) -> dict:
    """The leaf at each chlorophyll level, in columns: its measured colour at that level, yellow coming
    first between the veins.  Mean colour of a column is the diffuse reflectance measured at its level."""
    u = look["game"]["unreal"]
    levels = int(u["leaf_levels"])
    fractions = np.linspace(float(u["leaf_level_range"][0]), float(u["leaf_level_range"][1]), levels)
    n = int(look["leaves"]["texture_size_px"])
    R, _ = ap.leaf_colours(look, fractions)
    rgb = np.zeros((n, n * levels, 3), np.float32)
    nrm = np.zeros((n, n * levels, 3), np.float32)
    rough = np.full((n, n * levels), 0.5, np.float32)
    mask = None
    for i, f in enumerate(fractions):
        blade = tx.leaf_blade(look, seed, game._turning(float(f), look["leaves"]["interveinal_lead"]))
        a = blade["alpha"]
        mean = np.maximum((blade["rgb"] * a[..., None]).reshape(-1, 3).sum(0) / max(float(a.sum()), 1.0), 1e-4)
        colour = blade["rgb"] * (R[i] / mean).astype(np.float32)
        # the mesh is cut to the blade's outline, so what lies past it only needs to be leaf-coloured
        rgb[:, i * n:(i + 1) * n] = tx.push_pull_fill(colour, (a >= 0.5).astype(np.float32))
        nrm[:, i * n:(i + 1) * n] = blade["normal"]
        rough[:, i * n:(i + 1) * n] = 0.5 - 0.12 * np.clip(blade["normal"][..., 2] - 0.9, 0.0, 0.1) * 10.0
        mask = a
    return {"rgb": rgb, "normal": nrm, "rough": rough, "fractions": fractions, "mask": mask}


def blade_mesh(look: dict, leaves: ap.LeafInstances, chl: np.ndarray, fractions: np.ndarray) -> dict:
    """Each leaf its real outline, cut in the mesh (as the game's plants are), with no alpha for a voxel
    build to lose and a midrib fold that gives it some depth: rows from base to tip,
    folded along the midrib and bent back at the tip, with coarse teeth.  Area exactly the model's."""
    u = look["game"]["unreal"]
    rows = int(u["leaf_rows"])
    lv = look["leaves"]
    t = np.linspace(0.0, 1.0, rows + 1)
    tooth = np.where(np.arange(rows + 1) % 2 == 1, float(u["leaf_tooth"]), 0.0)
    half = np.maximum(tx.leaf_half_width(look, t) - tooth, 0.0)
    half[0] = half[-1] = 0.0
    aspect = float(lv["shape"]["aspect"])
    # area of the outline for a blade of length 1: 2 sides x half width x 1 / (2 aspect)
    unit = float(np.trapezoid(half, t)) / aspect
    n = len(leaves.node)
    L = np.sqrt(leaves.area / unit)
    Wh = 0.5 * L / aspect
    a, c = leaves.along, leaves.across
    nrm = np.cross(a, c)
    fold = np.radians(float(lv["fold_deg"]))
    curl = float(u["leaf_curl"])
    # vertices: base, then (middle, +side, -side) per inner row, then tip
    inner = rows - 1
    per = 2 + 3 * inner
    V = np.zeros((n, per, 3))
    UV = np.zeros((n, per, 2))
    drop = (curl * L)[:, None] * (t ** 2)[None, :]
    mid = leaves.base[:, None, :] + (L[:, None] * t[None, :])[..., None] * a[:, None, :] - drop[..., None] * nrm[:, None, :]
    V[:, 0] = mid[:, 0]
    V[:, -1] = mid[:, -1]
    UV[:, 0] = [0.5, 1.0]
    UV[:, -1] = [0.5, 0.0]
    for r in range(1, rows):
        o = 1 + 3 * (r - 1)
        side = (Wh * half[r])[:, None]
        V[:, o] = mid[:, r]
        V[:, o + 1] = mid[:, r] + c * side * np.cos(fold) - nrm * side * np.sin(fold)
        V[:, o + 2] = mid[:, r] - c * side * np.cos(fold) - nrm * side * np.sin(fold)
        UV[:, o] = [0.5, 1.0 - t[r]]
        UV[:, o + 1] = [0.5 + 0.49 * half[r], 1.0 - t[r]]
        UV[:, o + 2] = [0.5 - 0.49 * half[r], 1.0 - t[r]]
    # faces, the leaf's upper side turned up
    tri = []
    tri += [[0, 3, 1], [0, 1, 2]]
    for r in range(1, inner):
        o = 1 + 3 * (r - 1)
        m0, p0, q0 = o, o + 1, o + 2
        m1, p1, q1 = o + 3, o + 4, o + 5
        tri += [[m0, q0, q1], [m0, q1, m1], [m0, m1, p1], [m0, p1, p0]]
    o = 1 + 3 * (inner - 1)
    tip = per - 1
    tri += [[o, o + 2, tip], [o, tip, o + 1]]
    tri = np.asarray(tri, np.int64)
    F = (np.arange(n)[:, None, None] * per + tri[None]).reshape(-1, 3)
    V = V.reshape(-1, 3)
    # the atlas column of the leaf's level
    levels = len(fractions)
    level = np.clip(np.round((chl - fractions[0]) / max(fractions[-1] - fractions[0], 1e-6) * (levels - 1)), 0, levels - 1)
    UV = UV.reshape(-1, 2)
    UV[:, 0] = (np.repeat(level, per) + UV[:, 0]) / levels
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return {"V": V, "N": N, "F": F, "UV": UV, "T": game._tangents(V, N, UV, F), "per": per, "level": level}


def card_atlas(look: dict, seed: int) -> dict:
    """Leaf cards at a few chlorophyll levels, in columns of the same sprays, cut-away texels refilled."""
    u = look["game"]["unreal"]
    levels = int(u["card_levels"])
    fractions = np.linspace(float(u["leaf_level_range"][0]), float(u["leaf_level_range"][1]), levels)
    R, _ = ap.leaf_colours(look, fractions)
    clip = float(u["alpha_clip"])
    n = int(look["game"]["leaf_card"]["texture_px"])
    rgb = np.zeros((n, n * levels, 3), np.float32)
    alpha = np.zeros((n, n * levels), np.float32)
    nrm = np.zeros((n, n * levels, 3), np.float32)
    nrm[..., 2] = 1.0
    coverage = None
    grid = 1
    for i, f in enumerate(fractions):
        blade = tx.leaf_blade(look, seed, game._turning(float(f), look["leaves"]["interveinal_lead"]))
        a = blade["alpha"]
        mean = np.maximum((blade["rgb"] * a[..., None]).reshape(-1, 3).sum(0) / max(float(a.sum()), 1.0), 1e-4)
        blade = dict(blade, rgb=np.clip(blade["rgb"] * (R[i] / mean).astype(np.float32), 0.0, 1.0))
        sheet = tx.leaf_card_atlas(look, blade, seed + 200)
        solid = (sheet["alpha"] >= clip).astype(np.float32)
        rgb[:, i * n:(i + 1) * n] = tx.push_pull_fill(sheet["rgb"], solid)
        alpha[:, i * n:(i + 1) * n] = sheet["alpha"]
        grid = sheet["grid"]
        cell = n // grid
        coverage = [float(solid[y * cell:(y + 1) * cell, x * cell:(x + 1) * cell].mean()) for y in range(grid) for x in range(grid)]
    return {"rgb": rgb, "alpha": alpha, "normal": nrm, "rough": np.full(alpha.shape, 0.5, np.float32), "grid": grid, "coverage": coverage, "fractions": fractions}


def card_mesh(look: dict, leaves: ap.LeafInstances, chl: np.ndarray, flex: np.ndarray, phase: float, atlas: dict, target: int, centre: np.ndarray) -> dict | None:
    """Alpha cards standing for the leaves (game.leaf_cards), with each card's chlorophyll level in its
    UV and its season and wind data in the channels."""
    if len(leaves.node) == 0 or target < 1:
        return None
    ll = {"tint": np.ones((len(leaves.node), 3))}
    a = game.leaf_cards(look, leaves, ll, target, atlas["coverage"], atlas["grid"], centre, return_groups=True)
    inv, m = a["groups"], a["count"]
    w = leaves.area
    total = np.bincount(inv, w, m)

    def mean(x):
        return np.bincount(inv, x * w, m) / np.maximum(total, 1e-12)

    fractions = atlas["fractions"]
    levels = len(fractions)
    level = np.clip(np.round((mean(chl) - fractions[0]) / max(fractions[-1] - fractions[0], 1e-6) * (levels - 1)), 0, levels - 1)
    a["UV"] = np.stack([(np.repeat(level, 4) + a["UV"][:, 0]) / levels, a["UV"][:, 1]], 1)
    per_card = {"uv2": np.stack([mean(leaves.delay), mean(leaves.sun)], 1), "uv3": np.stack([mean(chl), total * 1e4], 1), "flex": mean(flex[leaves.node])}
    a["uv2"] = np.repeat(per_card["uv2"], 4, axis=0)
    a["uv3"] = np.repeat(per_card["uv3"], 4, axis=0)
    a["colour"] = _colour0(np.repeat(per_card["flex"], 4), phase, 1.0, np.repeat(ap.hash01(np.arange(m), 51) * 254.0 / 255.0, 4))
    return a


# -- bark strips ------------------------------------------------------------------------------------
def strip_atlas(look: dict, seed: int) -> dict:
    """The strips at each opacity level, in columns: alpha lowered so more of the holes open at the
    game's clip."""
    u = look["game"]["unreal"]
    cfg = look["bark"]["peel"]
    levels = int(u["strip_opacity_levels"])
    tex = tx.strip_texture(look, seed)
    H, W = tex["alpha"].shape
    ops = np.linspace(float(cfg["opacity_young"]), float(cfg["opacity_old"]), levels)
    rgb = np.zeros((H, W * levels, 3), np.float32)
    alpha = np.zeros((H, W * levels), np.float32)
    clip = float(u["alpha_clip"])
    solid = (tex["alpha"] >= 0.5).astype(np.float32)
    colour = tx.push_pull_fill(tex["rgb"], solid)
    for i, op in enumerate(ops):
        rgb[:, i * W:(i + 1) * W] = colour
        # the plain export's test was alpha x opacity >= 0.5
        alpha[:, i * W:(i + 1) * W] = np.clip(tex["alpha"] * op * clip / 0.5, 0.0, 1.0)
    return {"rgb": rgb, "alpha": alpha, "normal": np.dstack([np.zeros_like(alpha), np.zeros_like(alpha), np.ones_like(alpha)]), "rough": np.full(alpha.shape, 0.7, np.float32), "ops": ops}


# -- one age --------------------------------------------------------------------------------------------
def pot(a: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resampled to these sizes, a channel at a time."""
    from PIL import Image

    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((width, height), Image.BILINEAR), np.float32)
    return np.stack([pot(a[..., k], width, height) for k in range(a.shape[-1])], -1)


def next_pot(n: int) -> int:
    return 1 << int(np.ceil(np.log2(max(n, 1))))


def trunk_entry(stem: dict) -> dict:
    """Where the trunk meets the ground, as the game's measure_trunks.py finds it: its axis 0.2-0.9 m
    up, its radius 1.0-1.6 m up.  Metres to cm, in the model's frame, as trunks.json has them."""
    V = stem["V"]
    band = V[(V[:, 2] > 0.2) & (V[:, 2] < 0.9)]
    if len(band) < 3:
        band = V[V[:, 2] < 0.5 * V[:, 2].max()]
    centre = band[:, :2].mean(0)
    ring = V[(V[:, 2] > 1.0) & (V[:, 2] < 1.6)]
    if len(ring) < 3:
        ring = band
    r = float(np.percentile(np.linalg.norm(ring[:, :2] - centre, axis=1), 40))
    return {"trunk_x_cm": round(float(centre[0]) * 100, 1), "trunk_y_cm": round(float(centre[1]) * 100, 1), "trunk_r_cm": round(r * 100, 1)}


def bounds_entry(arrays: list) -> dict:
    """The sizes the game's manifest and flora.json hold for a variant (cm)."""
    V = np.concatenate(arrays)
    lo, hi = V.min(0), V.max(0)
    return {"height_cm": round(float(hi[2] - lo[2]) * 100, 1), "width_cm": round(float(max(hi[0] - lo[0], hi[1] - lo[1])) * 100, 1), "min_z_cm": round(float(lo[2]) * 100, 1),
            "center_x_cm": round(float(0.5 * (lo[0] + hi[0])) * 100, 1), "center_y_cm": round(float(-0.5 * (lo[1] + hi[1])) * 100, 1)}


def write_fragments(out: Path, asset: str, stages: list, surface_depth_m: float = 0.1) -> dict:
    """What a game script would fold into its own files, in those files' formats.  Nothing in the game
    is written.  ``sink_m``: the game seats a tree by its lowest point, which is this far below its
    ground line, so a rule with this sink puts the ground on that line."""
    trunks, variants = {}, []
    for st in stages:
        for season, files in st["seasons"].items():
            near = next(iter(files.values()))
            trunks[near["variant"]] = near["trunk"]
            variants.append({"id": near["variant"], "mesh": near["variant"], "height_m": round(near["bounds"]["height_cm"] / 100.0, 3), "width_m": round(near["bounds"]["width_cm"] / 100.0, 3)})
    (out / "fragments").mkdir(parents=True, exist_ok=True)
    (out / "fragments" / "trunks.json").write_text(json.dumps(trunks, indent=1), encoding="utf-8")
    (out / "fragments" / "flora_variants.json").write_text(json.dumps(variants, indent=1), encoding="utf-8")
    (out / "fragments" / "flora_rule.json").write_text(json.dumps({"sink_m": surface_depth_m}, indent=1), encoding="utf-8")
    return {"trunks": trunks, "variants": variants, "sink_m": surface_depth_m}


def export_stage(ctx: dict, age: int, seasons: list, log=print) -> dict:
    """All levels of one age, each season.  ``ctx`` from tools/game_export.py: look, model, sp, snaps,
    tiles, out, asset, meta and cli helpers already applied (skel, radii)."""
    look, model, sp, out, asset, meta, tiles = ctx["look"], ctx["model"], ctx["sp"], ctx["out"], ctx["asset"], ctx["meta"], ctx["tiles"]
    u = look["game"]["unreal"]
    T = model.tree
    st = model.stats[age]
    height, dbh_w = float(st["height_m"]), st["dbh_cm"]
    skel, rad, is_root, orig, pos, r_wood = ctx["skeleton"](model, age)
    n = skel.n
    part_age = age - np.asarray(skel.birth[:n], float)
    z = np.asarray(skel.pos[:n, 2], float)
    rad_ob = ap.add_bark_radius(look, np.asarray(rad[:n], float).copy(), part_age, z, np.asarray(is_root[:n]), height, dbh_w)
    root_cfg = u["roots"]
    line = ground_line(model, age, root_cfg)
    rad_ob = root_radii(look, model, age, rad_ob, skel, is_root, line, root_cfg, ap.over_bark_dbh_cm(look, dbh_w))
    gfull = look["game"]["full_mesh"]
    clean = {k: u[k] for k in ("ring_tolerance", "ring_tolerance_m", "ring_longest_span")}
    clean["drop_hidden_rings"] = float(u["ring_tolerance"]) > 0.0 or float(u["ring_tolerance_m"]) > 0.0
    settings0 = meshlib.MeshSettings(ring_attributes=True, stem_sides_by_radius=True, sides_allowed=tuple(gfull["sides_allowed"]), **clean)
    crown0, roots0 = tree_meshes(skel, np.ones(n, bool), rad_ob, is_root, orig, sp.geometry, settings0)
    wood = game.WoodParts(look, tiles, age, height, dbh_w, T.birth[: T.n], r_wood)
    game.bake_wood(wood, crown0, T, pos, model.radius_history)
    arrays0 = game.wood_arrays(wood, crown0, relief=True)
    wood.first_stem_node = int(arrays0["stem"]["node"][np.argmin(arrays0["stem"]["V"][:, 2])])
    alive = (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age))
    flex = wind_flex(pos, np.asarray(T.parent[: T.n]), alive, np.asarray(T.depth[: T.n]))
    phase = float(ap.hash01(np.array([int(ctx["seed"])]), 71)[0])
    seed = int(look["game"]["texture_seed"])
    tile_m = float(u["bark_wrap_tile_m"])
    lods = {lod["name"]: lod for lod in look["game"]["lods"]}
    lod1 = next((v for v in lods.values() if v["kind"] == "reduced"), None)
    arrays1 = None
    roots1 = None
    if lod1 is not None and lod1.get("budget") is not None:
        rm = look["game"]["reduced_mesh"]
        settings1 = meshlib.MeshSettings(edge_target=rm["edge_target"], sides_allowed=tuple(rm["sides_allowed"]), ring_spacing_factor=rm["ring_spacing_factor"],
                                         min_ring_spacing=rm["min_ring_spacing"], max_ring_spacing=rm["max_ring_spacing"], max_turn_deg=rm["max_turn_deg"],
                                         ring_attributes=True, stem_sides_by_radius=True, **clean)
        thr = game.reduced_radius_threshold(skel, rad_ob, is_root, orig, sp.geometry, settings1, int(float(lod1["budget"]) * float(lod1["wood_share"])))
        crown1, roots1 = tree_meshes(skel, game.reduced_selection(skel, rad_ob, thr), rad_ob, is_root, orig, sp.geometry, settings1)
        arrays1 = game.wood_arrays(wood, crown1)
    base_name = f"{asset}_age{age:03d}"
    maps = Maps(out, asset)
    split = out / "SourceArt" / "PolyHaven_split" / asset
    split.mkdir(parents=True, exist_ok=True)
    # bark maps, once per age
    stem_slot, branch_slot, strip_slot = f"{base_name}_stem_bark", f"{base_name}_branch_bark", f"{base_name}_bark_strip"
    stem_files = _bark_maps(maps, stem_slot, wood.stem_bake)
    branch_files = _bark_maps(maps, branch_slot, wood.atlas)
    stem_circ = 2.0 * np.pi * float(wood.profile.radius[0])
    turns = float(max(round(stem_circ / tile_m), 1))
    # roots: their own tree's ids, so their own birth years and radii
    root_birth = np.asarray(model.roots.tree.birth)
    root_radius = np.asarray(model.roots.radius_history[age], float)
    root_slot = f"{base_name}_root_bark"
    root_bake = root_atlas(look, wood, tiles, roots0, root_birth, root_radius, root_cfg)
    root_files = _bark_maps(maps, root_slot, root_bake)
    foot0, surface0, below0 = split_roots(roots0, root_cfg, line)
    foot1, surface1, below1 = split_roots(roots1, root_cfg, line)
    stem_node = int(wood.first_stem_node)
    foot_a = {"full": foot_arrays(look, wood, foot0, stem_node), "reduced": foot_arrays(look, wood, foot1, stem_node)}
    surface_a = {"full": root_arrays(look, wood, surface0, root_bake, root_birth, root_radius), "reduced": root_arrays(look, wood, surface1, root_bake, root_birth, root_radius)}
    root_files_out = {}
    for lname, below_md in (("lod0", below0), ("lod1", below1)):
        arr = root_arrays(look, wood, below_md, root_bake, root_birth, root_radius)
        if arr is None:
            continue
        rname = f"{base_name}_roots" + ("" if lname == "lod0" else f"_{lname}")
        rpath = split / f"{rname}.gltf"
        rglb = GameGLB(rpath, rname, {**meta, "age": age, "level": lname, "part": "everything below ground", "color0": COLOR0, "uv_layout": UV_LAYOUT})
        _root_mesh(rglb, wood, arr, "roots_below_ground", maps.material(rglb, root_slot, root_files, CLAMP, REPEAT), root_birth, root_radius, phase, tile_m)
        info = rglb.write_gltf()
        info.update(file=str(rpath.relative_to(out)).replace("\\", "/"), variant=rname, min_z_m=round(float(arr["V"][:, 2].min()), 3))
        root_files_out[lname] = info
    # leaves
    blade0 = tx.leaf_blade(look, seed + 500)
    leaves = ap.leaf_instances(look, sp, ctx["snaps"][age], pos, r_wood, age, blade0["fill"])
    atlas = leaf_atlas(look, seed + 500)
    leaf_slot = f"{base_name}_leaf"
    leaf_files = maps.write(leaf_slot, atlas["rgb"], atlas["normal"], atlas["rough"], alpha=np.ones(atlas["rough"].shape, np.float32))
    strips = ap.peel_strips(look, pos, T.parent[: T.n], r_wood, T.birth[: T.n], alive, age, height, ap.over_bark_dbh_cm(look, dbh_w))
    strip_tex = strip_atlas(look, seed + 600)
    strip_files = maps.write(strip_slot, strip_tex["rgb"], strip_tex["normal"], strip_tex["rough"], alpha=strip_tex["alpha"])
    cards = card_atlas(look, seed + 700) if lod1 is not None else None
    card_slot = f"{base_name}_card_leaf"
    card_files = maps.write(card_slot, cards["rgb"], cards["normal"], cards["rough"], alpha=cards["alpha"]) if cards is not None else None
    days = look["leaves"]["season"]["days"]
    out_stage = {"age": age, "height_m": height, "dbh_wood_cm": dbh_w, "dbh_over_bark_cm": round(ap.over_bark_dbh_cm(look, dbh_w), 2), "exported_leaves": int(len(leaves.node)),
                 "roots": {**root_table(model, age), "ground_line_m": round(line, 3), "thick_root_breaking_ground": thick_breaking(model, age, line), "files": root_files_out}, "upper_bark": black_zone(wood),
                 "model_leaf_area_m2": st["leaf_area_m2"], "exported_leaf_area_m2": round(float(leaves.area.sum()), 3), "peel_strips": 0 if strips is None else strips.count,
                 "bark_texture_y": _texture_y(wood), "stem_height_range_m": stem_files["height_range_m"], "seasons": {}}
    for season in seasons:
        suffix = "" if season == look["game"]["unreal"]["base_season"] else f"_{season}"
        files = {}
        chl = None if season == "winter" else ap.chlorophyll_at(look, float(days[season]), leaves.sun, leaves.delay)
        for lname, lod in lods.items():
            variant = base_name + suffix + ("" if lod["kind"] == "full" else f"_{lname}")
            path = split / f"{variant}.gltf"
            lmeta = {**meta, "age": age, "season": season, "level": lname, "color0": COLOR0, "uv_layout": UV_LAYOUT}
            glb = GameGLB(path, variant, lmeta)
            parts = {}
            if lod["kind"] == "far":
                near = split / f"{base_name}{suffix}.gltf"
                f = game.far_sheets(near, lod)
                H = f["albedo"].shape[0]
                W = next_pot(f["albedo"].shape[1])
                cov = pot(f["coverage"], W, H)
                nrm = pot(f["normal"], W, H)
                nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
                colour = tx.push_pull_fill(pot(f["albedo"], W, H), (cov > 0.05).astype(np.float32))
                far_slot = f"{variant}_leaf"
                far_files = maps.write(far_slot, colour, nrm, np.full(cov.shape, 0.8, np.float32), alpha=cov)
                m = maps.material(glb, far_slot, far_files, CLAMP, CLAMP, alpha_clip=float(u["alpha_clip"]))
                far_z = np.clip(f["V"][:, 2] / max(f["V"][:, 2].max(), 1e-6), 0.0, 1.0)
                glb.add_mesh("far_cards", m, f["V"], f["N"], f["F"], f["UV"], f["T"], colour=_colour0(far_z ** 2, phase, 0.0, np.ones(len(f["V"]))), colour_8bit=True)
                parts["far_cards"] = glb.triangles
            else:
                arrays = arrays0 if lod["kind"] == "full" else arrays1
                if "stem" in arrays:
                    m = maps.material(glb, stem_slot, stem_files, REPEAT, CLAMP)
                    _bark_mesh(glb, wood, arrays["stem"], "stem", m, flex, phase, turns, tile_m)
                    if foot_a[lod["kind"]] is not None:
                        _bark_mesh(glb, wood, foot_a[lod["kind"]], "stem_foot", m, flex, phase, turns, tile_m)
                if "branch" in arrays:
                    m = maps.material(glb, branch_slot, branch_files, CLAMP, REPEAT)
                    _bark_mesh(glb, wood, arrays["branch"], "branches", m, flex, phase, _column_turns(look, arrays["branch"]["col"], tile_m), tile_m)
                parts["wood"] = glb.triangles
                surface = surface_a[lod["kind"]]
                if surface is not None:
                    _root_mesh(glb, wood, surface, "surface_roots", maps.material(glb, root_slot, root_files, CLAMP, REPEAT), root_birth, root_radius, phase, tile_m)
                    parts["surface_roots"] = glb.triangles - parts["wood"]
                if lod.get("peel_strips") and strips is not None:
                    tri0 = glb.triangles
                    m = maps.material(glb, strip_slot, strip_files, CLAMP, CLAMP, alpha_clip=float(u["alpha_clip"]))
                    uv = strips.uv.copy()
                    level = np.round((float(look["bark"]["peel"]["opacity_young"]) - strips.opacity) / max(float(look["bark"]["peel"]["opacity_young"]) - float(look["bark"]["peel"]["opacity_old"]), 1e-6) * (len(strip_tex["ops"]) - 1))
                    uv[:, 0] = (level + uv[:, 0]) / len(strip_tex["ops"])
                    uv2 = np.stack([T.birth[strips.node].astype(np.float64), r_wood[strips.node] * 100.0], 1)
                    uv3 = np.stack([strips.opacity, np.zeros(len(strips.opacity))], 1)
                    glb.add_mesh("bark_strips", m, strips.vertices, strips.normals, strips.faces, uv, game._tangents(strips.vertices, strips.normals, uv, strips.faces),
                                 colour=_colour0(flex[strips.node], phase, 0.0, np.ones(len(strips.node))), colour_8bit=True, extra_uv=[_node_uv(strips.node), uv2, uv3], attributes={"NODE_ID": strips.node})
                    parts["bark_strips"] = glb.triangles - tri0
                if chl is not None and len(leaves.node):
                    tri0 = glb.triangles
                    if lod["leaf_kind"] == "blades":
                        m = maps.material(glb, leaf_slot, leaf_files, CLAMP, CLAMP, two_sided=True, extras=_leaf_extras(look, float(np.mean(chl))))
                        b = blade_mesh(look, leaves, chl, atlas["fractions"])
                        per = b["per"]
                        node = np.repeat(leaves.node, per)
                        uv2 = np.stack([np.repeat(leaves.delay, per), np.repeat(leaves.sun, per)], 1)
                        uv3 = np.stack([np.repeat(chl, per), np.repeat(leaves.area * 1e4, per)], 1)
                        leaf_id = np.repeat(ap.hash01(np.arange(len(leaves.node)), 52) * 254.0 / 255.0, per)
                        colour = _colour0(flex[node], phase, 1.0, leaf_id)
                        glb.add_mesh("leaves", m, b["V"], b["N"], b["F"], b["UV"], b["T"], colour=colour, colour_8bit=True, extra_uv=[_node_uv(node), uv2, uv3],
                                     attributes={"NODE_ID": node, "LEAF_SUN": uv2[:, 1], "LEAF_TURN": uv2[:, 0]})
                    else:
                        target = max((int(lod["budget"]) - glb.triangles) // 2, 1)
                        a = card_mesh(look, leaves, chl, flex, phase, cards, target, np.array([0.0, 0.0, 0.62 * height]))
                        if a is not None:
                            m = maps.material(glb, card_slot, card_files, CLAMP, CLAMP, alpha_clip=float(u["alpha_clip"]), two_sided=True, extras=_leaf_extras(look, float(np.mean(chl))))
                            glb.add_mesh("leaf_cards", m, a["V"], a["N"], a["F"], a["UV"], a["T"], colour=a["colour"], colour_8bit=True, extra_uv=[np.zeros((len(a["V"]), 2)), a["uv2"], a["uv3"]])
                            parts["leaf_area_represented_m2"] = round(a["represented_area"], 3)
                    parts["leaves"] = glb.triangles - tri0
            all_v = [np.asarray(m_) for m_ in _positions(glb)]
            info = glb.write_gltf()
            bud = lod.get("budget")
            info.update(parts=parts, budget=bud, within_budget=bud is None or info["triangles"] <= int(bud), variant=variant, file=str(path.relative_to(out)).replace("\\", "/"))
            if lod["kind"] == "full":
                info["bounds"] = bounds_entry([np.stack([a_[:, 0], -a_[:, 2], a_[:, 1]], 1) for a_ in all_v])
                info["trunk"] = trunk_entry(arrays0["stem"])
            files[lname] = info
        out_stage["seasons"][season] = files
        log(f"age {age} {season}: " + ", ".join(f"{k} {v['triangles']}" for k, v in files.items()))
    return out_stage


def _positions(glb: GameGLB) -> list:
    """Every mesh's vertices back out of the writer (y-up, as the file has them)."""
    out = []
    for mesh in glb.meshes:
        acc = glb.accessors[mesh["primitives"][0]["attributes"]["POSITION"]]
        view = glb.views[acc["bufferView"]]
        out.append(np.frombuffer(glb.blob, "<f4", acc["count"] * 3, view["byteOffset"]).reshape(-1, 3))
    return out


def _texture_y(wood: game.WoodParts) -> dict:
    """Mean linear luminance of the bark's colour maps, overall and in the lowest and upper stem."""
    y = np.array([0.2126, 0.7152, 0.0722], np.float32)
    a = wood.stem_bake["albedo"] @ y
    n = a.shape[0]
    return {"stem_all": round(float(a.mean()), 3), "stem_lowest_fifth_of_rows": round(float(a[: n // 5].mean()), 3), "stem_top_half_of_rows": round(float(a[n // 2:].mean()), 3),
            "branch_atlas": round(float((wood.atlas["albedo"] @ y).mean()), 3)}


def _leaf_extras(look: dict, chl: float) -> dict:
    """Measured light through the leaf, which the import drops as an extension: kept for a material to read."""
    R, T = ap.leaf_colours(look, np.array([chl]))
    return {"measured_reflectance_linear": [round(float(x), 4) for x in R[0]], "measured_transmittance_linear": [round(float(x), 4) for x in T[0]]}
