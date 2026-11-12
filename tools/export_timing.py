"""What an export costs, age by age: seconds in geometry, in baking textures and in writing them, and the files' sizes, for the
Unreal target (tools/game_export.py --target unreal) and the public exports (cambium export: glb, the plain exporter, and usd).
Measures only: timers wrap the exporters' functions from outside, so one tool times any checkout's code (--code), and old and new
code run turn about in one job, under the same load, and are compared file by file.  Server only.

    python tools/export_timing.py run --label node_qx_a                               # this checkout
    python tools/export_timing.py run --label node_qx_b --code ../repo_abc1234,.      # old then new, and what differs between them
    python tools/export_timing.py run --label node_qx_c --code ../repo_abc1234,. --quick   # and the new code's geometry-only export
    python tools/export_timing.py table out/bench/ensemble/node_qx_b

A tree is grown once (--modes stand,open; to the oldest of --ages, its leaves read at each) and kept in <label>/state, or in --state
from an earlier run: growth is never inside a timer.  --drop-state deletes the trees this run grew once it has used them (0.3 to
0.6 GB each at 60); a tree that was there already is never deleted.  What is run on it (--whats):

    unreal   tools/game_export.py's export for Unreal: .gltf, .bin and PNG maps, every level, summer
    glb      what `cambium export --format glb` runs once the tree is grown (Tree.export): .glb files with their maps inside
    usd      what `cambium export --format usd` runs (Tree.export): the research meshes, no maps; a tree grown to each age
    command  the `cambium export` command itself, growth and all, a stand tree at the first age: its time is growth plus `glb`
    history  the growth history files (timeline, stats), written by each checkout's code from the same tree, to compare
    levels   the stand tree's first age for Unreal, then each PNG it wrote put through every compression level: seconds and bytes

Compared between two checkouts: every map's decoded pixels, every mesh buffer (positions, normals, UVs, indices, every level),
every other file's content less run metadata.  Each export is hashed and deleted by the process that wrote it, so the disk never
holds two.  An export that fails is a row saying FAILED, and the job goes on; for `usd` each age is a row of its own, and only the
ages both checkouts wrote are compared.  Up to 2d33997 `usd` failed on the open-grown seed-1 tree ("axis chains are not
contiguous", from the mesh of its shed branches; tests/test_shed_branches.py).  Each `usd` export is also read back before it is
deleted (usd_counts): the points and faces of every group in the .usdc files against the plain .glb of the same group, and whether
every shed branch is in the mesh.  Results go to out/bench/ensemble/<label>/, where tools/node/fetch.sh looks.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import io
import json
import os
import pickle
import shutil
import struct
import subprocess
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "out" / "bench" / "ensemble"
FLOOR_GB = 12.0   # of free disk: nothing is exported below it
SPECIES, ENVIRONMENT = "betula_pendula", "sweden_open_field"

# What each timed function counts as.  A time goes to the innermost one running: a mesh written from inside a bake is geometry.
PARTS = {
    "geometry": "game.crown_mesh game.reduced_radius_threshold game.wood_arrays game.blades_arrays game.leaf_cards game._tangents "
                "gu.tree_meshes gu.sink_roots gu.split_roots gu.root_flows gu.root_arrays gu.root_radii gu.stem_goes_down gu.shape_stem "
                "gu.stem_edges gu.blade_mesh gu.card_mesh gu.hang_leaves gu.wind_flex gu.seat_sheets gu._bark_mesh gu._root_mesh "
                "ap.leaf_instances ap.peel_strips ap.add_bark_radius GameGLB.add_mesh GameGLB.write GameGLB.write_gltf cli.skeleton "
                "cli.export_all ge.shoot_arrays",
    "bake": "tx.make_tiles tx.leaf_blade tx.leaf_card_atlas tx.strip_texture tx.push_pull_fill tx.bake_stem tx.bake_branch_atlas tx.finish game.bake_wood game.far_sheets "
            "game.far_cards game.add_wood gu.scale_tiles_to_albedo gu.split_detail gu.stain_foot gu.moss_on_stem gu.root_atlas "
            "gu.leaf_atlas gu.card_atlas gu.strip_atlas gu.pot",
    "write": "game._encoded_bark game._leaf_material game.add_strips game.encode_image gu._bark_maps gu.Maps.write gu._write_png",
    "check": "ge.check_files ge.continuity",
    "outside": "pickle.load tree._grow",
}
TEXTURES = ("bake", "write", "png", "jpeg")
METADATA = {"run_manifest", "file_mb", "files_mb", "timings", "peak_memory"}


# -- one export, in a process of its own, on one checkout's code ------------------------------------------------------------
class Clock:
    """Seconds by part, and by function.  Time goes to the top of a stack; nothing counts until start()."""

    def __init__(self):
        self.stack, self.by, self.fn, self.t = [("other", "other")], defaultdict(float), defaultdict(float), None

    def start(self):
        self.t = time.perf_counter()

    def stop(self):
        self.tick()
        self.t = None

    def tick(self):
        now = time.perf_counter()
        if self.t is not None:
            self.by[self.stack[-1][0]] += now - self.t
            self.fn[self.stack[-1][1]] += now - self.t
            self.t = now

    def wrap(self, owner, name, part, on_done=None, label=None):
        fn = getattr(owner, name)

        @functools.wraps(fn)
        def timed(*args, **kwargs):
            self.tick()
            before = dict(self.by)
            self.stack.append((part(args) if callable(part) else part, label or name))
            try:
                return fn(*args, **kwargs)
            finally:
                self.tick()
                self.stack.pop()
                if on_done:
                    on_done(args, self.since(before))
        setattr(owner, name, timed)

    def since(self, before: dict) -> dict:
        return {k: round(v - before.get(k, 0.0), 3) for k, v in self.by.items() if k != "outside" and v - before.get(k, 0.0) > 0.0005}


def glb_json(path: Path) -> dict:
    """The JSON of a .glb or a .gltf, without reading its buffers."""
    if path.suffix == ".gltf":
        return json.loads(path.read_text(encoding="utf-8"))
    with open(path, "rb") as f:
        f.seek(12)
        n, _ = struct.unpack("<I4s", f.read(8))
        return json.loads(f.read(n))


def sizes(folder: Path, tag: str = "") -> dict:
    """Bytes written for one age (files with ``tag`` in their name): meshes, PNG and JPEG maps, in files or inside a .glb."""
    out, tris = defaultdict(int), {}
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or tag not in p.name:
            continue
        n = p.stat().st_size
        if p.suffix in (".glb", ".gltf"):
            doc = glb_json(p)
            for img in doc.get("images", []):
                if "bufferView" in img:
                    m = doc["bufferViews"][img["bufferView"]]["byteLength"]
                    out["png" if img["mimeType"] == "image/png" else "jpeg"] += m
                    n -= m
            tris[p.name] = sum(doc["accessors"][pr["indices"]]["count"] for me in doc.get("meshes", []) for pr in me["primitives"]) // 3
        out["png" if p.suffix == ".png" else "mesh" if p.suffix in (".glb", ".gltf", ".bin", ".usdc") else "other"] += n
    return {"bytes": dict(out), "triangles": tris}


# each group of a USD file, and the plain .glb that `cli.export_all` writes from the same chunks
USD_GROUPS = {"tree.usdc": {"Living": "tree.glb", "Roots": "tree_roots.glb", "PrunedHistory": "tree_pruned.glb"},
              "tree_reduced.usdc": {"Living": "tree_reduced.glb", "Roots": "tree_reduced_roots.glb"}}


def usd_counts(folder: Path, model) -> dict:
    """A USD export read back from its files.  'groups': per group, the points and faces of every mesh under it in the .usdc (its
    parts loaded) and those of its plain .glb.  'shed': how many shed branches the tree has, how many of them the mesh holds, living
    nodes in it (there should be none), and how many shed branches the mesher drew as the stem's own continuation
    (mesh.continue_trunk: such a branch gets a flat cap at its base, and the stem's swelling if it is near the ground)."""
    import numpy as np
    from pxr import Usd, UsdGeom
    from treegen import mesh

    groups, in_mesh = {}, [np.zeros(0, np.int64)]
    for usd, pairs in USD_GROUPS.items():
        counts = {g: {"points": 0, "faces": 0, "glb_points": 0, "glb_faces": 0} for g in pairs}
        stage = Usd.Stage.Open(str(folder / usd))
        for prim in stage.Traverse():
            if prim.IsA(UsdGeom.Mesh):
                g = prim.GetPath().pathString.split("/")[2]
                counts[g]["points"] += len(UsdGeom.Mesh(prim).GetPointsAttr().Get())
                counts[g]["faces"] += len(UsdGeom.Mesh(prim).GetFaceVertexCountsAttr().Get())
                if g == "PrunedHistory":
                    in_mesh.append(np.asarray(UsdGeom.PrimvarsAPI(prim).GetPrimvar("node_id").Get(), np.int64))
        for g, name in pairs.items():
            if (folder / name).exists():       # a group with nothing in it has no .glb
                doc = glb_json(folder / name)
                prim = doc["meshes"][0]["primitives"][0]
                counts[g]["glb_points"] = doc["accessors"][prim["attributes"]["POSITION"]]["count"]
                counts[g]["glb_faces"] = doc["accessors"][prim["indices"]]["count"] // 3
            groups[("reduced " if "reduced" in usd else "") + g] = counts[g]
    T = model.tree
    axis = np.asarray(T.axis[: T.n])
    dead = np.asarray(T.death[: T.n]) >= 0
    dead[0] = False
    in_mesh = np.unique(np.concatenate(in_mesh))
    view = np.asarray(mesh.continue_trunk(T, dead, None).axis[: T.n])
    shed = {"nodes": int(dead.sum()), "branches": int(np.unique(axis[dead]).size), "branches_in_mesh": int(np.unique(axis[in_mesh]).size),
            "all_in_mesh": bool(np.array_equal(np.unique(axis[dead]), np.unique(axis[in_mesh]))), "living_nodes_in_mesh": int((~dead[in_mesh]).sum()),
            "drawn_as_stem": int(np.unique(axis[dead & (view == 0) & (axis != 0)]).size)}
    return {"groups": groups, "shed": shed, "same_as_glb": all(c["points"] == c["glb_points"] and c["faces"] == c["glb_faces"] for c in groups.values())}


def png_levels(folder: Path) -> dict:
    """Every PNG under a folder through each of zlib's levels: seconds, bytes, and whether it decodes to the same pixels."""
    import numpy as np
    from PIL import Image

    out = {str(k): {"seconds": 0.0, "bytes": 0, "same_pixels": True} for k in (0, 1, 2, 3, 4, 5, 6, 9)}
    files = sorted(folder.rglob("*.png"))
    for p in files:
        pixels = np.asarray(Image.open(p))
        for level, row in out.items():
            buf = io.BytesIO()
            t0 = time.perf_counter()
            Image.fromarray(pixels).save(buf, "PNG", compress_level=int(level))
            row["seconds"] += time.perf_counter() - t0
            row["bytes"] += buf.tell()
            row["same_pixels"] &= bool(np.array_equal(np.asarray(Image.open(io.BytesIO(buf.getvalue()))), pixels))
    return {"files": len(files), "levels": out}


def one(a) -> None:
    code = Path(a.code).resolve()
    sys.path[0] = str(code)    # in place of this file's own folder: every import below is the checkout's
    os.chdir(code)
    import numpy  # noqa: F401
    import treegen
    assert Path(treegen.__file__).resolve().parent.parent == code, treegen.__file__
    import PIL.Image
    from cambium import _engine, _tree as tree
    from cambium._species import species_file
    from treegen import appearance as ap, checkpoint, export, game, game_unreal as gu, textures as tx
    from treegen.environment import make_environment, make_soil
    from treegen.export import GameGLB
    from treegen.growth import GrowthModel
    from treegen.params import load_environment, load_species

    ge, cli = _engine.load("game_export"), _engine.load("cli")
    ages = sorted(int(x) for x in a.ages.split(","))
    state, out, stand = Path(a.state), Path(a.out), a.mode == "stand"
    at = lambda age: state.with_name(f"{state.stem}_at{age:03d}.pkl")  # noqa: E731

    if a.what == "grow":
        # as game_export.grow_with_leaves, and the tree as it stood at each earlier age kept too (for usd, which writes a tree at its own age)
        sp, _ = load_species(SPECIES)
        env_p, _ = load_environment(ENVIRONMENT)
        model = GrowthModel(sp, make_environment(env_p), a.seed, stand=stand, soil=make_soil(env_p))
        snaps, t0 = {}, time.time()
        for age in ages:
            while model.year < age:
                model.step()
            snaps[age] = ap.leaf_snapshot(model, age)
            if age < ages[-1]:
                checkpoint.save_model(model, at(age))
            print(f"{a.mode} tree at {age}: {model.stats[-1]['height_m']:.1f} m, {int((model.tree.death[: model.tree.n] < 0).sum())} living nodes, {time.time() - t0:.0f} s", flush=True)
        model.run(0)
        state.parent.mkdir(parents=True, exist_ok=True)
        with open(state, "wb") as f:
            pickle.dump({"model": model, "snaps": snaps}, f, protocol=pickle.HIGHEST_PROTOCOL)
        return

    clock, rows = Clock(), {}
    names = {"game": game, "gu": gu, "tx": tx, "ap": ap, "GameGLB": GameGLB, "cli": cli, "ge": ge, "pickle": pickle, "tree": tree}
    for part, items in PARTS.items():
        for item in items.split():
            *owners, name = item.split(".")
            owner = functools.reduce(getattr, owners[1:], names[owners[0]])
            if hasattr(owner, name):
                clock.wrap(owner, name, part, label=item)
    clock.wrap(PIL.Image.Image, "save", lambda args: "jpeg" if "JPEG" in args[2:3] else "png", label="PIL save")
    clock.wrap(ge, "export_stage", "other", lambda args, took: rows.__setitem__(int(args[4]), took), "the stage's own lines")
    clock.wrap(gu, "export_stage", "other", lambda args, took: rows.__setitem__(int(args[1]), took), "the stage's own lines")

    def kept(age: int):
        """The tree as `cambium export` has it once grown: to its last age, or as it stood at an earlier one."""
        if age == ages[-1]:
            with open(state, "rb") as f:
                saved = pickle.load(f)
            model, snaps = saved["model"], saved["snaps"]
        else:
            model, snaps = checkpoint.load_model(at(age)), {}
            model.run(0)
        return tree.Tree(model, model.sp, species_file=species_file(SPECIES), environment_file=_engine.environment_file(ENVIRONMENT), seed=a.seed,
                         stand=stand, settings=[], snapshots=snaps)

    plain = {} if a.textures else {"textures": False}
    load0 = os.getloadavg()[0]
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    tags = {age: f"age{age:03d}" for age in ages}
    extra = {}
    if a.what in ("unreal", "levels"):
        if a.what == "levels":
            ages = ages[:1]
        clock.start()
        ge.main_export(argparse.Namespace(ages=",".join(str(x) for x in ages), seasons="summer", out=str(out), state=str(state), species=SPECIES, seed=a.seed,
                                          environment=ENVIRONMENT, stand=stand, set=[], budget=[], look=[], levels="", target="unreal", **plain))
        if a.what == "levels":
            clock.stop()
            extra["png_levels"] = png_levels(out)
    elif a.what == "glb":
        t = kept(ages[-1])
        clock.start()
        t.export(out, format="glb", ages=ages, seasons=["summer"], log=lambda s: print(s, flush=True), **plain)
    elif a.what == "usd":
        tags = {age: "" for age in ages}
        for age in ages:
            t = kept(age)
            clock.start()
            before = dict(clock.by)
            try:
                t.export(out / f"age{age:03d}", format="usd")
            except Exception:     # an age that fails is a finding of its own: it's recorded, and the other ages are still written
                traceback.print_exc()
                extra.setdefault("failed_ages", []).append(age)
                shutil.rmtree(out / f"age{age:03d}", ignore_errors=True)
                continue
            finally:
                clock.stop()
            rows[age] = clock.since(before)
            extra.setdefault("usd", {})[str(age)] = usd_counts(out / f"age{age:03d}", t.model)
    elif a.what == "command":
        from cambium.cli import main
        ages = ages[:1]
        clock.start()
        code_ = main(["export", "--seed", str(a.seed), "--ages", str(ages[0]), "--out", str(out)] + (["--forest"] if stand else []) + ([] if a.textures else ["--no-textures"]))
        assert code_ == 0, code_
    elif a.what == "history":
        t = kept(ages[-1])
        clock.start()
        export.write_timeline(out / "timeline.json", t.model, t.metadata())
        t.save(out)
    clock.stop()
    for age in ages:
        if age in rows:
            rows[age] = {"seconds": rows[age], **sizes(out / f"age{age:03d}" if a.what == "usd" else out, tags.get(age, ""))}
    commit = (code / "COMMIT").read_text().strip() if (code / "COMMIT").exists() else "checkout"
    doc = {"what": a.what, "mode": a.mode, "textures": a.textures, "code": commit, "seconds": clock.since({}), "wall_s": round(sum(clock.since({}).values()), 1),
           "outside_s": round(clock.by.get("outside", 0.0), 1), "rows": {str(k): v for k, v in sorted(rows.items())}, "all": sizes(out),
           "functions": {k: round(v, 2) for k, v in sorted(clock.fn.items(), key=lambda kv: -kv[1]) if v >= 0.05},
           "load": [round(load0, 1), round(os.getloadavg()[0], 1)], "peak_mb": cli.peak_memory_mb(), **extra, "digest": digest(out)}
    Path(a.json).write_text(json.dumps(doc), encoding="utf-8")
    shutil.rmtree(out, ignore_errors=True)     # its hashes are kept; the files, up to gigabytes, are not
    print(f"{a.mode} {a.what} on {commit}: {doc['wall_s']} s, and {doc['outside_s']} s reading or growing the tree; load {doc['load']}", flush=True)


# -- what an export holds, and what differs between two ---------------------------------------------------------------------
def _plain(o):
    """Without run metadata.  Unreal's files hold their extras as text, so text that is JSON is read."""
    if isinstance(o, dict):
        return {k: _plain(v) for k, v in o.items() if k not in METADATA}
    if isinstance(o, list):
        return [_plain(v) for v in o]
    if isinstance(o, str) and o[:1] in "{[":
        try:
            return _plain(json.loads(o))
        except ValueError:
            return o
    return o


def _sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, (bytes, bytearray, memoryview)) else json.dumps(p, sort_keys=True).encode("utf-8"))
    return h.hexdigest()[:24]


