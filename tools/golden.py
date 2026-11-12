"""Golden runs and their hashes (campaign P0, step 1).

Four runs fix what the model produces, and six more cover what those leave out: an open-grown tree,
a forest plot, a second seed, a game export, the meshes the game itself loads and the public USD
export of an open-grown tree.  After any performance change they are run again, and every model
output and mesh file must hash the same.

    python tools/golden.py record before            # run all ten, one at a time
    python tools/golden.py record before --only tree60,regen10
    python tools/golden.py compare before before_rerun
    python tools/golden.py hash out/bench/golden/before/tree60
    python tools/golden.py check before                # against the tracked file, cases/golden_server.json
    python tools/golden.py record after --check        # record, then check
    python tools/golden.py track before                # make that recording the tracked file (a new baseline)
    python tools/golden.py track after --only tree60   # add or replace only these runs in it

The tracked file is written by 'track' alone, from what a recording says: its label and commit, the
Python, libraries and processor it ran on, and each run's hashes, seconds and peak memory.  A
recording that leaves any of that out is refused, so nothing in the file is ever filled in by hand.

'check' exits 0 only when every run and every file hashes the same as in the tracked file, and 1
otherwise, naming each run or file that differs, is missing from the recording or is new in it.  A
comparison of nothing fails too: no runs on one side, or a run with no files on either.  A
different Python, library, processor or number of maths threads is said first, in plain words.  The tracked file holds the
server's hashes, and hashes belong to their machine, so check a recording made on the server:
    tools/node/submit.sh <commit> <label> tools/golden.py record <label> --check
The job's last line then reads EXIT 0 only if the check passed.  A change that moves no result leaves
the tracked file alone; one that does moves it ('track') in the same commit.

Run metadata is left out of the hash: manifest.json, logs, checkpoints, and inside
JSON and GLB files the keys in METADATA_KEYS (git commit, timings, memory figures).
An option listed as off isn't a result either, so a new option that's off by default leaves the
hash alone; an option that's on, or has a value, still counts, except the ways of running (speed.*)
and the records kept beside a run (log.*), whose own outputs would differ if they changed a result:
'record X --set log.rings=true --set log.stand=true' against a plain recording shows they don't.
'rehash' reworks a recording's
hashes from its saved folders, keeping the old ones beside them.
Each run's seconds, the processor seconds it and its children used, and its peak memory are recorded
next to the hashes, not in them.

Results depend on the maths libraries' versions and on the CPU, so a recording also
holds the machine's description.  Compare runs on another PC with that in mind.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import FLOOR_GB, free_gb, process_memory_gb  # noqa: E402
from run_cache import code_version  # noqa: E402
from treegen.machine import describe_machine  # noqa: E402

GOLDEN = ROOT / "out" / "bench" / "golden"
TRACKED = ROOT / "cases" / "golden_server.json"
ABOUT = ("The golden runs' hashes as recorded on the project's server (tools/golden.py). Hashes belong to the machine and the "
         "library versions: a recording made anywhere else differs without any change to the model. Check a server recording "
         "with 'python tools/golden.py check <label>'. Seconds, processor seconds and peak memory are one run's, on one core, for "
         "reference. Each run names the recording and the commit it came from; 'python tools/golden.py track' writes this file.")

# name -> (command, a rough peak in GB for the free-memory check)
RUNS = {
    "tree60": (["cli.py", "--stand", "--seed", "1", "--years", "60", "--no-mesh", "--no-preview", "--quiet", "--out", "{dir}"], 0.65),
    "mesh30": (["cli.py", "--stand", "--seed", "1", "--years", "30", "--no-preview", "--quiet", "--out", "{dir}"], 1.2),
    "plot25": (["tools/plot.py", "--start-trees", "25", "--mode", "natural", "--years", "20", "--seed", "1", "--no-mesh", "--out", "{dir}"], 1.5),
    "regen10": (["tools/plot.py", "--trees", "2", "--dense-start", "10000", "--mode", "natural", "--years", "10", "--seed", "1", "--no-mesh", "--out", "{dir}"], 1.5),
}
# Beyond the four the second PC runs (cases/golden.json, tests/test_worker.py), at the ages that are used (the tests audit, T3):
# an open-grown tree to 60, a 200 m2 forest plot to 30 with mortality on, the stand tree on a second seed, and a game export at 30.
MORE_RUNS = {
    "open60": (["cli.py", "--seed", "1", "--years", "60", "--no-mesh", "--no-preview", "--quiet", "--out", "{dir}"], 2.5),
    "forest30": (["tools/forest.py", "run", "--seed", "1", "--years", "30", "--area", "200", "--out", "{dir}"], 2.0),
    "tree60_seed2": (["cli.py", "--stand", "--seed", "2", "--years", "60", "--no-mesh", "--no-preview", "--quiet", "--out", "{dir}"], 0.65),
    "export30": (["tools/game_export.py", "export", "--seed", "1", "--ages", "30", "--out", "{dir}"], 3.0),
    # The exports people and the game load, pinned after the public USD export was found to fail on an open-grown tree
    # (tests/test_shed_branches.py).
    # unreal30: the game-target export of the stand tree at 30, geometry only, so the meshes the game loads at lod0 and lod1.  Hashed:
    # every .gltf and .bin byte for byte (positions, normals, tangents, UVs, vertex colours and wind data, indices, nodes, materials)
    # and the manifest and fragments less run metadata.  Not hashed: any map, as none is baked (and a .png is never hashed), and the
    # far level, lod2, which is three textured sheets and isn't written without its map.  A full export's meshes are these, accessor
    # by accessor (tools/export_timing.py --quick; tests/test_export_speed.py); export30 holds the plain target's maps and far level.
    "unreal30": (["tools/game_export.py", "export", "--seed", "1", "--ages", "30", "--target", "unreal", "--no-textures", "--out", "{dir}"], 3.0),
    # usd_open30: `cambium export --format usd`, the public command, on the open-grown tree at 30: tree.usdc and tree_reduced.usdc
    # with their parts, and the five plain .glb files, shed branches among them.  Hashed: every byte, less the .glb files' run
    # manifest.  The files name Cambium's version (their generator), so a new version number moves these hashes: track the run again.
    "usd_open30": (["-m", "cambium", "export", "--seed", "1", "--ages", "30", "--format", "usd", "--out", "{dir}"], 3.0),
}

METADATA_KEYS = {"run_manifest", "timings", "peak_memory", "peak_mb", "runtime_s", "files_mb"}
# (saved states are left out of the hash too: they're a way of running, not output)
SKIP_NAMES = {"manifest.json", "checkpoint.pkl", "checkpoint.pkl.tmp", "hashes.json"}
SKIP_SUFFIXES = {".log", ".png", ".tmp"}
SKIP_DIRS = {"history", "previews", "__pycache__"}


def strip_metadata(o):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in METADATA_KEYS:
                continue
            if k == "options" and isinstance(v, dict):
                # (speed.*: ways of running; log.*: records kept beside a run, treegen/logs.py.  If one changes a result, the result's own files differ)
                v = {name: value for name, value in v.items() if value is not False and value is not None and not name.startswith(("speed.", "log."))}
            if k == "year_log" and isinstance(v, list):
                # tools/forest.py: each year's seconds and peak MB (the 2nd and 3rd numbers) are the run's; the rest is the plot's
                v = [row[:1] + row[3:] if isinstance(row, list) else row for row in v]
            out[k] = strip_metadata(v)
        return out
    if isinstance(o, list):
        return [strip_metadata(v) for v in o]
    return o


def _canonical(o) -> bytes:
    return json.dumps(strip_metadata(o), sort_keys=True, separators=(",", ":"), allow_nan=True).encode("utf-8")


def hash_file(path: Path) -> str:
    """SHA-256 of what a file holds, leaving out run metadata."""
    h = hashlib.sha256()
    suffix = path.suffix.lower()
    if suffix == ".json":
        h.update(_canonical(json.loads(path.read_text(encoding="utf-8"))))
    elif suffix == ".npz":
        with np.load(path) as z:
            for name in sorted(z.files):
                a = z[name]
                h.update(name.encode())
                h.update(str(a.dtype).encode())
                h.update(str(a.shape).encode())
                h.update(a.tobytes())
    elif suffix == ".glb":
        with open(path, "rb") as f:
            magic, version, _total = struct.unpack("<4sII", f.read(12))
            if magic != b"glTF" or version != 2:
                raise ValueError(f"{path}: not a glTF 2 binary")
            length, kind = struct.unpack("<I4s", f.read(8))
            if kind != b"JSON":
                raise ValueError(f"{path}: first chunk is not JSON")
            h.update(_canonical(json.loads(f.read(length))))
            for block in iter(lambda: f.read(1 << 22), b""):
                h.update(block)
    else:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 22), b""):
                h.update(block)
    return h.hexdigest()


def hash_tree(folder: Path) -> dict:
    """Relative path -> hash, for every model output and mesh file under a folder."""
    out = {}
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name in SKIP_NAMES or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        rel = path.relative_to(folder)
        if SKIP_DIRS & set(rel.parts) or any(part.startswith("state_") or part == "states" for part in rel.parts):
            continue
        out[rel.as_posix()] = hash_file(path)
    return out


def peak_of_child(proc) -> float | None:
    """Peak memory of a child process (MB), while it can still be read.  On Windows a venv's
    python.exe is only a launcher, so this reads the launcher, not the run: see peak_of_run."""
    gb = process_memory_gb(proc, peak=True)
    return None if gb is None else round(gb * 1024, 1)


def peak_of_run(folder: Path) -> float | None:
    """The peak memory a run recorded for itself (MB): a tree's manifest, or a plot's plot.json."""
    peaks = []
    for f in folder.rglob("manifest.json"):
        peaks += [v for v in json.loads(f.read_text(encoding="utf-8")).get("peak_memory", {}).values() if isinstance(v, (int, float))]
    for f in folder.rglob("plot.json"):
        v = json.loads(f.read_text(encoding="utf-8")).get("peak_mb")
        if isinstance(v, (int, float)):
            peaks.append(v)
    return round(max(peaks), 1) if peaks else None


def run_one(name: str, folder: Path, sets: list | None = None) -> dict:
    command, peak_gb = {**RUNS, **MORE_RUNS}[name]
    return run_case(name, command + [x for s in sets or [] for x in ("--set", s)], peak_gb, folder)


def run_case(name: str, command: list, peak_gb: float, folder: Path) -> dict:
    """One run in its own process: time, peak memory and the hash of every output."""
    free = free_gb()
    if free - peak_gb < FLOOR_GB:
        raise SystemExit(f"STOP before {name}: {free:.2f} GB free, it needs about {FLOOR_GB + peak_gb:.2f} GB "
                         f"(PROTOCOL.md section 6). Nothing was started.")
    folder.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable] + [c.format(dir=str(folder)) for c in command]
    t0, used = time.time(), os.times()
    with open(folder / "run.log", "w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
        peak = None
        while proc.poll() is None:
            peak = peak_of_child(proc) or peak
            time.sleep(0.2)
        peak = peak_of_child(proc) or peak
    if proc.returncode != 0:
        raise SystemExit(f"{name} failed with exit {proc.returncode}; see {folder / 'run.log'}")
    seconds = round(time.time() - t0, 1)
    # the processor time the run and its own children took: on a busy machine it moves less than the seconds do (Windows keeps none)
    cpu = round(sum(os.times()[2:4]) - sum(used[2:4]), 1) or None
    return {"seconds": seconds, "cpu_seconds": cpu, "peak_mb": peak_of_run(folder) or peak, "free_gb_at_launch": round(free, 2), "files": hash_tree(folder)}


def commit() -> str | None:
    """The commit being run: git's, or on the server, where the code comes without git, the one in COMMIT."""
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT), capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        f = ROOT / "COMMIT"
        return f.read_text(encoding="utf-8").strip() if f.exists() else None


