"""Writers for the mesh files, the growth timeline and stats.json.

Internal frame is z-up metres.  USD keeps it (upAxis = Z, metersPerUnit = 1);
glTF requires y-up, so GLB output is rotated (x, y, z) -> (x, z, -y).

Meshes are written a chunk at a time (``mesh.build_mesh_chunks``), so a
tree never sits in memory whole:

* ``GLBWriter`` spools each vertex stream to a temporary file and assembles
  one glTF primitive at the end;
* ``USDWriter`` writes ``tree.usdc`` with one Xform per mesh group; the
  chunk meshes live in part layers (``<stem>_parts/<group>_NNN.usdc``),
  loaded as payloads, each saved and released once it is full.

The timeline is ``timeline.npz`` (numpy arrays) with a small JSON header
(``timeline.json``) that describes the layout; ``load_timeline`` reads it.
"""
from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

import numpy as np

from .mesh import MeshData

GLB_ATTRIBUTE_NAMES = {
    "birth_year": "_BIRTH_YEAR",
    "death_year": "_DEATH_YEAR",
    "branch_order": "_BRANCH_ORDER",
    "radius": "_RADIUS",
    "node_id": "_NODE_ID",
    "depth_below_ground": "_DEPTH_BELOW_GROUND",
}


def _y_up(v: np.ndarray) -> np.ndarray:
    return np.stack([v[:, 0], v[:, 2], -v[:, 1]], axis=1)


# -- GLB ------------------------------------------------------------------------
class GLBWriter:
    """One mesh (one glTF primitive) streamed into a .glb chunk by chunk."""

    def __init__(self, path, name: str, metadata: dict, attributes, base_color=(220, 218, 205)):
        self.path = Path(path)
        self.name = name
        self.metadata = metadata
        self.attributes = list(attributes)
        self.base_color = base_color
        self.tmp = self.path.with_name(self.path.name + ".spool")
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.streams = ["POSITION", "NORMAL"] + [GLB_ATTRIBUTE_NAMES[k] for k in self.attributes] + ["INDICES"]
        self.files = {s: open(self.tmp / s, "wb") for s in self.streams}
        self.nv = 0
        self.nf = 0
        self.lo = np.full(3, np.inf)
        self.hi = np.full(3, -np.inf)

    def add(self, md: MeshData | None):
        if md is None or not len(md.faces):
            return
        v = np.ascontiguousarray(_y_up(md.vertices), dtype="<f4")
        self.lo = np.minimum(self.lo, v.min(0))
        self.hi = np.maximum(self.hi, v.max(0))
        self.files["POSITION"].write(v.tobytes())
        self.files["NORMAL"].write(np.ascontiguousarray(_y_up(md.normals), dtype="<f4").tobytes())
        for k in self.attributes:
            self.files[GLB_ATTRIBUTE_NAMES[k]].write(np.ascontiguousarray(md.attributes[k], dtype="<f4").tobytes())
        self.files["INDICES"].write(np.ascontiguousarray(md.faces + self.nv, dtype="<u4").tobytes())
        self.nv += len(v)
        self.nf += len(md.faces)

    def close(self) -> dict:
        for f in self.files.values():
            f.close()
        info = {"vertices": int(self.nv), "triangles": int(self.nf)}
        if self.nv == 0:
            shutil.rmtree(self.tmp, ignore_errors=True)
            return info
        views, accessors, attrs, offset = [], [], {}, 0
        for s in self.streams:
            size = (self.tmp / s).stat().st_size
            idx = s == "INDICES"
            views.append({"buffer": 0, "byteOffset": offset, "byteLength": size, "target": 34963 if idx else 34962})
            acc = {"bufferView": len(views) - 1, "componentType": 5125 if idx else 5126,
                   "count": 3 * self.nf if idx else self.nv,
                   "type": "SCALAR" if idx or s not in ("POSITION", "NORMAL") else "VEC3"}
            if s == "POSITION":
                acc["min"] = [float(x) for x in self.lo]
                acc["max"] = [float(x) for x in self.hi]
            accessors.append(acc)
            if not idx:
                attrs[s] = len(accessors) - 1
            offset += size
        doc = {
            "asset": {"version": "2.0", "generator": "treegen", "extras": self.metadata},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": self.name}],
            "meshes": [{"name": self.name, "primitives": [
                {"attributes": attrs, "indices": len(accessors) - 1, "material": 0, "mode": 4}]}],
            "materials": [{"name": "bark_placeholder", "pbrMetallicRoughness": {
                "baseColorFactor": [c / 255.0 for c in self.base_color] + [1.0],
                "metallicFactor": 0.0, "roughnessFactor": 0.85}}],
            "accessors": accessors,
            "bufferViews": views,
            "buffers": [{"byteLength": offset}],
        }
        js = json.dumps(doc, separators=(",", ":")).encode("utf-8")
        js += b" " * (-len(js) % 4)
        with open(self.path, "wb") as out:
            out.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + offset))
            out.write(struct.pack("<I4s", len(js), b"JSON"))
            out.write(js)
            out.write(struct.pack("<I4s", offset, b"BIN\x00"))
            for s in self.streams:
                with open(self.tmp / s, "rb") as f:
                    shutil.copyfileobj(f, out, 1 << 22)
        shutil.rmtree(self.tmp, ignore_errors=True)
        return info