def _pixels(data) -> str:
    import numpy as np
    from PIL import Image

    im = Image.open(io.BytesIO(data))
    return _sha([im.mode, list(im.size)], np.asarray(im).tobytes())


def digest(folder: Path) -> dict:
    """What an export holds, file by file, as hashes, so that two exports are compared with neither kept on disk.  'bytes': the file
    as it is.  'pixels': a PNG's mode, size and decoded pixels; for a .glb, those of each image in it (a JPEG by its bytes).
    'buffers': each accessor's bytes, in order: positions, normals, tangents, UVs, colours, attributes, indices.  'meshes': the meshes'
    names, attributes and accessor layouts.  'json': the JSON less run metadata and less where things lie in a buffer.  'arrays':
    an .npz's arrays."""
    import numpy as np
    from treegen.export import read_glb

    out = {}
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        data = p.read_bytes()
        d = {"bytes": _sha(data)}
        if p.suffix == ".png":
            d["pixels"] = _pixels(data)
        elif p.suffix == ".json":
            d["json"] = _sha(_plain(json.loads(data)))
        elif p.suffix == ".npz":
            with np.load(p) as z:
                d["arrays"] = _sha(*[x for k in sorted(z.files) for x in ([k, str(z[k].dtype), list(z[k].shape)], z[k].tobytes())])
        elif p.suffix in (".glb", ".gltf"):
            del data
            doc, blob = read_glb(p)
            views = doc.pop("bufferViews", [])
            doc.pop("buffers", None)
            take = lambda v: memoryview(blob)[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]  # noqa: E731
            d["buffers"] = [_sha(take(views[acc["bufferView"]])) for acc in doc.get("accessors", [])]
            d["meshes"] = _sha([[m.get("name"), [[pr["attributes"], pr["indices"]] for pr in m["primitives"]]] for m in doc.get("meshes", [])],
                               [{k: v for k, v in acc.items() if k != "bufferView"} for acc in doc.get("accessors", [])])
            inside = [(img["mimeType"], take(views[img["bufferView"]])) for img in doc.get("images", []) if "bufferView" in img]
            if inside:
                d["pixels"] = _sha([_pixels(x) if mime == "image/png" else _sha(x) for mime, x in inside])
            doc["views"] = [{k: v for k, v in view.items() if k != "byteOffset" and (k != "byteLength" or "target" in view)} for view in views]
            d["json"] = _sha(_plain(doc))
        out[p.relative_to(folder).as_posix()] = d
    return out