def llvmlite_version() -> str | None:
    """numba's compiler, which treegen/machine.py doesn't list."""
    try:
        import llvmlite
        return llvmlite.__version__
    except ImportError:
        return None


def record(label: str, only: list | None, root: Path = GOLDEN, sets: list | None = None) -> dict:
    """Run the golden runs one at a time (they count as heavy) and save the hashes."""
    base = root / label
    target = base / "hashes.json"
    doc = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"label": label, "machine": describe_machine(),
                                                                                  "code_version": code_version(), "runs": {}}
    if doc.setdefault("commit", commit()) != commit():
        # (else a later 'check' would pass on runs this code never ran)
        raise SystemExit(f"{label} was recorded at {doc['commit']}, and this is {commit()}: use a new label. Nothing was run.")
    doc["machine"]["math_libraries"].setdefault("llvmlite", llvmlite_version())
    for name in only or list(RUNS) + list(MORE_RUNS):
        print(f"{name}: running...", flush=True)
        doc["runs"][name] = run_one(name, base / name, sets)
        r = doc["runs"][name]
        print(f"{name}: {r['seconds']} s ({r['cpu_seconds']} s of processor time), peak {r['peak_mb']} MB, {len(r['files'])} files hashed", flush=True)
        target.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc


def load_hashes(label_or_path: str, root: Path = GOLDEN) -> dict:
    p = Path(label_or_path)
    if p.suffix != ".json":
        p = (p / "hashes.json") if p.is_dir() else (root / label_or_path / "hashes.json")
    return json.loads(p.read_text(encoding="utf-8"))