# -- USD ------------------------------------------------------------------------
def _define_mesh(stage, path: str, m: MeshData, color):
    from pxr import Gf, Sdf, UsdGeom, Vt

    mesh = UsdGeom.Mesh.Define(stage, path)
    pts = np.ascontiguousarray(m.vertices, dtype=np.float32)
    mesh.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(pts))
    mesh.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(m.faces), 3, dtype=np.int32)))
    mesh.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(np.ascontiguousarray(m.faces.ravel(), dtype=np.int32)))
    mesh.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(np.ascontiguousarray(m.normals, dtype=np.float32)))
    mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    mesh.CreateOrientationAttr(UsdGeom.Tokens.rightHanded)
    lo, hi = pts.min(0), pts.max(0)
    mesh.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, lo)), Gf.Vec3f(*map(float, hi))]))
    mesh.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(*color)]))
    pv = UsdGeom.PrimvarsAPI(mesh)
    for key, arr in m.attributes.items():
        if arr.dtype.kind == "f":
            p = pv.CreatePrimvar(key, Sdf.ValueTypeNames.FloatArray, UsdGeom.Tokens.vertex)
            p.Set(Vt.FloatArray.FromNumpy(np.ascontiguousarray(arr, dtype=np.float32)))
        else:
            p = pv.CreatePrimvar(key, Sdf.ValueTypeNames.IntArray, UsdGeom.Tokens.vertex)
            p.Set(Vt.IntArray.FromNumpy(np.ascontiguousarray(arr, dtype=np.int32)))


def _new_stage(path: Path):
    from pxr import Sdf, Usd, UsdGeom

    layer = Sdf.Layer.Find(str(path))
    if layer:  # still registered from an earlier write in this process
        layer.Clear()
        stage = Usd.Stage.Open(layer)
    else:
        stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    return stage