def same(a: dict, b: dict) -> str:
    """Two files' digests.  'bytes': the same file; 'content': the same once decoded and less run metadata; or what differs."""
    if a["bytes"] == b["bytes"]:
        return "bytes"
    keys = (set(a) | set(b)) - {"bytes"}
    differ = sorted(k for k in keys if a.get(k) != b.get(k))
    return "content" if keys and not differ else ("DIFFERENT " + ", ".join(differ)).strip()


def compare(a: dict, b: dict) -> dict:
    """Two exports' digests, file by file."""
    out = {"files": len(set(a) & set(b)), "in_one_only": sorted(set(a) ^ set(b)), "by_kind": {}, "different": []}
    for rel in sorted(set(a) & set(b)):
        how = same(a[rel], b[rel])
        kind = out["by_kind"].setdefault(Path(rel).suffix, {})
        kind[how.split()[0]] = kind.get(how.split()[0], 0) + 1
        if how.startswith("DIFFERENT"):
            out["different"].append(f"{rel}: {how}")
    out["identical"] = not out["different"] and not out["in_one_only"]
    return out


def compare_geometry(full: dict, quick: dict) -> dict:
    """A geometry-only export against the full one: every mesh file it wrote must hold the same meshes and buffers, accessor by accessor."""
    files = [rel for rel in sorted(quick) if "buffers" in quick[rel]]
    different = [rel for rel in files if rel not in full or any(quick[rel][k] != full[rel][k] for k in ("buffers", "meshes"))]
    return {"files": len(files), "accessors": sum(len(quick[rel]["buffers"]) for rel in files), "different": different,
            "not_written": sorted(rel for rel in full if "buffers" in full[rel] and rel not in quick), "identical": bool(files) and not different}


