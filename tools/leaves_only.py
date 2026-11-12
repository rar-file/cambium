"""Two exports of one tree, part by part: is anything but the leaves different?

Written for the day new leaves each spring became the default (appearance.leaves.each_year, 2026-11-12), when the pinned export
runs of tools/golden.py had to change and nothing else was allowed to.  A golden hash is one number for a whole file, and a file
with leaves in it holds the wood as well, so this opens the files:

    meshes   every mesh of every .glb and .gltf, by its name: each accessor's layout and bytes (positions, normals, tangents,
             UVs, colours, the per-vertex birth year, radius and node id, the indices), and its material's name
    maps     every image, inside a .glb or a .png of its own: its decoded pixels
    rest     each mesh file's materials and what is left of its JSON, and every other file: content less run metadata; in a
             .json file, each value that differs, by its path

A part is the leaves' if its name says so: the meshes leaves, leaf_cards and far_cards, and any map or material with "leaf" in
its name or "far" at its start.  The far level is a picture of the whole tree drawn from the near level's file, wood and leaves
together, so all of it counts as leaves here; that its wood is unchanged rests on the near file's wood being identical.  In a
manifest, a whole file's triangles, vertices, megabytes and bounds take the leaves in too, and so do the height and width the
game target gives a variant, which are its mesh's box; they are listed apart, and each level's triangles less its leaves are
compared as a number.

    # two recordings of tools/golden.py on one machine: the tracked one and a new one
    python tools/leaves_only.py recordings --label node_x --old ../repo_abc/out/bench/golden/node_a --new out/bench/golden/node_b \\
        --runs export30,unreal30,usd_open30 --timelapse export30,unreal30
    # any two export folders
    python tools/leaves_only.py folders OLD NEW

--timelapse: those golden runs are made again here with the export's --timelapse option, hashed as golden.py hashes them, and
must equal the old recording file by file: the option gives the leaves the exports had before.  Their files are deleted.
Exit 0 only if every difference is the leaves' and every --timelapse run is identical.  Only reads the two exports.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import golden  # noqa: E402

E = ROOT / "out" / "bench" / "ensemble"
LEAF_MESHES = ("leaves", "leaf_cards", "far_cards")
# a whole file's numbers in a manifest, which take its leaves in
WHOLE_FILE = ("triangles", "vertices", "file_mb", "within_budget", "bounds")
LEAF_KEYS = ("leaves", "leaf_area_represented_m2", "far_cards")
BYTES_OF = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
WIDTH_OF = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def is_leaf(name: str) -> bool:
    n = str(name).lower()
    return "leaf" in n or n.startswith("far")


def sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, (bytes, bytearray, memoryview)) else json.dumps(p, sort_keys=True).encode("utf-8"))
    return h.hexdigest()[:24]


def pixels(data: bytes) -> str:
    import numpy as np
    from PIL import Image

    im = Image.open(io.BytesIO(data))
    return sha([im.mode, list(im.size)], np.asarray(im).tobytes())


def plain(o):
    """Without run metadata, as tools/golden.py leaves it out.  The game target's files hold their extras as text: read where it is JSON."""
    if isinstance(o, dict):
        return {k: plain(v) for k, v in o.items() if k not in golden.METADATA_KEYS}
    if isinstance(o, list):
        return [plain(v) for v in o]
    if isinstance(o, str) and o[:1] in "{[":
        try:
            return plain(json.loads(o))
        except ValueError:
            return o
    return o


def accessor_bytes(doc: dict, blob, index: int):
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    start = view.get("byteOffset", 0)
    if "byteStride" in view:
        return memoryview(blob)[start:start + view["byteLength"]]
    start += acc.get("byteOffset", 0)
    return memoryview(blob)[start:start + acc["count"] * WIDTH_OF[acc["type"]] * BYTES_OF[acc["componentType"]]]


