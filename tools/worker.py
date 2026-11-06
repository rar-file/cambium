"""Second-PC worker (campaign P0, D10).  Takes a list of cases, runs them one at a time
with the same settings as the main PC, and writes the outputs and hashes to a folder
to copy back.  See WORKER.md.

    python tools/worker.py cases/golden.json --out worker_out

It stops first if the Python or package versions differ from requirements.lock, because
that could change results.  It records the CPU, memory, library versions, thread counts
and the OpenBLAS kernel, because results can differ in the last digits between CPUs.  A
stopped worker can be started again: finished cases are kept.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from golden import run_case  # noqa: E402
from run_cache import code_version  # noqa: E402
from treegen.machine import describe_machine  # noqa: E402

# what a case may run: the model's own entry points, nothing else
ALLOWED = {"cli.py", "tools/plot.py"}


def locked_versions(path: Path = ROOT / "requirements.lock") -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "==" in line:
            name, version = line.split("==", 1)
            out[name.lower()] = version
    return out


def version_problems(locked: dict | None = None, python: str | None = None) -> list:
    """Everything that differs from the lock file and the pinned Python."""
    problems = []
    want = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    have = python or sys.version.split()[0]
    if have != want:
        problems.append(f"Python is {have}, needs {want}")
    for name, version in (locked if locked is not None else locked_versions()).items():
        try:
            got = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            problems.append(f"{name} isn't installed, needs {version}")
            continue
        if got != version:
            problems.append(f"{name} is {got}, needs {version}")
    return problems


def load_cases(path: Path) -> list:
    cases = json.loads(Path(path).read_text(encoding="utf-8"))["cases"]
    for c in cases:
        if not c["args"] or c["args"][0] not in ALLOWED:
            raise SystemExit(f"case {c.get('name')}: only {sorted(ALLOWED)} may be run")
    return cases


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cases")
    ap.add_argument("--out", default="worker_out")
    ap.add_argument("--allow-version-mismatch", action="store_true", help="run anyway; only good for exploring")
    a = ap.parse_args()

    problems = version_problems()
    if problems and not a.allow_version_mismatch:
        print("Stopped: this PC's versions differ from requirements.lock, which could change results:")
        print("\n".join(f"  {p}" for p in problems))
        sys.exit(2)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "hashes.json"
    doc = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {"runs": {}}
    machine = describe_machine()
    doc.update({"label": f"worker on {machine['computer']}", "machine": machine, "code_version": code_version(),
                "version_problems": problems})
    target.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"CPU: {machine['cpu']} ({machine['cpu_threads']} threads), memory {machine['memory_gb']} GB")
    print(f"OpenBLAS kernel: {machine['numpy_openblas_kernel']}; maths threads: {machine['math_threads']}", flush=True)

    for case in load_cases(a.cases):
        name = case["name"]
        if name in doc["runs"]:
            print(f"{name}: already done", flush=True)
            continue
        print(f"{name}: running...", flush=True)
        doc["runs"][name] = run_case(name, case["args"], float(case.get("peak_gb", 1.5)), out / name)
        r = doc["runs"][name]
        print(f"{name}: {r['seconds']} s, peak {r['peak_mb']} MB, {len(r['files'])} files hashed", flush=True)
        target.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"\nDone. Copy this folder back to the main PC: {out.resolve()}")


if __name__ == "__main__":
    main()
