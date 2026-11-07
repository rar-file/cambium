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
  Nanite's limit.  Which channel holds what: ``UV_LAYOUT``, and docs/unreal.md;
* the file's origin far enough below the tree's lowest point that M_Surface's ground moss, which it
  reads by height above the origin and which smears up an upright surface, stays off: the moss is in
  our own stem map instead, and the game's seat by the lowest point is as right as ever;
* on the nearest level, the bark's height map in the stem's mesh, by the same ageing rules as its
  colour, and each leaf's real outline, from ``appearance.game.unreal.leaf``.

Colour that the plain export gave per vertex now lives in textures, so an unmodified M_Surface and
M_Foliage show it: a leaf's UV picks the column of its chlorophyll level in a leaf atlas.

Reads only; nothing goes back into growth, and the plain export is untouched.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

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
    "leaf": {"UV0": "leaf atlas: the column is the leaf's chlorophyll level on the export's day, the row its outline variant, the rest of the cell the blade; the cell's corner holds the stalk's colour",
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
    out["leaves"]["shape"] = u["leaf"]["shape"]
    out["leaves"]["texture_size_px"] = int(u["leaf"]["texture_px"])
    # the rough base's top, uneven
    if out["bark"].get("uneven_top"):
        out["bark"]["uneven_top"] = {**out["bark"]["uneven_top"], "strength": float(u["stem_relief"]["uneven_top"])}
    # each leaf where its shoot has it
    out["leaves"]["on_shoots"] = {**out["leaves"]["on_shoots"], "strength": float(u["leaf"]["on_shoots"])}
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


def _paid(model) -> bool:
    return bool(getattr(getattr(model.sp.roots, "paid", None), "enabled", False))


def collar_radius(model, age: int) -> float:
    """The radius the foot's rules go by.  With roots.paid the root collar is the real stump, wider than the stem
    at z = 0 as the stem's own butt swell isn't in its wood radius: the stem's is what the look was tuned on."""
    if _paid(model):
        return float(np.asarray(model.radius_history[age], float)[0])
    return float(np.asarray(model.roots.radius_history[age], float).max())


def foot_settings(model, cfg: dict) -> dict:
    """The roots' look, with what roots.paid changes: only its thick roots show, they sink slowly along their
    length, and a root never comes back up once it's going under."""
    if not _paid(model):
        return cfg
    out = dict(cfg)
    out["surface_min_radius_share"] = cfg["paid_surface_min_radius_share"]
    out["sink_length_radii"] = cfg["paid_sink_length_radii"]
    out["bury_per_sink_length"] = cfg["paid_bury_per_sink_length"]
    out["ground_line_radii"] = cfg["paid_ground_line_radii"]
    out["never_rises"] = True
    return out


def ground_line(model, age: int, cfg: dict) -> float:
    """Where the game's ground should meet the tree, in the model's frame: below its z = 0 by a share of
    the root collar's radius, so the model's own thick roots break it.  Its z = 0 itself has almost none
    above it (``root_table``)."""
    collar = collar_radius(model, age)
    return -min(float(cfg["ground_line_max_m"]), float(cfg["ground_line_radii"]) * collar)


def flow_shape(r: float, foot_r: float, cfg: dict) -> tuple:
    """A swell for a root of radius ``r`` at the stem: how far out (m), half width (rad), how far up above
    the root's crest (m), and the root's crest over the ground (m).  Its ridge comes down the stem and
    lands on that crest at the swell's end, over the root, which stays low and comes out from under it."""
    out = min(float(cfg["flow_out_radii"]) * r, float(cfg["flow_max_share"]) * foot_r)
    return out, min(float(cfg["flow_width_radii"]) * r / foot_r, 0.9), float(cfg["flow_up_radii"]) * r, root_crest(r, out / max(r, 1e-6), cfg)


def root_crest(r, along_radii, cfg: dict):
    """How far a root's top stands over the ground, ``along_radii`` of its first radius out from the stem:
    it sinks along all it shows, a little faster as it goes, and is gone by ``visible_radii``."""
    g = np.clip(np.asarray(along_radii, float) / float(cfg["visible_radii"]), 0.0, 1.0)
    return (1.0 + float(cfg["centre_above_ground_radii"])) * r * (1.0 - g ** float(cfg["sink_power"]))


def _goes_under(placed: np.ndarray, rc: np.ndarray, rho: np.ndarray, along: np.ndarray, foot_r: float, thr: float, line: float, cfg: dict) -> np.ndarray:
    """One root's ring heights, so that it's under the soil before it's thin, and goes there as a real
    one does: lying part buried, and sinking along all it shows.  A tube that keeps its thickness cuts a
    level plane in a long rounded tongue; it's a thin one tapering as it crosses that draws a spike."""
    outside = rho >= foot_r
    if not outside.any():
        return placed
    i0 = int(np.argmax(outside))
    t = along - along[i0]
    r0 = float(rc[i0])
    # it may have to be gone sooner than its thickness says, if it thins too fast
    thin = (t > 0.0) & (rc < float(cfg["under_share"]) * thr)
    run = float(t[int(np.argmax(thin))]) if thin.any() else float(cfg["visible_radii"]) * r0
    run = min(run, float(cfg["visible_radii"]) * r0)
    crest = root_crest(rc, t / max(run, 1e-6) * float(cfg["visible_radii"]), cfg)
    limit = np.where(t >= run, line - rc - 0.025, line - rc + crest)
    return np.where(t >= 0.0, np.minimum(placed, limit), placed)


def sink_roots(md: meshlib.MeshData | None, line: float, centre: np.ndarray, foot_r: float, collar: float, cfg: dict) -> meshlib.MeshData | None:
    """The ground meets the tree below the model's zero at the stem, and at it further out: so a root's
    place in the soil holds out there, and it comes out of the foot and sinks along its length.  Each
    root keeps its path as seen from above, its radius and its branches; only its height moves, ring by
    ring so its section stays round: none stands off the ground as a strut, a thick root lies half
    buried, and by the time it's thin it is under the soil, where the model has its thin ends."""
    if md is None:
        return None
    V = md.vertices.copy()
    root = md.attributes["axis_id"] != 0
    if not root.any():
        return md
    # one entry per ring: its centre and its radius
    ring = np.stack([md.attributes["axis_id"][root].astype(np.int64), np.round(md.attributes["ring_along"][root] * 1.0e5).astype(np.int64)], 1)
    rings, inv = np.unique(ring, axis=0, return_inverse=True)
    inv = np.ravel(inv)
    count = np.bincount(inv).astype(float)
    centre_of = lambda values: np.bincount(inv, values) / count  # noqa: E731
    zc = centre_of(V[root, 2])
    rc = centre_of(md.attributes["radius"][root])
    rho = np.hypot(centre_of(V[root, 0]) - centre[0], centre_of(V[root, 1]) - centre[1])
    L = max(float(cfg["sink_length_radii"]) * collar, 1e-3)
    sunk = zc + line * (1.0 - np.exp(-np.maximum(rho - foot_r, 0.0) / L))
    # fully thick: this share of a radius above the ground; at half the thickness that goes on showing: under it
    thr = max(float(cfg["surface_min_radius_m"]), float(cfg["surface_min_radius_share"]) * collar)
    s = np.clip((rc / thr - 0.5) / 0.5, 0.0, 1.0)
    s = s * s * (3.0 - 2.0 * s)
    above = float(cfg["centre_above_ground_radii"]) - float(cfg.get("bury_per_sink_length", 0.0)) * np.maximum(rho - foot_r, 0.0) / L
    highest = line + s * above * rc - (1.0 - s) * (rc + 0.01)
    placed = np.minimum(sunk, highest)
    # rings come out of np.unique by axis, then along it
    first = np.unique(rings[:, 0], return_index=True)[1]
    ends = np.r_[first[1:], len(placed)]
    along = rings[:, 1] / 1.0e5
    for a, b in zip(first.tolist(), ends.tolist()):
        if rc[a:b].max() >= thr:
            placed[a:b] = _goes_under(placed[a:b], rc[a:b], rho[a:b], along[a:b], foot_r, thr, line, cfg)
    if cfg.get("never_rises"):
        # a root that shows goes down along its length, none of its rings higher than the one before; once it's
        # under, it keeps the model's path and stays under
        for a, b in zip(first.tolist(), ends.tolist()):
            if rc[a:b].max() < thr:
                continue
            run = np.minimum.accumulate(placed[a:b])
            under = line - rc[a:b] - 0.02
            gone = np.nonzero(run < under)[0]
            i = int(gone[0]) if gone.size else b - a
            placed[a:a + i] = run[:i]
            placed[a + i:b] = np.minimum(placed[a + i:b], under[i:])
    V[root, 2] += (placed - zc)[inv]
    return meshlib.MeshData(V, md.faces, md.normals, md.attributes)


def root_flows(surface: meshlib.MeshData | None, centre: np.ndarray, foot_r: float, cfg: dict) -> np.ndarray:
    """A swell on the stem for each thick root that leaves its foot, so the stem's surface runs out along
    the root and lands on it, and the two are one shape, with no line where they meet (``flow_shape``).
    Rows: direction (rad), how far out at the ground (m), half width (rad), how
    above it (m), the root's crest over the ground (m).  It's the stem's surface that moves: the root
    keeps its path and its radius."""
    if surface is None:
        return np.zeros((0, 5))
    axis = surface.attributes["axis_id"]
    along = np.round(surface.attributes["ring_along"] * 1.0e5).astype(np.int64)
    exits = []
    for a in np.unique(axis):
        sel = axis == a
        keys, inv = np.unique(along[sel], return_inverse=True)
        inv = np.ravel(inv)
        count = np.bincount(inv).astype(float)
        cx = np.bincount(inv, surface.vertices[sel, 0]) / count - centre[0]
        cy = np.bincount(inv, surface.vertices[sel, 1]) / count - centre[1]
        rho = np.hypot(cx, cy)
        # a branch further out along a root isn't at the stem
        if rho.min() > 1.6 * foot_r or not (rho >= foot_r).any():
            continue
        i = int(np.argmax(rho >= foot_r))
        exits.append((float(np.arctan2(cy[i], cx[i])), float(np.bincount(inv, surface.attributes["radius"][sel])[i] / count[i])))
    if not exits:
        return np.zeros((0, 5))
    biggest = max(r for _, r in exits)
    rows = []
    for az, r in exits:
        if r < float(cfg["flow_min_share"]) * biggest:
            continue
        rows.append((az, *flow_shape(r, foot_r, cfg)))
    return np.array(rows, float).reshape(-1, 5)


def flow_offset(theta: np.ndarray, above: np.ndarray, flows: np.ndarray) -> np.ndarray:
    """How far the stem's surface moves out, at these directions and heights above the ground line: the
    ridge comes down the stem, ever flatter, and lands on the root's crest at ``out``, over the root,
    which comes out from under it there; lower down the flanks spread on to the ground, so there's no
    upright lip.  A swell doesn't pile on its neighbour."""
    total = np.zeros_like(theta)
    for az, out_m, width, up_m, crest in flows:
        d = (theta - az + np.pi) % (2.0 * np.pi) - np.pi
        rise = _swell_rise(above, up_m, crest, out_m)
        total = total + (out_m * np.exp(-0.5 * (d / width) ** 2) * rise) ** 4
    return total ** 0.25


def _swell_rise(above: np.ndarray, up_m: float, crest: float, out_m: float) -> np.ndarray:
    """A swell's reach by height, as a share of how far it goes at the root's crest.  Below the crest it
    slopes on to the ground, over twice the crest's height, whatever the size of the root: a thick root's
    swell ends in a slope, not a wall."""
    ridge = (1.0 - np.clip((above - crest) / max(up_m, 1e-6), 0.0, 1.0)) ** 2.2
    flank = 1.0 + (2.0 * crest / max(out_m, 1e-6)) * np.clip((crest - above) / max(crest, 1e-6), 0.0, 1.0)
    return ridge * flank


def split_roots(md: meshlib.MeshData | None, cfg: dict, line: float, collar: float) -> tuple:
    """The roots as three parts: the stem's foot and the thick roots, which go with the tree, down to a
    little below the ground line so uneven ground meets them without a gap, and everything else, which
    is under ground.  They share their rings' vertices, so no seam.  A thick root stays until it sinks;
    a root never thick stays in the last part, shallow or not: drawn, it'd be a hair on the soil.  The
    stem's foot takes whole rings, cut by each ring's mean height: below the cut the stem leans off along
    the taproot, its rings tilt, and one side of them can come up to the ground, as an open flap."""
    if md is None:
        return None, None, None
    z = md.vertices[md.faces][..., 2]
    radius = md.attributes["radius"][md.faces].mean(1)
    axis = md.attributes["axis_id"][md.faces[:, 0]]
    stem = axis == 0
    thr = max(float(cfg["surface_min_radius_m"]), float(cfg["surface_min_radius_share"]) * collar)
    near = z.min(1) >= line - float(cfg["surface_depth_m"])
    level = np.full(len(md.vertices), -np.inf)
    on_stem = md.attributes["axis_id"] == 0
    if on_stem.any():
        _, ring = np.unique(np.round(md.attributes["ring_along"][on_stem] * 1.0e5).astype(np.int64), return_inverse=True)
        ring = np.ravel(ring)
        level[on_stem] = (np.bincount(ring, md.vertices[on_stem, 2]) / np.bincount(ring))[ring]
    foot = near & stem & (level[md.faces].min(1) >= line - float(cfg["surface_depth_m"]))
    thick_axes = np.unique(axis[radius >= thr])
    surface = near & ~stem & np.isin(axis, thick_axes) & ((radius >= thr) | (z.max(1) > line - 0.01))
    return _face_subset(md, foot), _face_subset(md, surface), _face_subset(md, ~(foot | surface))


def stem_goes_down(skel, is_root: np.ndarray, line: float, cfg: dict):
    """The skeleton with the stem carried straight down to below the ground line.  In the model the
    stem runs on as the taproot, whose first half metre leans well out to one side.  That's buried
    in the model; with the ground lower, and the stem's thickness on it, it would be a great hoof."""
    from types import SimpleNamespace

    n = skel.n
    pos = np.array(skel.pos, float)
    root = np.asarray(is_root[:n], bool)
    axis0 = np.asarray(skel.axis[:n]) == 0
    stem = np.nonzero(axis0 & ~root)[0]
    chain = np.nonzero(axis0 & root)[0]
    if not len(stem) or not len(chain):
        return skel
    base = pos[stem[np.argmin(pos[stem, 2])], :2]
    start = line - float(cfg["surface_depth_m"])
    t = np.clip((start - pos[chain, 2]) / max(float(cfg["foot_fade_m"]), 1e-6), 0.0, 1.0)
    pos[chain, :2] = base + (pos[chain, :2] - base) * (t * t * (3.0 - 2.0 * t))[:, None]
    return SimpleNamespace(n=n, pos=pos, parent=skel.parent, axis=skel.axis, is_lateral=skel.is_lateral, order=skel.order, birth=skel.birth, death=skel.death, depth=skel.depth)


def as_stem(foot: meshlib.MeshData | None, stem_node: int) -> meshlib.MeshData | None:
    """The stem under the model's zero, as part of the stem: the node at its foot, for its age and size."""
    if foot is None:
        return None
    attrs = dict(foot.attributes)
    attrs["node_id"] = np.full(len(foot.vertices), stem_node, np.int32)
    return meshlib.MeshData(foot.vertices, foot.faces, foot.normals, attrs)


def stem_edges(wood: game.WoodParts, z_nodes: np.ndarray, age_nodes: np.ndarray, d_nodes: np.ndarray, line: float, surface_depth: float, cfg: dict, reach: float = 0.0) -> tuple:
    """How fine the stem's mesh must be at each height: by how deep the ageing rules make its cracks
    there.  Almost none on young white bark, finest on the old black base.  ``reach``: how far above its
    level the rough base's top gets, somewhere round the stem."""
    grid = np.arange(line - surface_depth, float(z_nodes.max()) + 0.25, 0.05)
    fissure = wood.state(np.interp(grid, z_nodes, age_nodes), np.interp(grid, z_nodes, d_nodes), grid - reach)["fissure_m"]
    t = np.clip(fissure / float(cfg["full_at_fissure_m"]), 0.0, 1.0)
    t = t * t * (3.0 - 2.0 * t)
    coarse, fine = float(cfg["edge_coarse_m"]), float(cfg["edge_fine_m"])
    edge = coarse + (fine - coarse) * t
    return ((float(grid[0]) - 0.06, coarse),) + tuple((float(a), float(b)) for a, b in zip(grid, edge))


def weld_normals(V: np.ndarray, F: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    """Vertex normals from the faces, the same for every vertex at one place, so a seam or a cut shades through."""
    q = np.round(V * 2.0e5).astype(np.int64)
    key = q[:, 0] * 73856093 ^ q[:, 1] * 19349663 ^ q[:, 2] * 83492791
    _, inv = np.unique(key, return_inverse=True)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    total = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(total, inv[F[:, k]], fn)
    N = total[inv]
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    return np.where(ln > 1e-14, N / np.maximum(ln, 1e-14), fallback)


def _bilinear(m: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Across the columns wrapping, up the rows clamped."""
    H, W = m.shape
    x = np.mod(u, 1.0) * W - 0.5
    y = np.clip(v * H - 0.5, 0.0, H - 1.0)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    x0, x1 = x0 % W, (x0 + 1) % W
    y1 = np.minimum(y0 + 1, H - 1)
    return (m[y0, x0] * (1 - fx) + m[y0, x1] * fx) * (1 - fy) + (m[y1, x0] * (1 - fx) + m[y1, x1] * fx) * fy


def shape_stem(a: dict, wood: game.WoodParts, line: float, floor: float, swell: tuple, table: tuple | None, cfg: dict, flows: np.ndarray | None = None, centre: np.ndarray | None = None) -> dict:
    """The stem's real surface: the butt swell into the ground, steepest at the ground as on a real
    butt, a swell for each root that leaves it (``root_flows``), and, on the nearest level, the bark's
    own height map in the mesh, so plates stand out of the outline and cracks hold shadow.  Depth is
    what the bake holds: what the ageing rules gave each height.  Nothing goes below ``floor``, since
    the game seats a tree by its lowest point."""
    V, N, UV, F = a["V"], a["N"], a["UV"], a["F"]
    extra, reach = swell
    above = np.maximum(V[:, 2] - line, 0.0) / max(reach, 1e-6)
    out = V + N * (a["radius"] * extra * np.exp(-2.0 * above))[:, None]
    on_swell = np.zeros(len(V))
    if flows is not None and len(flows):
        low = np.nonzero(out[:, 2] - line < float((flows[:, 3] + flows[:, 4]).max()))[0]
        dx, dy = out[low, 0] - centre[0], out[low, 1] - centre[1]
        rho = np.maximum(np.hypot(dx, dy), 1e-6)
        push = flow_offset(np.arctan2(dy, dx), out[low, 2] - line, flows)
        out[low, 0] += push * dx / rho
        out[low, 1] += push * dy / rho
        on_swell[low] = np.clip(push / (0.5 * float(flows[:, 1].max())), 0.0, 1.0)
        # the bark's relief stands out from the surface as it now is
        N = weld_normals(out, F, N)
    if table is not None:
        t = np.asarray(table, float)
        edge = np.interp(V[:, 2], t[:, 0], t[:, 1])
        lim, fine = float(cfg["rings_under_m"]), float(cfg["edge_fine_m"])
        w = np.clip((lim - edge) / max(lim - fine, 1e-6), 0.0, 1.0)
        depth = w * _bilinear(wood.deep_height, UV[:, 0], UV[:, 1]) + (1.0 - w) * game._relief(wood, UV[:, 0], UV[:, 1])
        # a swell's face is slanted, so the map's stretched over it, and full relief there folds the surface
        depth = depth * (1.0 - (1.0 - float(cfg["relief_on_swell"])) * on_swell * on_swell * (3.0 - 2.0 * on_swell))
        out = out + N * depth[:, None]
    out[:, 2] = np.maximum(out[:, 2], floor)
    N2 = weld_normals(out, F, N)
    return {**a, "V": out, "N": N2, "T": game._tangents(out, N2, UV, F)}


def split_detail(wood: game.WoodParts, cfg: dict) -> dict:
    """The bake's height as what the mesh will carry and what stays in the normal map.  The map holds
    all that the mesh can't, and a share of what it can, since a mesh shades only as sharply as its
    edges are short.  Returns the bake with that normal map."""
    bake = wood.stem_bake
    r = int(cfg["mesh_blur_px"])
    wood.deep_height = tx._box_v(tx._box_u(bake["height"], r), r)
    dx, dy = bake["texel_m"]
    keep = float(cfg["normal_keeps_deep_share"])
    fine = tx.finish({"albedo": bake["albedo"], "rough": bake["rough"], "height": bake["height"] - (1.0 - keep) * wood.deep_height}, np.broadcast_to(dx, dy.shape), dy)
    return {**bake, "normal": fine["normal"]}


def stain_foot(wood: game.WoodParts, a: dict, flows: np.ndarray, line: float, centre: np.ndarray, cfg: dict, look: dict, seed: int) -> None:
    """The stem's bark goes the colour of the roots' down each swell, and a little all round at the
    ground, as soil and rain do: patchily.  So the foot and the roots meet in colour.  ``a``: the stem's
    mesh, which says which way round its map each direction is."""
    bake = wood.stem_bake
    alb = bake["albedo"]
    H, W = alb.shape[:2]
    s = tx.stem_s(look, (np.arange(H) + 0.5) / H, wood.stem_length)
    prof = wood.profile
    above = np.interp(s, prof.s, np.maximum.accumulate(prof.z)) - line
    tallest = float((flows[:, 3] + flows[:, 4]).max()) if len(flows) else 0.0
    rows = np.nonzero(above < max(tallest, 3.0 * float(cfg["stain_ground_m"])))[0]
    if not len(rows):
        return
    h = int(rows[-1]) + 1
    up = np.maximum(above[:h], 0.0)
    field = np.broadcast_to((float(cfg["stain_ground_share"]) * np.exp(-up / float(cfg["stain_ground_m"])))[:, None], (h, W)).copy()
    if len(flows):
        low = np.nonzero(a["V"][:, 2] < line + 0.3)[0]
        theta = np.arctan2(a["V"][low, 1] - centre[1], a["V"][low, 0] - centre[0])
        turn = 2.0 * np.pi * a["UV"][low, 0]
        same, opposite = np.exp(1j * (turn - theta)).mean(), np.exp(1j * (turn + theta)).mean()
        sign, phase = (1.0, np.angle(same)) if abs(same) >= abs(opposite) else (-1.0, np.angle(opposite))
        u = (np.arange(W) + 0.5) / W
        for az, out_m, width, up_m, crest in flows:
            d = (2.0 * np.pi * u - (sign * az + phase) + np.pi) % (2.0 * np.pi) - np.pi
            rise = np.minimum(_swell_rise(up, up_m, crest, out_m), 1.0)
            field = np.maximum(field, np.exp(-0.5 * (d / (1.3 * width)) ** 2)[None, :] * rise[:, None])
    n = tx.rank01(0.6 * tx.noise((h, W), seed, (60.0, 24.0), 2.2) + 0.4 * tx.noise((h, W), seed + 1, (10.0, 6.0), 1.8))
    # the noise scales with the field, so where there's none to give there's no stain, and no edge
    amount = tx.smooth(0.12, 0.5, field * (0.4 + 1.2 * n)) * float(cfg["stain_opacity"])
    colour = np.asarray(cfg["root_colour"], np.float32) * (0.75 + 0.5 * n[..., None])
    alb[:h] = alb[:h] + (colour - alb[:h]) * amount[..., None].astype(np.float32)


def moss_amount(above: np.ndarray, u: np.ndarray, rough: np.ndarray, cfg: dict, seed: int) -> tuple:
    """How much moss at each texel, rows x columns, for rows at ``above`` reaches over the ground line:
    tufts and clumps, not a coat.  Their share of the bark falls off with height and round the stem,
    so there's no edge to see, and it's all but gone on the far side.  Also its tone, 0-1."""
    H, W = len(above), len(u)
    toward = float(ap.hash01(np.array([seed]), 72)[0])
    side = (0.5 + 0.5 * np.cos(2.0 * np.pi * (u - toward))) ** float(cfg["moss_side_power"])
    elsewhere = float(cfg["moss_elsewhere"])
    # how far up it gets wanders round the stem
    wander = 0.55 + 0.75 * tx.rank01(tx.noise((H, W), seed, (260.0, 90.0), 2.4))
    x = np.clip(above[:, None] / wander, 0.0, 1.0)
    fall = 1.0 - x * x * (3.0 - 2.0 * x)
    on_bark = float(cfg["moss_on_white"]) + (1.0 - float(cfg["moss_on_white"])) * rough[:, None]
    cover = float(cfg["moss_cover"]) * (elsewhere + (1.0 - elsewhere) * side[None, :]) * fall * on_bark
    clumps = tx.rank01(0.65 * tx.noise((H, W), seed + 1, (70.0, 34.0), 2.2) + 0.35 * tx.noise((H, W), seed + 2, (16.0, 9.0), 2.0))
    tuft = tx.rank01(tx.noise((H, W), seed + 3, (5.0, 4.0), 1.6))
    soft = 0.035
    amount = tx.smooth(1.0 - cover - soft, 1.0 - cover + soft, clumps) * (cover > 0.002)
    # thin on white bark, which shows it pale
    return (amount * float(cfg["moss_opacity"]) * (0.7 + 0.3 * tuft) * (0.4 + 0.6 * rough[:, None])).astype(np.float32), tuft


def moss_on_stem(look: dict, wood: game.WoodParts, line: float, cfg: dict, seed: int) -> None:
    """Moss at the foot, in the stem's own colour map.  The game's M_Surface would add it by world
    position, which smears up any upright surface, so the file's origin keeps that off (``origin_z``)."""
    bake = wood.stem_bake
    alb = bake["albedo"]
    H, W = alb.shape[:2]
    v = (np.arange(H) + 0.5) / H
    s = tx.stem_s(look, v, wood.stem_length)
    prof = wood.profile
    z = np.interp(s, prof.s, np.maximum.accumulate(prof.z))
    reach = min(float(cfg["moss_reach_m"]) + float(cfg["moss_reach_per_year_m"]) * wood.age, float(cfg["moss_reach_max_m"]))
    above = (z - line) / max(reach, 1e-6)
    rough = wood.state(np.interp(s, prof.s, prof.part_age), np.interp(s, prof.s, prof.d_wood), z)["weights"][-1]
    rows = np.nonzero(above < 1.3)[0]
    if not len(rows):
        return
    h = int(rows[-1]) + 1
    amount, tone = moss_amount(above[:h], (np.arange(W) + 0.5) / W, rough[:h], cfg, seed)
    colour = np.asarray(cfg["moss_colour"], np.float32) * (0.55 + 0.9 * tone[..., None])
    alb[:h] = alb[:h] + (colour - alb[:h]) * amount[..., None]
    bake["rough"][:h] = bake["rough"][:h] + (0.9 - bake["rough"][:h]) * amount


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
    # (roots.paid: a root's radius already holds its bark, as its density does)
    out[:n] = r if _paid(model) else np.where(root, r + wall * grow, r)
    axis0 = np.asarray(skel.axis[:n]) == 0
    stem = np.nonzero(axis0 & ~root)[0]
    if len(stem):
        foot_r = float(rad_ob[stem[np.argmin(z[stem])]])
        chain = axis0 & root
        fade = float(cfg["foot_fade_m"])
        # the fade starts below all that can show, or the smoothing along the stem brings it up as a waist
        t = np.clip((line - float(cfg["surface_depth_m"]) - z) / max(fade, 1e-6), 0.0, 1.0)
        want = foot_r + (out[:n] - foot_r) * (t * t * (3.0 - 2.0 * t))
        if _paid(model):
            # the stump's mass stays in the model; what shows is the stem's foot, which swells by its own rule
            out[:n] = np.where(chain, np.minimum(out[:n], foot_r), out[:n])
        else:
            out[:n] = np.where(chain, np.maximum(out[:n], want), out[:n])
    return out


def root_state(wood: game.WoodParts, part_age, d_wood, rough: float = 1.0) -> dict:
    """A root's bark: the stem's own white and rough stages, by ``rough``, whatever its age, so it's the
    bark of the foot it comes out of, and no root shows a shoot's red.  TUNED."""
    st = wood.state(part_age, d_wood, np.zeros(len(np.atleast_1d(part_age))))
    w = np.zeros_like(np.asarray(st["weights"], float))
    w[:-1] = 1.0
    w[-1] = float(rough)
    return {**st, "weights": w, "peel": np.zeros_like(st["peel"])}


def root_atlas(look: dict, wood: game.WoodParts, tiles: list, md: meshlib.MeshData, birth: np.ndarray, radius_now: np.ndarray, cfg: dict) -> dict:
    """The branch atlas's layout, baked with what the roots are, stained by the soil."""
    classes = np.asarray(look["bark"]["branch_circumference_m"], float)
    node = md.attributes["node_id"].astype(np.int64)
    F = md.faces
    V = md.vertices
    cl = game._face_class(md.attributes["radius"], F, classes)
    area = 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    st = root_state(wood, wood.age - birth[node], 2.0 * radius_now[node], float(cfg["root_rough"]))
    states = [None] * len(classes)
    for k in range(len(classes)):
        sel = cl == k
        if sel.any():
            v0 = F[sel, 0]
            wts = area[sel] / max(area[sel].sum(), 1e-12)
            states[k] = {"weights": (st["weights"][:, v0] * wts).sum(1), "peel": 0.0, "grime": float((st["grime"][v0] * wts).sum()), "fissure_m": float((st["fissure_m"][v0] * wts).sum())}
    atlas = tx.bake_branch_atlas(look, tiles, states)
    # low contrast: a root seen against the soil is one colour, near enough, and the foot's stain is that colour
    colour = np.asarray(cfg["root_colour"], np.float32)
    atlas["albedo"] = colour + (atlas["albedo"] - colour) * float(cfg["root_contrast"])
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


def roots_showing(surface: meshlib.MeshData | None, line: float, centre: np.ndarray) -> dict:
    """What of the roots stands above the ground in the file: how many, and how far out."""
    if surface is None:
        return {"roots": 0, "reach_m": 0.0}
    above = surface.vertices[:, 2] > line
    if not above.any():
        return {"roots": 0, "reach_m": 0.0}
    return {"roots": int(len(np.unique(surface.attributes["axis_id"][above]))), "reach_m": round(float(np.hypot(*(surface.vertices[above, :2] - centre).T).max()), 2)}


def seat_sheets(f: dict, lowest: float) -> dict:
    """The far level's sheets, cut off at the tree's lowest point, since the game seats each level by
    its own."""
    V, UV = f["V"].copy(), f["UV"].copy()
    for q in range(0, len(V), 4):
        z = V[q:q + 4, 2]
        lo, hi = z.min(), z.max()
        if lo >= lowest or hi <= lowest:
            continue
        v_lo, v_hi = UV[q:q + 4, 1][np.argmin(z)], UV[q:q + 4, 1][np.argmax(z)]
        bottom = z < 0.5 * (lo + hi)
        UV[q:q + 4, 1][bottom] = v_lo + (lowest - lo) / (hi - lo) * (v_hi - v_lo)
        V[q:q + 4, 2][bottom] = lowest
    return {**f, "V": V, "UV": UV}


def black_zone(wood: game.WoodParts, origin_z: float = 0.0, reach: float = 0.0) -> dict:
    """Up the stem, where the rough base gives way to what's above it: BarkStartCm and BarkBlendCm for
    M_Surface's UpperBark, which fades from the colour map to a tiled scan.  ``reach``: as ``stem_edges``,
    so the scan starts above the highest of the base's tongues."""
    prof = wood.profile
    w = wood.state(prof.part_age, prof.d_wood, prof.z - reach)["weights"]
    rough = w[2] if len(w) > 2 else np.zeros(len(prof.z))
    z = np.maximum.accumulate(prof.z)
    hi = z[rough >= 0.9]
    lo = z[rough >= 0.1]
    start = float(hi.max()) if len(hi) else 0.0
    end = float(lo.max()) if len(lo) else start
    return {"bark_start_cm": round((start + origin_z) * 100.0, 1), "bark_blend_cm": round(max(end - start, 0.05) * 100.0, 1)}


# -- leaves -----------------------------------------------------------------------------------------
def leaf_atlas(look: dict, seed: int) -> dict:
    """The leaf at each chlorophyll level, in columns: its measured colour at that level, yellow coming
    first between the veins.  Mean colour of a column is the diffuse reflectance measured at its level."""
    u = look["game"]["unreal"]
    levels = int(u["leaf_levels"])
    fractions = np.linspace(float(u["leaf_level_range"][0]), float(u["leaf_level_range"][1]), levels)
    n = int(look["leaves"]["texture_size_px"])
    R, _ = ap.leaf_colours(look, fractions)
    sh = look["leaves"]["shape"]
    rows = int(sh["variants"])
    rgb = np.zeros((n * rows, n * levels, 3), np.float32)
    nrm = np.zeros((n * rows, n * levels, 3), np.float32)
    rough = np.full((n * rows, n * levels), 0.5, np.float32)
    alpha = np.zeros((n * rows, n * levels), np.float32)
    uv_half = float(sh["uv_half"]) * 2.0
    unit = np.zeros(rows)
    stalk = np.asarray(u["leaf"]["stalk_colour"], np.float32)
    s = max(n // 40, 3)
    for v in range(rows):
        y0, y1 = v * n, (v + 1) * n
        for i, f in enumerate(fractions):
            blade = tx.leaf_blade(look, seed + 37 * v, game._turning(float(f), look["leaves"]["interveinal_lead"]), variant=v)
            a = blade["alpha"]
            mean = np.maximum((blade["rgb"] * a[..., None]).reshape(-1, 3).sum(0) / max(float(a.sum()), 1.0), 1e-4)
            colour = blade["rgb"] * (R[i] / mean).astype(np.float32)
            colour = tx.push_pull_fill(colour, (a >= 0.5).astype(np.float32))
            # the leaf stalk's colour, in the corner the blade doesn't reach
            colour[-s:, :s] = stalk
            rgb[y0:y1, i * n:(i + 1) * n] = colour
            nrm[y0:y1, i * n:(i + 1) * n] = blade["normal"]
            rough[y0:y1, i * n:(i + 1) * n] = 0.5 - 0.12 * np.clip(blade["normal"][..., 2] - 0.9, 0.0, 0.1) * 10.0
            alpha[y0:y1, i * n:(i + 1) * n] = a
            alpha[y1 - s:y1, i * n:i * n + s] = 1.0
        # the blade's area for a length of 1: the cell is 1 long and hmax / uv_half wide
        hmax = tx.leaf_margin(sh, v)["hmax"]
        unit[v] = float((a >= 0.35).mean()) * 2.0 * hmax / uv_half
    return {"rgb": rgb, "normal": nrm, "rough": rough, "alpha": alpha, "fractions": fractions, "unit": unit, "stalk_px": s, "cell_px": n, "rows": rows}


def hang_leaves(leaves: ap.LeafInstances, z_rel: np.ndarray, cfg: dict) -> ap.LeafInstances:
    """The leaves' angle to the horizontal as measured (Hagemeier & Leuschner 2019a): they hang, 49
    degrees on average, about 55 at the top of the crown and about 30 at its bottom.  That's a blade's
    slope from its base to its tip, so the curl ``blade_mesh`` will give each leaf is taken off here."""
    n = len(leaves.node)
    key = np.arange(n)
    table = np.asarray(cfg["angle_by_height"], float)
    mean = np.interp(z_rel, table[:, 0], table[:, 1])
    curl = float(cfg["curl"][0]) + (float(cfg["curl"][1]) - float(cfg["curl"][0])) * ap.hash01(key, 86)
    inc = np.radians(mean + float(cfg["angle_spread_deg"]) * (ap.hash01(key, 81) - 0.5) * 2.0) - np.arctan(curl)
    az = np.arctan2(leaves.along[:, 1], leaves.along[:, 0])
    outward = np.stack([np.cos(az), np.sin(az), np.zeros(n)], 1)
    along = outward * np.cos(inc)[:, None] + np.array([0.0, 0.0, -1.0]) * np.sin(inc)[:, None]
    across = np.stack([-np.sin(az), np.cos(az), np.zeros(n)], 1)
    roll = (ap.hash01(key, 3) - 0.5) * float(cfg["roll_rad"])
    n0 = np.cross(along, across)
    across = across * np.cos(roll)[:, None] + n0 * np.sin(roll)[:, None]
    out = copy.copy(leaves)
    out.along, out.across = along, across
    return out


def _zipper(t_mid: np.ndarray, t_side: np.ndarray, side0: int, flip: bool) -> list:
    """Triangles between the midrib's chain (vertices 0 up, base and tip its ends) and one margin's
    chain, walking both by position along the leaf.  The margin starts at the base and ends at the tip."""
    n_mid = len(t_mid)
    ext = [0] + [side0 + k for k in range(len(t_side))] + [n_mid - 1]
    t_ext = np.r_[0.0, t_side, 1.0]
    tri = []
    i, j = 0, 0
    while i < n_mid - 1 or j < len(ext) - 1:
        go_mid = j == len(ext) - 1 or (i < n_mid - 1 and t_mid[i + 1] <= t_ext[j + 1])
        if go_mid:
            f = (i, i + 1, ext[j])
            i += 1
        else:
            f = (i, ext[j + 1], ext[j])
            j += 1
        if len(set(f)) == 3:
            tri.append(f[::-1] if flip else f)
    return tri


def blade_mesh(look: dict, leaves: ap.LeafInstances, chl: np.ndarray, atlas: dict, z_rel: np.ndarray) -> dict:
    """Each leaf its real outline, curved, with its main teeth in the mesh and the small ones cut by the
    colour map's alpha, a stalk from the twig, a fold along the midrib, a droop to the tip and a slight
    twist, all differing from leaf to leaf.  Visible area exactly the model's."""
    cfg = look["game"]["unreal"]["leaf"]
    sh = look["leaves"]["shape"]
    fractions = atlas["fractions"]
    levels = len(fractions)
    rows = atlas["rows"]
    n = len(leaves.node)
    key = np.arange(n)
    h = lambda salt: ap.hash01(key, salt)  # noqa: E731
    variant = (h(82) * rows).astype(np.int64)
    flip_uv = h(83) < 0.5
    width = float(cfg["width_low"]) + (float(cfg["width_high"]) - float(cfg["width_low"])) * h(84)
    fold = np.radians(float(cfg["fold_deg"][0]) + (float(cfg["fold_deg"][1]) - float(cfg["fold_deg"][0])) * h(85))
    curl = float(cfg["curl"][0]) + (float(cfg["curl"][1]) - float(cfg["curl"][0])) * h(86)
    twist = float(cfg["twist_rad"]) * (h(87) - 0.5) * 2.0
    bend = float(cfg["side_bend"]) * (h(88) - 0.5) * 2.0
    ripple = float(cfg["ripple"]) * h(89)
    L = np.sqrt(leaves.area / (atlas["unit"][variant] * width))
    hmax = np.array([tx.leaf_margin(sh, v)["hmax"] for v in range(rows)])
    # the stalk: from the twig's surface, out and arching down to the blade's base
    outward = leaves.base - leaves.twig
    plen = np.linalg.norm(outward, axis=1)
    out_dir = outward / np.maximum(plen, 1e-9)[:, None]
    plen = plen * (0.8 + 0.5 * h(90))
    z_up = np.array([0.0, 0.0, 1.0])
    p0 = leaves.twig
    p1 = p0 + out_dir * (0.55 * plen)[:, None] + z_up * (0.12 * plen)[:, None]
    p2 = p0 + out_dir * (0.85 * plen)[:, None] - z_up * (0.35 * plen)[:, None]
    a, c = leaves.along, leaves.across
    nrm = np.cross(a, c)
    # vertices: blade (midrib, then each margin), then the stalk's three pairs
    t_mid = np.asarray(cfg["midrib_at"], float)
    n_mid = len(t_mid)
    margins = [tx.leaf_margin(sh, v) for v in range(rows)]
    t_lead = np.asarray(cfg["base_points_at"], float)
    n_side = len(t_lead) + int(sh["main_teeth"])
    blade_v = n_mid + 2 * n_side
    per = blade_v + 6
    V = np.zeros((n, per, 3))
    UV = np.zeros((n, per, 2))

    def along_midrib(tv):
        """Where the midrib is at tv (n x k), and the two directions across it there."""
        t2 = tv * tv
        tw = (twist[:, None] * tv)
        cc, ss = np.cos(tw), np.sin(tw)
        P = p2[:, None, :] + (L[:, None] * tv)[..., None] * a[:, None, :] + (L[:, None] * bend[:, None] * t2)[..., None] * c[:, None, :] - (L[:, None] * curl[:, None] * t2)[..., None] * nrm[:, None, :]
        C = cc[..., None] * c[:, None, :] + ss[..., None] * nrm[:, None, :]
        N_ = cc[..., None] * nrm[:, None, :] - ss[..., None] * c[:, None, :]
        return P, C, N_

    tm = np.broadcast_to(t_mid, (n, n_mid))
    P_mid, _, _ = along_midrib(tm)
    V[:, :n_mid] = P_mid
    UV[:, :n_mid, 0] = 0.5
    UV[:, :n_mid, 1] = 1.0 - tm
    sides = {}
    for k_side, (side, offset) in enumerate(((1, n_mid), (-1, n_mid + n_side))):
        ts = np.zeros((n, n_side))
        hs = np.zeros((n, n_side))
        for v in range(rows):
            sel = variant == v
            m = margins[v]
            tv = np.r_[t_lead, m["tips"][side]]
            ts[sel] = tv
            hs[sel] = tx.leaf_half_at(m, tv)
        sides[side] = ts
        P, C, N_ = along_midrib(ts)
        half = (L * hmax[variant] * width)[:, None] * hs
        up = np.sin(fold)[:, None] * half + (ripple * L)[:, None] * np.where(np.arange(n_side) % 2 == 0, 1.0, -1.0)
        V[:, offset:offset + n_side] = P + (side * np.cos(fold)[:, None] * half)[..., None] * C + up[..., None] * N_
        u = 0.5 + side * float(sh["uv_half"]) * hs
        UV[:, offset:offset + n_side, 0] = u
        UV[:, offset:offset + n_side, 1] = 1.0 - ts
    # the stalk: a thin ribbon, across the leaf
    w_stalk = float(cfg["stalk_width_m"]) * 0.5
    o = blade_v
    for k, p in enumerate((p0, p1, p2)):
        V[:, o + 2 * k] = p - c * w_stalk
        V[:, o + 2 * k + 1] = p + c * w_stalk
    cell = atlas["cell_px"]
    s_uv = (atlas["stalk_px"] * 0.5) / cell
    UV[:, o:o + 6, 0] = s_uv
    UV[:, o:o + 6, 1] = 1.0 - s_uv
    # mirror half the leaves in the map; the column of the leaf's chlorophyll, the row of its variant
    low, high = fractions[0], fractions[-1]
    level = np.clip(np.round((chl - low) / max(high - low, 1e-6) * (levels - 1)), 0, levels - 1)
    blade_u = UV[:, :blade_v, 0]
    UV[:, :blade_v, 0] = np.where(flip_uv[:, None], 1.0 - blade_u, blade_u)
    UV[..., 0] = (level[:, None] + UV[..., 0]) / levels
    UV[..., 1] = (variant[:, None] + UV[..., 1]) / rows
    # faces: one template, as the same counts hold for every leaf; which teeth sit where changes little
    t_side_r = np.r_[t_lead, margins[0]["tips"][1]]
    t_side_l = np.r_[t_lead, margins[0]["tips"][-1]]
    tri = _zipper(t_mid, t_side_r, n_mid, False) + _zipper(t_mid, t_side_l, n_mid + n_side, True)
    tri += [(o, o + 1, o + 2), (o + 1, o + 3, o + 2), (o + 2, o + 3, o + 4), (o + 3, o + 5, o + 4)]
    tri = np.asarray(tri, np.int64)
    F = (np.arange(n)[:, None, None] * per + tri[None]).reshape(-1, 3)
    V = V.reshape(-1, 3)
    UV = UV.reshape(-1, 2)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return {"V": V, "N": N, "F": F, "UV": UV, "T": game._tangents(V, N, UV, F), "per": per, "level": level, "tris_per_leaf": len(tri)}


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
    root_cfg = foot_settings(model, u["roots"])
    line = ground_line(model, age, root_cfg)
    rad_ob = root_radii(look, model, age, rad_ob, skel, is_root, line, root_cfg, ap.over_bark_dbh_cm(look, dbh_w))
    skel = stem_goes_down(skel, is_root, line, root_cfg)
    gfull = look["game"]["full_mesh"]
    clean = {k: u[k] for k in ("ring_tolerance", "ring_tolerance_m", "ring_longest_span")}
    clean["drop_hidden_rings"] = float(u["ring_tolerance"]) > 0.0 or float(u["ring_tolerance_m"]) > 0.0
    wood = game.WoodParts(look, tiles, age, height, dbh_w, T.birth[: T.n], r_wood)
    wood.tree_seed = int(ctx["seed"])
    alive = (T.birth[: T.n] <= age) & ((T.death[: T.n] < 0) | (T.death[: T.n] > age))
    relief_cfg = u["stem_relief"]
    surface_depth = float(root_cfg["surface_depth_m"])
    # the stem's nodes, foot upwards, as the mesher will have it
    clean["stem_stub_share"] = ap.stem_stub_share(look)
    view = meshlib.continue_trunk(SimpleNamespace(n=T.n, pos=pos, parent=T.parent, axis=T.axis, is_lateral=T.is_lateral, order=T.order, birth=T.birth, death=T.death, depth=T.depth), alive, r_wood, clean["stem_stub_share"])
    stem_ids = np.nonzero((np.asarray(view.axis[: T.n]) == 0) & alive)[0]
    stem_ids = stem_ids[np.argsort(pos[stem_ids, 2])]
    stem_node = int(stem_ids[0])
    edge_top = tx.uneven_top(look, float(age - T.birth[stem_ids].min()), wood.tree_seed, wood.dbh_ob)
    edge_reach = 0.0 if edge_top is None else edge_top.reach
    table = None
    if float(relief_cfg["edge_fine_m"]) > 0.0:
        table = stem_edges(wood, pos[stem_ids, 2], age - T.birth[stem_ids].astype(float), 2.0 * r_wood[stem_ids], line, surface_depth, relief_cfg, edge_reach)
    # the ridges hold down to below where the ground can reach, so the foot only ever widens towards it
    clean["buttress_hold_m"] = surface_depth - line
    # the foot's shape here is the butt swell and a swell for each root that shows (root_flows)
    clean["no_stem_ridges"] = True
    settings0 = meshlib.MeshSettings(ring_attributes=True, stem_sides_by_radius=True, sides_allowed=tuple(gfull["sides_allowed"]), stem_edge_by_height=table or (),
                                     stem_along_factor=float(relief_cfg["along_factor"]), stem_rings_under=float(relief_cfg["rings_under_m"]), **clean)
    crown0, roots0 = tree_meshes(skel, np.ones(n, bool), rad_ob, is_root, orig, sp.geometry, settings0)
    collar = collar_radius(model, age)
    swell = (float(sp.geometry.root_flare_extra) * float(relief_cfg["swell_share"]), float(sp.geometry.root_flare_height))
    stem_r = crown0.attributes["radius"][crown0.attributes["axis_id"] == 0]
    stem_v_low = crown0.vertices[crown0.attributes["axis_id"] == 0]
    low = stem_v_low[:, 2] < float(stem_v_low[:, 2].min()) + 0.2
    centre = stem_v_low[low, :2].mean(0)
    foot_r = float(np.median(stem_r[low])) * (1.0 + swell[0])
    foot0, surface0, below0 = split_roots(sink_roots(roots0, line, centre, foot_r, collar, root_cfg), root_cfg, line, collar)
    merged0 = game.join_meshes([crown0, as_stem(foot0, stem_node)])
    if foot0 is not None:
        wood.stem_y_offset = float(crown0.attributes["ring_along"][crown0.attributes["axis_id"] == 0].min() - foot0.attributes["ring_along"].min())
    game.bake_wood(wood, merged0, T, pos, model.radius_history)
    stem_near = split_detail(wood, relief_cfg) if table is not None else wood.stem_bake
    arrays0 = game.wood_arrays(wood, merged0)
    flows = root_flows(surface0, centre, foot_r, root_cfg)
    stain_foot(wood, arrays0["stem"], flows, line, centre, root_cfg, look, int(look["game"]["texture_seed"]) + 920)
    moss_on_stem(look, wood, line, root_cfg, int(look["game"]["texture_seed"]) + 910)
    arrays0["stem"] = shape_stem(arrays0["stem"], wood, line, line - surface_depth, swell, table, relief_cfg, flows, centre)
    origin_z = float(root_cfg["origin_below_lowest_m"]) - (line - surface_depth)
    flex = wind_flex(pos, np.asarray(T.parent[: T.n]), alive, np.asarray(T.depth[: T.n]))
    phase = float(ap.hash01(np.array([int(ctx["seed"])]), 71)[0])
    seed = int(look["game"]["texture_seed"])
    tile_m = float(u["bark_wrap_tile_m"])
    lods = {lod["name"]: lod for lod in look["game"]["lods"]}
    lod1 = next((v for v in lods.values() if v["kind"] == "reduced"), None)
    arrays1 = None
    surface1, below1 = None, None
    if lod1 is not None and lod1.get("budget") is not None:
        rm = look["game"]["reduced_mesh"]
        settings1 = meshlib.MeshSettings(edge_target=rm["edge_target"], sides_allowed=tuple(rm["sides_allowed"]), ring_spacing_factor=rm["ring_spacing_factor"],
                                         min_ring_spacing=rm["min_ring_spacing"], max_ring_spacing=rm["max_ring_spacing"], max_turn_deg=rm["max_turn_deg"],
                                         ring_attributes=True, stem_sides_by_radius=True, **clean)
        thr = game.reduced_radius_threshold(skel, rad_ob, is_root, orig, sp.geometry, settings1, int(float(lod1["budget"]) * float(lod1["wood_share"])))
        crown1, roots1 = tree_meshes(skel, game.reduced_selection(skel, rad_ob, thr), rad_ob, is_root, orig, sp.geometry, settings1)
        foot1, surface1, below1 = split_roots(sink_roots(roots1, line, centre, foot_r, collar, root_cfg), root_cfg, line, collar)
        arrays1 = game.wood_arrays(wood, game.join_meshes([crown1, as_stem(foot1, stem_node)]))
        arrays1["stem"] = shape_stem(arrays1["stem"], wood, line, line - surface_depth, swell, None, relief_cfg, flows, centre)
    base_name = f"{asset}_age{age:03d}"
    maps = Maps(out, asset)
    split = out / "SourceArt" / "PolyHaven_split" / asset
    split.mkdir(parents=True, exist_ok=True)
    # bark maps, once per age
    stem_slot, branch_slot, strip_slot = f"{base_name}_stem_bark", f"{base_name}_branch_bark", f"{base_name}_bark_strip"
    stem_files = _bark_maps(maps, stem_slot, stem_near)
    # a level without the relief in its mesh needs it all in its normal map
    stem_far_slot, stem_far_files = stem_slot, stem_files
    if stem_near is not wood.stem_bake and arrays1 is not None:
        stem_far_slot = f"{stem_slot}_lod1"
        stem_far_files = _bark_maps(maps, stem_far_slot, wood.stem_bake)
    branch_files = _bark_maps(maps, branch_slot, wood.atlas)
    stem_circ = 2.0 * np.pi * float(wood.profile.radius[0])
    turns = float(max(round(stem_circ / tile_m), 1))
    # roots: their own tree's ids, so their own birth years and radii
    root_birth = np.asarray(model.roots.tree.birth)
    root_radius = np.asarray(model.roots.radius_history[age], float)
    root_slot = f"{base_name}_root_bark"
    root_bake = root_atlas(look, wood, tiles, roots0, root_birth, root_radius, root_cfg)
    root_files = _bark_maps(maps, root_slot, root_bake)
    surface_a = {"full": root_arrays(look, wood, surface0, root_bake, root_birth, root_radius), "reduced": root_arrays(look, wood, surface1, root_bake, root_birth, root_radius)}
    root_files_out = {}
    for lname, below_md in (("lod0", below0), ("lod1", below1)):
        arr = root_arrays(look, wood, below_md, root_bake, root_birth, root_radius)
        if arr is None:
            continue
        rname = f"{base_name}_roots" + ("" if lname == "lod0" else f"_{lname}")
        rpath = split / f"{rname}.gltf"
        rglb = GameGLB(rpath, rname, {**meta, "age": age, "level": lname, "part": "everything below ground", "color0": COLOR0, "uv_layout": UV_LAYOUT})
        rglb.origin_z = origin_z
        _root_mesh(rglb, wood, arr, "roots_below_ground", maps.material(rglb, root_slot, root_files, CLAMP, REPEAT), root_birth, root_radius, phase, tile_m)
        info = rglb.write_gltf()
        info.update(file=str(rpath.relative_to(out)).replace("\\", "/"), variant=rname, min_z_m=round(float(arr["V"][:, 2].min()), 3))
        root_files_out[lname] = info
    # leaves
    blade0 = tx.leaf_blade(look, seed + 500)
    leaves = ap.leaf_instances(look, sp, ctx["snaps"][age], pos, r_wood, age, blade0["fill"])
    # where each leaf's stalk leaves its twig: the base as placed, less the stalk's length
    leaf_out = leaves.base - pos[leaves.node]
    leaf_out /= np.maximum(np.linalg.norm(leaf_out, axis=1, keepdims=True), 1e-9)
    leaves.twig = pos[leaves.node] + leaf_out * r_wood[leaves.node][:, None]
    leaf_z_rel = np.clip(pos[leaves.node, 2] / max(height, 1e-3), 0.0, 1.0)
    leaves = hang_leaves(leaves, leaf_z_rel, u["leaf"])
    atlas = leaf_atlas(look, seed + 500)
    leaf_slot = f"{base_name}_leaf"
    leaf_files = maps.write(leaf_slot, atlas["rgb"], atlas["normal"], atlas["rough"], alpha=atlas["alpha"])
    strips = ap.peel_strips(look, pos, T.parent[: T.n], r_wood, T.birth[: T.n], alive, age, height, ap.over_bark_dbh_cm(look, dbh_w))
    strip_tex = strip_atlas(look, seed + 600)
    strip_files = maps.write(strip_slot, strip_tex["rgb"], strip_tex["normal"], strip_tex["rough"], alpha=strip_tex["alpha"])
    cards = card_atlas(look, seed + 700) if lod1 is not None else None
    card_slot = f"{base_name}_card_leaf"
    card_files = maps.write(card_slot, cards["rgb"], cards["normal"], cards["rough"], alpha=cards["alpha"]) if cards is not None else None
    days = look["leaves"]["season"]["days"]
    out_stage = {"age": age, "height_m": height, "dbh_wood_cm": dbh_w, "dbh_over_bark_cm": round(ap.over_bark_dbh_cm(look, dbh_w), 2), "exported_leaves": int(len(leaves.node)),
                 "roots": {**root_table(model, age), "ground_line_m": round(line, 3), "showing": roots_showing(surface0, line, centre), "files": root_files_out},
                 "upper_bark": black_zone(wood, origin_z, edge_reach), "origin": {"model_zero_in_file_m": round(origin_z, 4), "ground_in_file_m": round(origin_z + line, 4), "lowest_in_file_m": round(origin_z + line - surface_depth, 4)},
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
            glb.origin_z = origin_z
            parts = {}
            if lod["kind"] == "far":
                near = split / f"{base_name}{suffix}.gltf"
                f = seat_sheets(game.far_sheets(near, lod), origin_z + line - surface_depth)
                glb.origin_z = 0.0      # read from the near file, so already where it goes
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
                    near_level = lod["kind"] == "full"
                    m = maps.material(glb, stem_slot if near_level else stem_far_slot, stem_files if near_level else stem_far_files, REPEAT, CLAMP)
                    _bark_mesh(glb, wood, arrays["stem"], "stem", m, flex, phase, turns, tile_m)
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
                        m = maps.material(glb, leaf_slot, leaf_files, CLAMP, CLAMP, alpha_clip=float(u["alpha_clip"]), two_sided=True, extras=_leaf_extras(look, float(np.mean(chl))))
                        b = blade_mesh(look, leaves, chl, atlas, leaf_z_rel)
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
            all_v = _positions(glb)
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
