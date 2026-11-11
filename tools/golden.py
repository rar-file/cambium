"""Golden runs and their hashes (campaign P0, step 1).

Four runs fix what the model produces.  After any performance change they are run
again, and every model output and mesh file must hash the same.

    python tools/golden.py record before            # run all four, one at a time
    python tools/golden.py record before --only tree60,regen10
    python tools/golden.py compare before before_rerun
    python tools/golden.py hash out/bench/golden/before/tree60

Run metadata is left out of the hash: manifest.json, logs, checkpoints, and inside
JSON and GLB files the keys in METADATA_KEYS (git commit, timings, memory figures).
An option listed as off isn't a result either, so a new option that's off by default leaves the
hash alone; an option that's on, or has a value, still counts, except the ways of running (speed.*)
and the records kept beside a run (log.*), whose own outputs would differ if they changed a result:
'record X --set log.rings=true --set log.stand=true' against a plain recording shows they don't.
'rehash' reworks a recording's
hashes from its saved folders, keeping the old ones beside them.
Each run's time and peak memory are recorded next to the hashes, not in them.

Results depend on the maths libraries' versions and on the CPU, so a recording also
holds the machine's description.  Compare runs on another PC with that in mind.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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

# name -> (command, a rough peak in GB for the free-memory check)
RUNS = {
    "tree60": (["cli.py", "--stand", "--seed", "1", "--years", "60", "--no-mesh", "--no-preview", "--quiet", "--out", "{dir}"], 0.65),
    "mesh30": (["cli.py", "--stand", "--seed", "1", "--years", "30", "--no-preview", "--quiet", "--out", "{dir}"], 1.2),
    "plot25": (["tools/plot.py", "--start-trees", "25", "--mode", "natural", "--years", "20", "--seed", "1", "--no-mesh", "--out", "{dir}"], 1.5),
    "regen10": (["tools/plot.py", "--trees", "2", "--dense-start", "10000", "--mode", "natural", "--years", "10", "--seed", "1", "--no-mesh", "--out", "{dir}"], 1.5),
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
    command, peak_gb = RUNS[name]
    return run_case(name, command + [x for s in sets or [] for x in ("--set", s)], peak_gb, folder)


def run_case(name: str, command: list, peak_gb: float, folder: Path) -> dict:
    """One run in its own process: time, peak memory and the hash of every output."""
    free = free_gb()
    if free - peak_gb < FLOOR_GB:
        raise SystemExit(f"STOP before {name}: {free:.2f} GB free, it needs about {FLOOR_GB + peak_gb:.2f} GB "
                         f"(PROTOCOL.md section 6). Nothing was started.")
    folder.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable] + [c.format(dir=str(folder)) for c in command]
    t0 = time.time()
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
    return {"seconds": seconds, "peak_mb": peak_of_run(folder) or peak, "free_gb_at_launch": round(free, 2), "files": hash_tree(folder)}


def record(label: str, only: list | None, root: Path = GOLDEN, sets: list | None = None) -> dict:
    """Run the golden runs one at a time (they count as heavy) and save the hashes."""
    base = root / label
    target = base / "hashes.json"
    doc = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"label": label, "machine": describe_machine(),
                                                                                  "code_version": code_version(), "runs": {}}
    for name in only or list(RUNS):
        print(f"{name}: running...", flush=True)
        doc["runs"][name] = run_one(name, base / name, sets)
        r = doc["runs"][name]
        print(f"{name}: {r['seconds']} s, peak {r['peak_mb']} MB, {len(r['files'])} files hashed", flush=True)
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


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    r = sub.add_parser("record")
    r.add_argument("label")
    r.add_argument("--only", default=None, help="comma-separated run names")
    r.add_argument("--set", action="append", default=[], metavar="KEY=JSON", help="run with a setting changed, to prove it changes no result")
    c = sub.add_parser("compare")
    c.add_argument("first")
    c.add_argument("second")
    re_h = sub.add_parser("rehash")
    re_h.add_argument("label")
    h = sub.add_parser("hash")
    h.add_argument("folder")
    a = ap.parse_args()
    if a.what == "record":
        record(a.label, a.only.split(",") if a.only else None, sets=a.set)
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