# -- the job ----------------------------------------------------------------------------------------------------------------
def run(a) -> int:
    out = BASE / a.label
    work, state_dir = out / "work", Path(a.state).resolve() if a.state else out / "state"
    out.mkdir(parents=True, exist_ok=True)
    codes = [Path(c).resolve() for c in a.code.split(",")]
    doc = {"label": a.label, "seed": a.seed, "ages": a.ages, "cores": os.cpu_count(), "runs": [], "compare": {}}

    def child(code: Path, what: str, mode: str, folder: Path, textures: bool = True) -> dict:
        free = shutil.disk_usage(out).free / 2 ** 30
        if free < FLOOR_GB:
            raise SystemExit(f"STOP: {free:.1f} GB of disk free, under {FLOOR_GB:.0f}; nothing more is exported")
        result = out / f"{folder.name}.json"
        cmd = [sys.executable, str(Path(__file__).resolve()), "one", "--code", str(code), "--what", what, "--mode", mode, "--seed", str(a.seed), "--ages", a.ages,
               "--state", str(state_dir / f"{mode}_s{a.seed}.pkl"), "--out", str(folder), "--json", str(result)] + ([] if textures else ["--no-textures"])
        if subprocess.run(cmd).returncode != 0:
            if what == "grow":
                raise SystemExit(f"growing the {mode} tree failed")
            # an export that fails is a finding: it's recorded, and the job goes on
            print(f"FAILED: {mode} {what} on {code.name}; its traceback is above", flush=True)
            shutil.rmtree(folder, ignore_errors=True)
            return {"what": what, "mode": mode, "textures": textures, "code": code.name, "failed": True}
        return json.loads(result.read_text(encoding="utf-8")) if what != "grow" else {}

    for mode in a.modes.split(","):
        grown = not (state_dir / f"{mode}_s{a.seed}.pkl").exists()
        if grown:
            child(codes[0], "grow", mode, work / "grow")
        for k, what in enumerate(a.whats.split(",")):
            if what in ("command", "levels") and mode != "stand":
                continue
            runs = {}
            for code in codes[-1:] if what == "levels" else codes if k % 2 == 0 else codes[::-1]:
                runs[code] = child(code, what, mode, work / f"{mode}_{what}_{code.name}")
            if a.quick and what in ("unreal", "glb", "command"):
                runs["quick"] = child(codes[-1], what, mode, work / f"{mode}_{what}_geometry_only", textures=False)
            if not any(r.get("failed") for r in runs.values()):
                if len(codes) == 2 and what != "levels":
                    # an age that failed on either code has nothing to compare: its row says so
                    skip = tuple(f"age{age:03d}/" for c in codes for age in runs[c].get("failed_ages", []))
                    old, new = ({rel: d for rel, d in runs[c]["digest"].items() if not rel.startswith(skip)} for c in codes)
                    if old or new or not skip:
                        doc["compare"][f"{mode} {what}"] = compare(old, new)
                if "quick" in runs:
                    doc["compare"][f"{mode} {what}: geometry only against full"] = compare_geometry(runs[codes[-1]]["digest"], runs["quick"]["digest"])
            for r in runs.values():
                r.pop("digest", None)     # each run's own .json keeps it
                doc["runs"].append(r)
            (out / "results.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
        if grown and a.drop_state:
            for p in state_dir.glob(f"{mode}_s{a.seed}*.pkl"):
                p.unlink()
    text = table(doc)
    (out / "table.md").write_text(text, encoding="utf-8")
    print(text)
    bad = [k for k, v in doc["compare"].items() if not v["identical"]] + [f"{r['mode']} {r['what']} failed on {r['code']}" for r in doc["runs"] if r.get("failed")]
    bad += [f"{r['mode']} usd at {age} failed on {r['code']}" for r in doc["runs"] for age in r.get("failed_ages", [])]
    bad += [f"{r['mode']} usd at {age} on {r['code']}: its counts" for r in doc["runs"] for age, u in (r.get("usd") or {}).items()
            if not (u["same_as_glb"] and u["shed"]["all_in_mesh"] and u["shed"]["living_nodes_in_mesh"] == 0)]
    print("COMPARED: " + ("nothing differs but PNG bytes and run metadata" if not bad else f"NOT SO: {bad}") if doc["compare"] or bad else "one checkout: nothing to compare")
    return 1 if bad else 0


def table(doc: dict) -> str:
    mb = lambda n: f"{n / 2 ** 20:.1f}"  # noqa: E731
    lines = ["| Tree | Export | Code | Age | All, s | Geometry, s | Baking textures, s | Writing textures, s | of that, PNG compression, s | Checks and the rest, s | "
             "Meshes, MB | PNG, MB | JPEG, MB | Triangles, nearest level | Load |", "|" + "---|" * 15]
    for r in doc["runs"]:
        name = r["what"] + ("" if r["textures"] else ", geometry only")
        if r.get("failed"):
            lines.append(f"| {r['mode']} | {name} | {r['code']} | FAILED |" + " |" * 11)
            continue
        lines += [f"| {r['mode']} | {name} | {r['code']} | {age}: FAILED |" + " |" * 11 for age in r.get("failed_ages", [])]
        rows = [(age, v["seconds"], v["bytes"], max(v["triangles"].values(), default=0)) for age, v in r["rows"].items()]
        rows.append(("whole export", r["seconds"], r["all"]["bytes"], ""))
        for age, s, b, tris in rows:
            total = sum(s.values())
            lines.append(f"| {r['mode']} | {name} | {r['code']} | {age} | {total:.1f} | {s.get('geometry', 0.0):.1f} | {s.get('bake', 0.0):.1f} | "
                         f"{sum(s.get(k, 0.0) for k in TEXTURES[1:]):.1f} | {s.get('png', 0.0):.1f} | {s.get('check', 0.0) + s.get('other', 0.0):.1f} | "
                         f"{mb(b.get('mesh', 0))} | {mb(b.get('png', 0))} | {mb(b.get('jpeg', 0))} | {tris} | {r['load'][0]}-{r['load'][1]} |")
    for r in doc["runs"]:
        if r.get("png_levels"):
            lines += ["", f"The {r['png_levels']['files']} PNG maps of the {r['mode']} tree's first age for Unreal, each put through every level:", "",
                      "| PNG level | Seconds | MB | The same pixels |", "|---|---|---|---|"]
            lines += [f"| {k} | {v['seconds']:.1f} | {mb(v['bytes'])} | {'yes' if v['same_pixels'] else 'NO'} |" for k, v in r["png_levels"]["levels"].items()]
    if any(r.get("usd") for r in doc["runs"]):
        pf = lambda c: f"{c['points']}, {c['faces']}"  # noqa: E731
        lines += ["", "Each USD export read back from its files (usd_counts): points and faces of each group in the .usdc.", "",
                  "| Tree | Code | Age | Living: points, faces | Roots | Shed branches | Reduced crown | Reduced roots | The .glb files hold the same counts | "
                  "Shed branches in the tree | of them in the mesh | Living nodes in the shed mesh | Shed branches drawn as stem |", "|" + "---|" * 13]
        for r in doc["runs"]:
            for age, u in (r.get("usd") or {}).items():
                g, s = u["groups"], u["shed"]
                lines.append(f"| {r['mode']} | {r['code']} | {age} | {pf(g['Living'])} | {pf(g['Roots'])} | {pf(g['PrunedHistory'])} | {pf(g['reduced Living'])} | "
                             f"{pf(g['reduced Roots'])} | {'yes' if u['same_as_glb'] else 'NO'} | {s['branches']} | {s['branches_in_mesh']}{'' if s['all_in_mesh'] else ' (NOT all)'} | "
                             f"{s['living_nodes_in_mesh']} | {s['drawn_as_stem']} |")
    lines.append("")
    for k, v in doc["compare"].items():
        lines.append(f"- {k}: {'IDENTICAL' if v['identical'] else 'DIFFERENT'}; {json.dumps({x: y for x, y in v.items() if x != 'identical'})}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap_.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    r.add_argument("--code", default=str(ROOT), help="one checkout, or two with a comma between: old,new")
    r.add_argument("--modes", default="stand,open")
    r.add_argument("--whats", default="unreal,glb,usd,command,history")
    r.add_argument("--quick", action="store_true", help="also the last checkout's geometry-only export, checked against its full one")
    r.add_argument("--state", default=None, help="a folder of trees kept by an earlier run")
    r.add_argument("--drop-state", action="store_true", help="delete the trees this run grew, once it has used them")
    o = sub.add_parser("one")
    for name in ("--code", "--what", "--mode", "--state", "--out", "--json"):
        o.add_argument(name, required=True)
    o.add_argument("--no-textures", dest="textures", action="store_false")
    for p in (r, o):
        p.add_argument("--seed", type=int, default=1)
        p.add_argument("--ages", default="30,50,60")
    t = sub.add_parser("table")
    t.add_argument("folder")
    a = ap_.parse_args()
    if a.command == "run":
        return run(a)
    if a.command == "one":
        one(a)
        return 0
    print(table(json.loads((Path(a.folder) / "results.json").read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