def rehash(label: str, root: Path = GOLDEN) -> None:
    """Rework a recording's hashes from its saved folders, after a change in what's hashed."""
    path = root / label / "hashes.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    path.with_name("hashes_before_rehash.json").write_text(json.dumps(saved, indent=1), encoding="utf-8")
    for name, run in saved["runs"].items():
        run["files"] = hash_tree(root / label / name)
    path.write_text(json.dumps(saved, indent=1), encoding="utf-8")


def compare(a: dict, b: dict) -> tuple:
    """(identical?, lines describing every difference, time and memory table rows)."""
    same = True
    lines, table = [], []
    for name in sorted(set(a["runs"]) | set(b["runs"])):
        ra, rb = a["runs"].get(name), b["runs"].get(name)
        if ra is None or rb is None:
            same = False
            lines.append(f"{name}: only in {'second' if ra is None else 'first'} recording")
            continue
        fa, fb = ra["files"], rb["files"]
        only = sorted(set(fa) ^ set(fb))
        changed = sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])
        if only or changed:
            same = False
        lines.append(f"{name}: {len(set(fa) & set(fb)) - len(changed)} files identical, {len(changed)} differ, {len(only)} in one only")
        lines.extend(f"  differs: {k}" for k in changed[:40])
        lines.extend(f"  in one only: {k}" for k in only[:40])
        table.append((name, ra.get("seconds"), rb.get("seconds"), ra.get("peak_mb"), rb.get("peak_mb")))
    return same, lines, table