def mesh_file_parts(path: Path, rel: str) -> dict:
    """The parts of one .glb or .gltf: its meshes, the maps inside it, its materials, and the rest of its JSON."""
    from treegen.export import read_glb

    doc, blob = read_glb(path)
    images = doc.get("images", [])
    image_name = lambda i: images[i].get("name") or images[i].get("uri") or f"image {i}"  # noqa: E731
    texture_name = lambda t: image_name(doc["textures"][t]["source"])  # noqa: E731

    def named(o):
        """A material with each texture's number replaced by its image's name."""
        if isinstance(o, dict):
            return {k: (texture_name(v) if k == "index" and isinstance(v, int) else named(v)) for k, v in o.items()}
        return [named(v) for v in o] if isinstance(o, list) else o

    materials = doc.get("materials", [])
    out, seen = {}, {}
    for mesh in doc.get("meshes", []):
        name = mesh.get("name", "mesh")
        seen[name] = seen.get(name, 0) + 1
        key = name if seen[name] == 1 else f"{name} #{seen[name]}"
        hashed, vertices, triangles = [], 0, 0
        for prim in mesh["primitives"]:
            for attr, index in sorted(prim["attributes"].items()) + [("indices", prim["indices"])]:
                acc = doc["accessors"][index]
                hashed += [[attr, {k: v for k, v in acc.items() if k not in ("bufferView", "byteOffset")}], accessor_bytes(doc, blob, index)]
            hashed.append(["material", materials[prim["material"]].get("name") if "material" in prim else None])
            vertices += doc["accessors"][prim["attributes"]["POSITION"]]["count"]
            triangles += doc["accessors"][prim["indices"]]["count"] // 3
        out[f"{rel}: mesh {key}"] = {"kind": "mesh", "leaf": name in LEAF_MESHES, "sha": sha(*hashed), "vertices": vertices, "triangles": triangles}
    for i, img in enumerate(images):
        if "bufferView" in img:
            view = doc["bufferViews"][img["bufferView"]]
            data = bytes(memoryview(blob)[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]])
            out[f"{rel}: map {image_name(i)}"] = {"kind": "map", "leaf": is_leaf(image_name(i)), "sha": pixels(data)}
    for m in materials:
        out[f"{rel}: material {m.get('name')}"] = {"kind": "rest", "leaf": is_leaf(m.get("name", "")), "sha": sha(plain(named(m)))}
    rest = {k: v for k, v in doc.items() if k not in ("meshes", "accessors", "bufferViews", "buffers", "images", "textures", "samplers", "materials")}
    out[f"{rel}: scene, nodes and asset"] = {"kind": "rest", "leaf": False, "sha": sha(plain(rest))}
    return out


def flat(o, path=()) -> dict:
    if isinstance(o, dict):
        return {k: v for key, val in o.items() for k, v in flat(val, path + (str(key),)).items()}
    if isinstance(o, list):
        return {k: v for i, val in enumerate(o) for k, v in flat(val, path + (str(i),)).items()}
    return {path: o}


def parts(folder: Path) -> tuple:
    """(every part of an export, its .json files flattened), over the files tools/golden.py hashes and the .png maps it leaves out."""
    import numpy as np

    out, docs = {}, {}
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder).as_posix()
        if not p.is_file() or p.name in golden.SKIP_NAMES or p.suffix.lower() in (".log", ".tmp") or golden.SKIP_DIRS & set(p.relative_to(folder).parts):
            continue
        suffix = p.suffix.lower()
        if suffix in (".glb", ".gltf"):
            out.update(mesh_file_parts(p, rel))
        elif suffix == ".bin" and p.with_suffix(".gltf").exists():
            continue                                      # read through its .gltf, accessor by accessor
        elif suffix == ".png":
            out[f"{rel}: map"] = {"kind": "map", "leaf": is_leaf(p.name), "sha": pixels(p.read_bytes())}
        elif suffix == ".json":
            docs[rel] = flat(plain(json.loads(p.read_text(encoding="utf-8"))))
        elif suffix == ".npz":
            with np.load(p) as z:
                out[f"{rel}: arrays"] = {"kind": "rest", "leaf": False, "sha": sha(*[x for k in sorted(z.files) for x in ([k, str(z[k].dtype), list(z[k].shape)], z[k].tobytes())])}
        else:
            out[f"{rel}: bytes"] = {"kind": "rest", "leaf": False, "sha": sha(p.read_bytes())}
    return out, docs


def json_kind(rel: str, path: tuple) -> str:
    """Whose a value in a .json file is: the leaves', a whole file's (leaves included), or something else's."""
    if any(k in LEAF_KEYS for k in path):
        return "leaves"
    # the game target's variants: the height and width of the mesh's box (treegen/game_unreal.py, write_fragments), not the tree's
    box = path[-1] in ("height_m", "width_m") and ("variants" in path or rel.endswith("flora_variants.json"))
    return "whole file" if box or any(k in WHOLE_FILE for k in path) else "other"


def levels(doc: dict) -> dict:
    """From a game manifest, flattened: for each age, season and level, its triangles in all, in each part, and in all but leaves."""
    rows = {}
    for path, value in doc.items():
        if path[0] == "stages" and len(path) in (6, 7) and path[2] == "seasons" and (path[5:] == ("triangles",) or path[5] == "parts"):
            rows.setdefault((path[1], path[3], path[4]), {"stage": path[1], "season": path[3], "level": path[4]})[path[-1]] = value
    for row in rows.values():
        row["not_leaves"] = row.get("triangles", 0) - sum(row.get(k, 0) for k in ("leaves", "far_cards"))
    return rows