class USDWriter:
    """``tree.usdc``: /Tree with one Xform per group (Living, Roots, ...).

    ``inline=False``: chunk meshes go to part layers loaded as payloads; a
    part is saved and released once it holds ``part_vertices`` vertices.
    ``inline=True``: chunk meshes are written into the root layer (for small
    meshes)."""

    def __init__(self, path, metadata: dict, inline: bool = False, part_vertices: int = 1_500_000):
        from pxr import UsdGeom

        self.path = Path(path)
        self.inline = inline
        self.part_vertices = int(part_vertices)
        self.parts_dir = self.path.with_name(self.path.stem + "_parts")
        if not inline:
            shutil.rmtree(self.parts_dir, ignore_errors=True)
            self.parts_dir.mkdir(parents=True)
        self.stage = _new_stage(self.path)
        root = UsdGeom.Xform.Define(self.stage, "/Tree")
        self.stage.SetDefaultPrim(root.GetPrim())
        root.GetPrim().SetCustomData({k: v for k, v in metadata.items() if isinstance(v, (int, float, str))})
        self.groups = {}

    def group(self, name: str, color=(0.86, 0.85, 0.80), hidden: bool = False, attrs: dict | None = None):
        from pxr import Sdf, UsdGeom, Vt

        x = UsdGeom.Xform.Define(self.stage, f"/Tree/{name}")
        if hidden:
            x.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
        for key, val in (attrs or {}).items():
            if isinstance(val, (list, tuple)):
                x.GetPrim().CreateAttribute(key, Sdf.ValueTypeNames.FloatArray, custom=True).Set(
                    Vt.FloatArray([float(v) for v in val]))
            elif val is not None:
                x.GetPrim().CreateAttribute(key, Sdf.ValueTypeNames.Float, custom=True).Set(float(val))
        self.groups[name] = {"color": color, "chunks": 0, "parts": 0, "part": None, "part_v": 0,
                             "vertices": 0, "triangles": 0}

    def _close_part(self, g):
        if g["part"] is not None:
            g["part"].GetRootLayer().Save()
            g["part"] = None
            g["part_v"] = 0

    def add(self, name: str, md: MeshData | None):
        from pxr import Sdf, UsdGeom

        if md is None or not len(md.faces):
            return
        g = self.groups[name]
        cname = f"chunk_{g['chunks']:04d}"
        if self.inline:
            _define_mesh(self.stage, f"/Tree/{name}/{cname}", md, g["color"])
        else:
            if g["part"] is None or g["part_v"] >= self.part_vertices:
                self._close_part(g)
                fname = f"{name}_{g['parts']:03d}.usdc"
                part = _new_stage(self.parts_dir / fname)
                p = UsdGeom.Xform.Define(part, "/Part")
                part.SetDefaultPrim(p.GetPrim())
                holder = UsdGeom.Xform.Define(self.stage, f"/Tree/{name}/part_{g['parts']:03d}")
                holder.GetPrim().GetPayloads().AddPayload(Sdf.Payload(f"./{self.parts_dir.name}/{fname}", Sdf.Path("/Part")))
                g["part"], g["parts"] = part, g["parts"] + 1
            _define_mesh(g["part"], f"/Part/{cname}", md, g["color"])
            g["part_v"] += md.n_vertices
        g["chunks"] += 1
        g["vertices"] += md.n_vertices
        g["triangles"] += len(md.faces)

    def close(self) -> dict:
        for g in self.groups.values():
            self._close_part(g)
        self.stage.GetRootLayer().Save()
        self.stage = None
        return {k: {"vertices": g["vertices"], "triangles": g["triangles"], "chunks": g["chunks"], "parts": g["parts"]}
                for k, g in self.groups.items()}