def made_on(rec: dict) -> dict:
    """What a recording was made with, without the computer's name: Python, the libraries that can change a result, the processor."""
    m = rec.get("machine", {})
    libs = m.get("math_libraries", {})
    return {"python": libs.get("python"),
            "libraries": {k: libs.get(k) for k in ("numpy", "scipy", "numba", "llvmlite", "numpy_blas", "scipy_blas")},
            "processor": f"{m.get('cpu')} ({m.get('architecture')}), {m.get('cpu_threads')} threads",
            "openblas_kernel": m.get("numpy_openblas_kernel"), "math_threads": m.get("math_threads")}


def made_on_differences(here: dict, tracked: dict) -> list:
    """Plain lines for every way two made_on blocks differ."""
    def plain(m):
        return {"Python": m.get("python"), **m.get("libraries", {}), "the processor": m.get("processor"),
                "the OpenBLAS kernel": m.get("openblas_kernel"), "the number of maths threads": m.get("math_threads")}
    a, b = plain(here), plain(tracked)
    return [f"{k} is {a.get(k) or 'not recorded'} in this recording and {b.get(k) or 'not recorded'} in the tracked file: "
            "the hashes can differ for that reason alone." for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]


def unsaid(rec: dict) -> list:
    """What a recording leaves out of all that the tracked file holds: its label, its commit, or a part of made_on."""
    on, m = made_on(rec), rec.get("machine", {})
    said = {"label": rec.get("label"), "commit": rec.get("commit"), "python": on["python"], **on["libraries"], "cpu": m.get("cpu"),
            "architecture": m.get("architecture"), "cpu_threads": m.get("cpu_threads"), "openblas_kernel": on["openblas_kernel"], "math_threads": on["math_threads"]}
    return sorted(k for k, v in said.items() if not v)


def track(rec: dict, only: list | None = None, path: Path = TRACKED, commit_id: str | None = None) -> dict:
    """Write a recording's hashes into the tracked file: all of it (the whole file rebuilt, a new baseline), or only some runs, which
    must then come from the same Python, libraries and processor as the file.  Each run names its recording and commit."""
    on = made_on(rec)
    doc = json.loads(path.read_text(encoding="utf-8")) if only and path.exists() else {"about": ABOUT, "made_on": on, "runs": {}}
    if only and made_on_differences(on, doc["made_on"]):
        raise SystemExit("Not added: " + " ".join(made_on_differences(on, doc["made_on"])))
    for name in only or sorted(rec["runs"]):
        r = rec["runs"][name]
        doc["runs"][name] = {"commit": commit_id or rec.get("commit"), "recording": rec.get("label"), "seconds": r.get("seconds"),
                             "cpu_seconds": r.get("cpu_seconds"), "peak_mb": r.get("peak_mb"), "files": r["files"]}
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    return doc