def compare(old: Path, new: Path) -> dict:
    """What differs between two exports, and whether it is the leaves alone."""
    (a, docs_a), (b, docs_b) = parts(old), parts(new)
    rows = {"same": [], "differ": [], "in_one_only": []}
    for key in sorted(set(a) | set(b)):
        if key not in a or key not in b:
            rows["in_one_only"].append({"part": key, "leaf": (a.get(key) or b.get(key))["leaf"], "in": "old" if key in a else "new"})
        elif a[key]["sha"] == b[key]["sha"]:
            rows["same"].append(key)
        else:
            row = {"part": key, "leaf": a[key]["leaf"]}
            if a[key]["kind"] == "mesh":
                row.update(vertices=[a[key]["vertices"], b[key]["vertices"]], triangles=[a[key]["triangles"], b[key]["triangles"]])
            rows["differ"].append(row)
    values = []
    for rel in sorted(set(docs_a) | set(docs_b)):
        da, db = docs_a.get(rel, {}), docs_b.get(rel, {})
        for path in sorted(set(da) | set(db)):
            if da.get(path, "(absent)") != db.get(path, "(absent)"):
                values.append({"file": rel, "path": ".".join(path), "old": da.get(path, "(absent)"), "new": db.get(path, "(absent)"), "whose": json_kind(rel, path)})
    numbers = []
    for rel in sorted(set(docs_a) & set(docs_b)):
        la, lb = levels(docs_a[rel]), levels(docs_b[rel])
        for key in sorted(set(la) & set(lb)):
            x, y = la[key], lb[key]
            numbers.append({"file": rel, **{k: x[k] for k in ("stage", "season", "level")}, "wood_triangles": [x.get("wood"), y.get("wood")],
                            "triangles_not_leaves": [x["not_leaves"], y["not_leaves"]], "triangles_in_all": [x.get("triangles"), y.get("triangles")]})
        if set(la) != set(lb):
            numbers.append({"file": rel, "levels": [len(la), len(lb)]})
        for stage in sorted({p[1] for p in docs_a[rel] if p[0] == "stages"}):
            get = lambda d, k: d.get(("stages", stage, k))  # noqa: E731
            if get(docs_a[rel], "exported_leaves") is not None:
                numbers.append({"file": rel, "stage": stage, "age": get(docs_a[rel], "age"), **{k: [get(docs_a[rel], k), get(docs_b[rel], k)] for k in ("exported_leaves", "exported_leaf_area_m2", "model_leaf_area_m2")}})
    kinds = {}
    for key in rows["same"]:
        kinds.setdefault(a[key]["kind"] + (" of leaves" if a[key]["leaf"] else ""), [0, 0])[0] += 1
    for row in rows["differ"]:
        kinds.setdefault(a[row["part"]]["kind"] + (" of leaves" if row["leaf"] else ""), [0, 0])[1] += 1
    not_leaves = [r["part"] for r in rows["differ"] + rows["in_one_only"] if not r["leaf"]] + [f"{v['file']}: {v['path']}" for v in values if v["whose"] == "other"]
    not_leaves += [f"{n['file']}: {k} at {n.get('level', n.get('stage'))}" for n in numbers
                   for k in ("wood_triangles", "triangles_not_leaves", "exported_leaves", "exported_leaf_area_m2", "model_leaf_area_m2", "levels") if k in n and n[k][0] != n[k][1]]
    compared = len(rows["same"]) + len(rows["differ"])
    return {"old": str(old), "new": str(new), "parts_compared": compared, "same_and_differ_by_kind": kinds, "differ": rows["differ"], "in_one_only": rows["in_one_only"],
            "values_that_differ": values, "numbers_old_new": numbers, "not_the_leaves": not_leaves, "identical": compared > 0 and not rows["differ"] and not rows["in_one_only"] and not values,
            "leaves_only": compared > 0 and not not_leaves}


def say(name: str, c: dict) -> None:
    print(f"\n{name}: {c['parts_compared']} parts compared; same and different by kind: {json.dumps(c['same_and_differ_by_kind'])}")
    for row in c["differ"]:
        print(f"  differs ({'leaves' if row['leaf'] else 'NOT LEAVES'}): {row['part']}" + (f"; vertices {row['vertices']}, triangles {row['triangles']}" if "triangles" in row else ""))
    for row in c["in_one_only"]:
        print(f"  only in the {row['in']} one ({'leaves' if row['leaf'] else 'NOT LEAVES'}): {row['part']}")
    for v in c["values_that_differ"]:
        print(f"  value ({v['whose']}): {v['file']}: {v['path']}: {v['old']} -> {v['new']}")
    for n in c["numbers_old_new"]:
        print("  " + json.dumps(n))
    print(f"  {name}: " + ("IDENTICAL" if c["identical"] else "LEAVES ONLY" if c["leaves_only"] else "NOT LEAVES ONLY: " + "; ".join(c["not_the_leaves"][:20])))