# -- timeline -------------------------------------------------------------------
def _encode_radius(history, birth, death, years, step, tol, block=100_000):
    """Radius per node over its life: float16 samples at its birth year, every
    ``step``-th calendar year and its last year, linearly interpolated in
    between.  A node whose interpolation error would exceed ``tol``
    (relative) is stored every year instead."""
    n = len(birth)
    end = np.where(death < 0, years, death - 1).astype(np.int64)
    birth = birth.astype(np.int64)
    counts = np.zeros(n, np.uint8)
    steps = np.full(n, step, np.uint8)
    values = []
    max_err = 0.0
    Y = np.arange(years + 1)[:, None]
    for b0 in range(0, n, block):
        b1 = min(n, b0 + block)
        H = np.zeros((years + 1, b1 - b0), np.float32)
        for y, h in enumerate(history):
            if len(h) > b0:
                k = min(len(h), b1)
                H[y, : k - b0] = h[b0:k]
        H16 = H.astype(np.float16).astype(np.float32)
        bi, ei = birth[b0:b1][None], end[b0:b1][None]
        valid = (Y >= bi) & (Y <= ei)

        def recon(k):
            g = (Y // k) * k
            lo = np.clip(np.maximum(bi, g), 0, years)
            hi = np.clip(np.minimum(ei, g + k), 0, years)
            hlo = np.take_along_axis(H16, lo, 0)
            hhi = np.take_along_axis(H16, hi, 0)
            frac = np.where(hi > lo, (Y - lo) / np.maximum(hi - lo, 1), 0.0)
            return hlo + (hhi - hlo) * frac

        rel = np.where(valid, np.abs(recon(step) - H) / np.maximum(H, 1e-9), 0.0)
        err = rel.max(0)
        st = np.where(err <= tol, step, 1).astype(np.uint8)
        rel1 = np.where(valid, np.abs(H16 - H) / np.maximum(H, 1e-9), 0.0).max(0)
        max_err = max(max_err, float(np.where(st == step, err, rel1).max(initial=0.0)))
        M = valid & ((Y == bi) | (Y == ei) | (Y % st[None] == 0))
        counts[b0:b1] = M.sum(0)
        steps[b0:b1] = st
        values.append(H16.T[M.T].astype(np.float16))
    return {"radius": np.concatenate(values) if values else np.zeros(0, np.float16),
            "radius_count": counts, "radius_step": steps}, max_err


def _rings(prefix, tree, history, years, min_radius=0.01):
    """Yearly ring widths (m, float32) of every wood node (radius at least
    ``min_radius`` at its last year): one value per year it lived, the
    growth of its radius that year, concatenated in node order."""
    n = tree.n
    death = tree.death[:n].astype(np.int64)
    birth = tree.birth[:n].astype(np.int64)
    last = np.where(death < 0, years, death - 1)
    r_last = np.zeros(n)
    for y in np.unique(last).tolist():
        idx = np.nonzero(last == y)[0]
        h = history[y]
        ok = idx < len(h)
        r_last[idx[ok]] = h[idx[ok]]
    wood = np.nonzero(r_last >= min_radius)[0]
    widths, counts = [], []
    for i in wood.tolist():
        ys = np.arange(birth[i], last[i] + 1)
        r = np.array([history[y][i] for y in ys], np.float64)
        w = np.diff(np.r_[0.0, r])
        widths.append(w.astype(np.float32))
        counts.append(len(w))
    return {f"{prefix}ring_node": wood.astype(np.int32), f"{prefix}ring_count": np.asarray(counts, np.int16),
            f"{prefix}ring_width_m": np.concatenate(widths) if widths else np.zeros(0, np.float32)}


def _node_arrays(prefix, tree, history, years, step, tol):
    n = tree.n
    birth = tree.birth[:n].astype(np.int16)
    death = tree.death[:n].astype(np.int16)
    enc, err = _encode_radius(history, birth, death, years, step, tol)
    out = {
        f"{prefix}parent": tree.parent[:n].astype(np.int32),
        f"{prefix}birth_year": birth,
        f"{prefix}death_year": death,
        f"{prefix}branch_order": tree.order[:n].astype(np.int8),
        f"{prefix}axis": tree.axis[:n].astype(np.int32),
        f"{prefix}is_lateral": tree.is_lateral[:n].astype(np.uint8),
        f"{prefix}position": tree.pos[:n].astype(np.float32),
    }
    out.update({prefix + k: v for k, v in enc.items()})
    return out, err


def write_timeline(path: Path, model, metadata: dict, radius_step: int = 5, radius_tolerance: float = 0.02):
    """``timeline.npz`` (arrays) + ``timeline.json`` (header describing them).

    ``path`` is the header (.json); the arrays go next to it with the same
    stem and .npz."""
    path = Path(path)
    years = model.year
    T = model.tree
    arrays, err_s = _node_arrays("shoot_", T, model.radius_history, years, radius_step, radius_tolerance)
    # branches bend over the years: crown positions at keyframe years, as
    # float16 offsets from the final position
    keys = sorted(model.keyframes)
    disp, counts, kf_err = [], [], 0.0
    for k in keys:
        kf = model.keyframes[k]
        d = kf - T.pos[: len(kf)].astype(np.float32)
        d16 = d.astype(np.float16)
        kf_err = max(kf_err, float(np.abs(d16.astype(np.float32) - d).max(initial=0.0)))
        disp.append(d16)
        counts.append(len(kf))
    arrays["shoot_keyframe_years"] = np.asarray(keys, np.int16)
    arrays["shoot_keyframe_count"] = np.asarray(counts, np.int32)
    arrays["shoot_keyframe_offset"] = np.concatenate(disp) if disp else np.zeros((0, 3), np.float16)
    arrays["shoot_hanging_final"] = (T.dir[: T.n, 2] < -0.5).astype(np.uint8)
    sp = model.spurs
    arrays["spur_node"] = np.asarray(sp.node, np.int32)
    arrays["spur_birth_year"] = np.asarray(sp.birth, np.int16)
    arrays["spur_death_year"] = np.asarray(sp.death, np.int16)
    la, lma = model.spur_traits()
    arrays["spur_leaf_area_m2"] = np.asarray(la, np.float32)
    arrays["spur_lma_g_m2"] = np.asarray(lma, np.float32)
    arrays["shoot_leaf_area_m2"] = np.where(T.leaf_size[: T.n] > 0, T.leaf_size[: T.n], model.light.leaf_area).astype(np.float32)
    arrays["shoot_lma_g_m2"] = T.lma[: T.n].astype(np.float32)
    arrays.update(_rings("shoot_", T, model.radius_history, years))
    err_r = 0.0
    if model.roots is not None:
        R = model.roots
        ra, err_r = _node_arrays("root_", R.tree, R.radius_history, years, radius_step, radius_tolerance)
        arrays.update(ra)
        arrays["root_kind"] = R.kind[R.tree.axis[: R.tree.n]].astype(np.int8)
        arrays.update(_rings("root_", R.tree, R.radius_history, years))
    npz = path.with_suffix(".npz")
    np.savez_compressed(npz, **arrays)
    header = {
        "format": "treegen.timeline/3",
        **metadata,
        "years": years,
        "data_file": npz.name,
        "units": {"length": "m", "up_axis": "Z", "frame": "x east, y north, z up (ground at z = 0)"},
        "arrays": {k: {"dtype": str(v.dtype), "shape": list(v.shape)} for k, v in arrays.items()},
        "conventions": {
            "prefixes": "shoot_* = crown, root_* = root system (same columns); root node 0 is the root collar",
            "node": "node i is the distal end of internode parent[i] -> i; node 0 is the base; parent -1 = none",
            "death_year": "-1 = alive at the final year; otherwise the first year the node is absent",
            "position": "final position (float32 xyz)",
            "radius": "node i has radius_count[i] float16 samples (concatenated in node order, starting at "
                      "cumsum(radius_count)[i-1]) at years: birth_year[i], every year y with "
                      "y % radius_step[i] == 0 strictly inside its life, and its last year (final year if "
                      "alive, else death_year - 1); interpolate linearly in between",
            "keyframes": "shoot_keyframe_offset holds, per keyframe year in order, shoot_keyframe_count[k] "
                         "rows of float16 xyz offsets of nodes 0..count-1 from their final position",
            "spurs": "short shoots (leaf/catkin attachment points) at crown node positions, with the leaf area "
                     "(m2 per leaf) and LMA (g m-2) of their last season",
            "leaves": "shoot_leaf_area_m2 / shoot_lma_g_m2: size and LMA of the leaves a node carries (sun leaves "
                      "smaller and thicker)",
            "rings": "<prefix>ring_node lists the wood nodes (radius >= 1 cm); each has ring_count yearly ring widths "
                     "(m) from its birth year, concatenated in that order in ring_width_m (the first is its first "
                     "year's radius)",
            "root_kind": "0 taproot, 1 lateral, 2 sinker; depth below ground = -z of position",
            "replay": "show node i in year y if birth_year <= y and (death_year < 0 or y < death_year); mesh "
                      "vertices carry node_id, so scale their ring offset by radius(y) / final radius",
        },
        "radius_encoding": {
            "keyframe_step_years": radius_step,
            "tolerance_relative": radius_tolerance,
            "max_relative_error_shoots": round(err_s, 5),
            "max_relative_error_roots": round(err_r, 5),
            "nodes_stored_every_year": int((arrays["shoot_radius_step"] == 1).sum()
                                           + (arrays.get("root_radius_step", np.zeros(0)) == 1).sum()),
        },
        "keyframe_max_abs_error_m": round(kf_err, 6),
    }
    path.write_text(json.dumps(header, indent=1), encoding="utf-8")
    return header


class Timeline:
    """Reader for timeline.json + timeline.npz."""

    def __init__(self, path):
        path = Path(path)
        self.header = json.loads(path.read_text(encoding="utf-8"))
        with np.load(path.with_name(self.header["data_file"])) as z:
            self.a = {k: z[k] for k in z.files}
        self.years = int(self.header["years"])
        self._samples = {}

    def __getitem__(self, key):
        return self.a[key]

    def _decode(self, prefix):
        if prefix not in self._samples:
            b = self.a[prefix + "birth_year"].astype(np.int64)
            d = self.a[prefix + "death_year"].astype(np.int64)
            e = np.where(d < 0, self.years, d - 1)
            st = self.a[prefix + "radius_step"].astype(np.int64)
            cnt = self.a[prefix + "radius_count"].astype(np.int64)
            node = np.repeat(np.arange(len(b)), cnt)
            # sample years: walk each node's grid
            Y = np.arange(self.years + 1)[None, :]
            M = (Y >= b[:, None]) & (Y <= e[:, None]) & ((Y == b[:, None]) | (Y == e[:, None]) | (Y % st[:, None] == 0))
            year = np.nonzero(M)[1]
            self._samples[prefix] = (node, year, self.a[prefix + "radius"].astype(np.float32))
        return self._samples[prefix]

    def radius_at(self, year: int, prefix: str = "shoot_") -> np.ndarray:
        """Radius of every node at the end of ``year`` (0 where absent)."""
        node, yr, val = self._decode(prefix)
        n = len(self.a[prefix + "birth_year"])
        key = node * 1024 + yr
        q = np.arange(n) * 1024 + year
        i = np.clip(np.searchsorted(key, q, side="right") - 1, 0, len(key) - 1)
        j = np.clip(i + 1, 0, len(key) - 1)
        ok = (node[i] == np.arange(n)) & (yr[i] <= year)
        same = ok & (node[j] == np.arange(n)) & (yr[j] > yr[i])
        f = np.where(same, (year - yr[i]) / np.maximum(yr[j] - yr[i], 1), 0.0)
        r = val[i] + (val[j] - val[i]) * f
        b = self.a[prefix + "birth_year"]
        d = self.a[prefix + "death_year"]
        present = ok & (b <= year) & ((d < 0) | (year < d))
        return np.where(present, r, 0.0).astype(np.float32)

    def positions_at(self, year: int) -> np.ndarray:
        """Crown node positions at the nearest keyframe at or before ``year``
        (final positions for nodes born later)."""
        pos = self.a["shoot_position"].copy()
        years = self.a["shoot_keyframe_years"]
        counts = self.a["shoot_keyframe_count"]
        offs = np.r_[0, np.cumsum(counts)]
        k = np.nonzero(years <= year)[0]
        if k.size:
            k = int(k[-1])
            c = int(counts[k])
            pos[:c] += self.a["shoot_keyframe_offset"][offs[k]:offs[k] + c].astype(np.float32)
        return pos


# -- stats ----------------------------------------------------------------------
def write_stats(path: Path, model, metadata: dict, reference: dict, anchorage: dict | None = None):
    doc = {
        "format": "treegen.stats/1",
        **metadata,
        "units": {"height": "m", "dbh": "cm (diameter at 1.3 m)", "crown_width": "m"},
        "definitions": {
            "crown_width_m": "mean of the east-west and north-south extents of living wood",
            "crown_projected_diameter_m": "diameter of the circle with the convex-hull area of the crown projection",
            "branches_by_order": "living axes per branch order (0 = trunk)",
            "crown_base_height_m": "lowest living first-order limb carrying at least 0.5 % of the leaves",
            "crown_ratio": "(height - crown base) / height",
            "mean_hanging_twig_length_m": "mean length of the hanging run (internodes > 30 deg below horizontal) "
                                          "ending at each shoot tip, over runs of at least 0.2 m",
            "water": "midday water status: transpiration, collar and lowest leaf water potential, mean "
                     "stomatal opening, share of carbon sent to the roots",
            "roots": "root length, depth (max, 90 % of length), share in the top 30/50 cm, lateral spread",
            "scaffold": "living first-order limbs: count over 5 / 10 cm base diameter, largest limb-to-trunk "
                        "diameter ratio, leaf share of the 5 biggest limbs, leaf area by height decile and by "
                        "distance from the trunk relative to the crown radius at that height",
        },
        "per_year": model.stats,
        "reference": reference,
        "anchorage": anchorage,
    }
    Path(path).write_text(json.dumps(doc, indent=1, allow_nan=False), encoding="utf-8")