def check(rec: dict, tracked: dict) -> tuple:
    """(exactly the same?, lines): every run and file that differs, is missing from the recording, or is new in it."""
    lines = made_on_differences(made_on(rec), tracked.get("made_on", {}))
    tracked_runs, rec_runs = tracked.get("runs") or {}, rec.get("runs") or {}
    same = bool(tracked_runs and rec_runs)
    if not tracked_runs or not rec_runs:
        # an empty comparison proves nothing, so it fails
        lines.append(f"NOTHING COMPARED: {'the tracked file' if not tracked_runs else 'the recording'} has no runs")
    for name in sorted(set(tracked_runs) | set(rec_runs)):
        t, r = tracked_runs.get(name), rec_runs.get(name)
        if r is None or t is None:
            same = False
            lines.append(f"{'MISSING' if r is None else 'NEW'}: {name}, {'tracked but not in the recording' if r is None else 'in the recording but not tracked'}")
            continue
        ft, fr = t["files"], r["files"]
        bad = [f"MISSING: {name}/{k}" for k in sorted(set(ft) - set(fr))] + [f"NEW: {name}/{k}" for k in sorted(set(fr) - set(ft))]
        bad += [f"DIFFERS: {name}/{k}" for k in sorted(set(ft) & set(fr)) if ft[k] != fr[k]]
        if not ft and not fr:
            bad.append(f"NOTHING COMPARED: {name} has no files on either side")
        same = same and not bad
        lines.append(f"{'same' if not bad else 'NOT the same'}: {name}, {len(ft)} files tracked; {r.get('seconds')} s and {r.get('peak_mb')} MB "
                     f"(tracked: {t.get('seconds')} s, {t.get('peak_mb')} MB)")
        lines.extend("  " + x for x in bad)
    return same, lines


def print_check(recording: str, against: Path) -> int:
    same, lines = check(load_hashes(recording), json.loads(against.read_text(encoding="utf-8")))
    print("\n".join(lines))
    print("\nIDENTICAL" if same else "\nDIFFERENT")
    return 0 if same else 1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="what", required=True)
    r = sub.add_parser("record")
    r.add_argument("label")
    r.add_argument("--only", default=None, help="comma-separated run names")
    r.add_argument("--set", action="append", default=[], metavar="KEY=JSON", help="run with a setting changed, to prove it changes no result")
    r.add_argument("--check", action="store_true", help="then check the recording against the tracked file, as 'check' does")
    c = sub.add_parser("compare")
    c.add_argument("first")
    c.add_argument("second")
    re_h = sub.add_parser("rehash")
    re_h.add_argument("label")
    h = sub.add_parser("hash")
    h.add_argument("folder")
    ck = sub.add_parser("check", help="compare a recording with the tracked file: exit 0 only if every hash is the same")
    ck.add_argument("recording", help="a label under out/bench/golden, its folder, or its hashes.json")
    ck.add_argument("--against", default=str(TRACKED))
    t = sub.add_parser("track", help="write a recording's hashes into the tracked file")
    t.add_argument("recording")
    t.add_argument("--only", default=None, help="comma-separated run names: add or replace only these, keeping the rest")
    t.add_argument("--commit", default=None, help="the commit the recording ran, for a recording that doesn't say")
    t.add_argument("--file", default=str(TRACKED))
    a = ap.parse_args()
    if a.what == "record":
        record(a.label, a.only.split(",") if a.only else None, sets=a.set)
        if a.check:
            sys.exit(print_check(a.label, TRACKED))
    elif a.what == "check":
        sys.exit(print_check(a.recording, Path(a.against)))
    elif a.what == "track":
        rec = load_hashes(a.recording)
        left_out = unsaid({**rec, "commit": a.commit or rec.get("commit")})
        if left_out:
            sys.exit(f"Not tracked: the recording doesn't say its {', '.join(left_out)}, and nothing in the tracked file is written in by hand. "
                     "Record the runs again with this code and track that recording.")
        doc = track(rec, a.only.split(",") if a.only else None, Path(a.file), a.commit)
        print(f"{a.file}: {len(doc['runs'])} runs")
    elif a.what == "rehash":
        rehash(a.label)
    elif a.what == "hash":
        print(json.dumps(hash_tree(Path(a.folder)), indent=1))
    else:
        first, second = load_hashes(a.first), load_hashes(a.second)
        same, lines, table = compare(first, second)
        print("\n".join(lines))
        print("\n| Run | Seconds, first | Seconds, second | Peak MB, first | Peak MB, second |")
        print("|---|---|---|---|---|")
        for row in table:
            print("| " + " | ".join(str(x) for x in row) + " |")
        m1, m2 = first.get("machine", {}), second.get("machine", {})
        diff = {k: (m1.get(k), m2.get(k)) for k in sorted(set(m1) | set(m2)) if m1.get(k) != m2.get(k)}
        if diff:
            print(f"\nMachines differ: {json.dumps(diff, indent=1)}")
        if first.get("code_version") != second.get("code_version"):
            print("\nThe model code differs between these recordings.")
        print("\nIDENTICAL" if same else "\nDIFFERENT")
        sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