def recordings(a) -> int:
    old, new = Path(a.old), Path(a.new)      # as given, so the result names no folder above the checkout's own
    rec_old, rec_new = golden.load_hashes(str(old)), golden.load_hashes(str(new))
    tracked = json.loads(golden.TRACKED.read_text(encoding="utf-8"))
    out = E / a.label
    out.mkdir(parents=True, exist_ok=True)
    result = {"old_recording": {"label": rec_old.get("label"), "commit": rec_old.get("commit")}, "new_recording": {"label": rec_new.get("label"), "commit": rec_new.get("commit")},
              "made_on_differences": golden.made_on_differences(golden.made_on(rec_new), golden.made_on(rec_old)), "runs": {}, "timelapse": {}}
    ok = not result["made_on_differences"]
    for line in result["made_on_differences"]:
        print(line)
    for run in [x for x in a.runs.split(",") if x]:
        files_old, files_new = rec_old["runs"][run]["files"], rec_new["runs"][run]["files"]
        c = compare(old / run, new / run)
        # the folders are what the recordings hashed, and the old recording is what the tracked file holds (until it is tracked again)
        c["old_folder_hashes_as_recorded"] = golden.hash_tree(old / run) == files_old
        c["new_folder_hashes_as_recorded"] = golden.hash_tree(new / run) == files_new
        c["tracked_file_holds_the_old_recording"] = tracked["runs"].get(run, {}).get("files") == files_old
        c["golden_files"] = {"same": sorted(k for k in files_old if files_new.get(k) == files_old[k]), "differ": sorted(k for k in files_old if k in files_new and files_new[k] != files_old[k]),
                             "in_one_only": sorted(set(files_old) ^ set(files_new))}
        result["runs"][run] = c
        say(run, c)
        print(f"  golden hashes, old against new: {len(c['golden_files']['same'])} files the same, {len(c['golden_files']['differ'])} differ ({', '.join(Path(k).name for k in c['golden_files']['differ'])}), "
              f"{len(c['golden_files']['in_one_only'])} in one only")
        print(f"  the old folder hashes as its recording says: {c['old_folder_hashes_as_recorded']}; the new one: {c['new_folder_hashes_as_recorded']}; "
              f"the tracked file holds the old recording's hashes: {c['tracked_file_holds_the_old_recording']}")
        ok = ok and c["leaves_only"] and c["old_folder_hashes_as_recorded"] and c["new_folder_hashes_as_recorded"]
        (out / "leaves_only.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for run in [x for x in a.timelapse.split(",") if x]:
        command, peak_gb = {**golden.RUNS, **golden.MORE_RUNS}[run]
        folder = out / "tmp" / run
        shutil.rmtree(folder, ignore_errors=True)
        got = golden.run_case(run, command + ["--timelapse"], peak_gb, folder)     # (a run that fails stops here, its log kept)
        shutil.rmtree(out / "tmp", ignore_errors=True)
        want = rec_old["runs"][run]["files"]
        differ = sorted(k for k in set(want) | set(got["files"]) if want.get(k) != got["files"].get(k))
        result["timelapse"][run] = {"command": " ".join(command + ["--timelapse"]).replace("{dir}", "DIR"), "files": len(got["files"]), "differ_from_the_old_recording": differ,
                                    "identical": bool(want) and not differ, "seconds": got["seconds"]}
        print(f"\n{run} with --timelapse: {len(got['files'])} files hashed; " + ("IDENTICAL to the old recording" if not differ and want else "DIFFERENT: " + ", ".join(differ)))
        ok = ok and bool(want) and not differ
        (out / "leaves_only.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    result["verdict"] = "LEAVES ONLY" if ok else "NOT LEAVES ONLY"
    (out / "leaves_only.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"\n{result['verdict']}")
    return 0 if ok else 1


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    r = sub.add_parser("recordings", help="two recordings of tools/golden.py, run by run")
    r.add_argument("--label", required=True, help="where the result goes: out/bench/ensemble/<label>/leaves_only.json")
    r.add_argument("--old", required=True, help="the recording's folder before the change")
    r.add_argument("--new", required=True, help="the recording's folder after it")
    r.add_argument("--runs", default="export30,unreal30,usd_open30")
    r.add_argument("--timelapse", default="", help="golden runs to make again with the export's --timelapse option; each must hash as the old recording")
    f = sub.add_parser("folders", help="two export folders")
    f.add_argument("old")
    f.add_argument("new")
    a = ap.parse_args(argv)
    if a.what == "recordings":
        return recordings(a)
    c = compare(Path(a.old), Path(a.new))
    say("export", c)
    return 0 if c["leaves_only"] else 1


if __name__ == "__main__":
    sys.exit(main())
