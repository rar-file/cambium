"""Why do parallel runs slow each other down?  (Campaign P0, after the golden runs.)

Runs the seed-1 tree alone and two at once: as they are, each pinned to its own physical
core, and in lean mode.  While each group runs it samples the disk write rate, hard page
faults and the CPU clock.  Every run's hash must be the same, or the test is void.

Windows can't show memory bandwidth directly, so a benchmark that isn't the model tests
it: one workload that fits in a core's own cache, one that fits the shared cache, and one
that has to go to memory, each run 1, 2 and 4 at once.  If the cache workload scales and the
memory one doesn't, memory bandwidth is the limit, not the cores or the clock.

    python tools/diagnose_parallel.py                 # all of it, about 10 minutes
    python tools/diagnose_parallel.py --micro-only    # the benchmark, about 2 minutes
    python tools/diagnose_parallel.py --scale 1,8,14  # how many at once is fastest

Light runs only (PROTOCOL.md section 6).  It checks the free-memory floor before each group.
Results: out/bench/p0/parallel_diagnosis.md and .json.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from batch import FLOOR_GB, free_gb, process_memory_gb  # noqa: E402
from treegen.machine import describe_machine  # noqa: E402

OUT = ROOT / "out" / "bench" / "p0"
SCREEN = ROOT / "tools" / "sensitivity_screen.py"
RUN_PEAK_GB = 0.6
COUNTERS = {
    "disk_write_mb_s": r"\PhysicalDisk(_Total)\Disk Write Bytes/sec",
    "disk_read_mb_s": r"\PhysicalDisk(_Total)\Disk Read Bytes/sec",
    "hard_faults_s": r"\Memory\Page Reads/sec",
    "cpu_busy_pct": r"\Processor(_Total)\% Processor Time",
    "clock_pct": r"\Processor Information(_Total)\% Processor Performance",
    "clock_base_mhz": r"\Processor Information(_Total)\Processor Frequency",
}


def physical_core_masks() -> list:
    """One affinity mask per physical core (its two threads), from Windows."""
    import ctypes.wintypes as wt

    class Info(ctypes.Structure):
        _fields_ = [("mask", ctypes.c_size_t), ("relation", ctypes.c_int), ("pad", ctypes.c_byte * 16)]

    k32 = ctypes.WinDLL("kernel32")
    size = wt.DWORD(0)
    k32.GetLogicalProcessorInformation(None, ctypes.byref(size))
    count = size.value // ctypes.sizeof(Info)
    buf = (Info * count)()
    if not k32.GetLogicalProcessorInformation(buf, ctypes.byref(size)):
        raise OSError("GetLogicalProcessorInformation failed")
    return core_masks_from(buf)


def core_masks_from(entries) -> list:
    return sorted(int(e.mask) for e in entries if e.relation == 0)   # 0 = RelationProcessorCore


def pin(proc, mask: int) -> None:
    import ctypes.wintypes as wt

    k32 = ctypes.WinDLL("kernel32")
    k32.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
    k32.SetProcessAffinityMask.restype = wt.BOOL
    if not k32.SetProcessAffinityMask(wt.HANDLE(int(proc._handle)), mask):
        raise OSError("SetProcessAffinityMask failed")


def _proc_snapshot() -> dict:
    """Linux: running totals of hard faults and disk writes, and the time."""
    out = {"t": time.time(), "hard_faults": 0, "written_mb": 0.0}
    for line in Path("/proc/vmstat").read_text().splitlines():
        if line.startswith("pgmajfault "):
            out["hard_faults"] = int(line.split()[1])
    for line in Path("/proc/diskstats").read_text().splitlines():
        p = line.split()
        if len(p) > 9 and p[2].rstrip("0123456789") == p[2] and not p[2].startswith(("loop", "ram")):
            out["written_mb"] += int(p[9]) * 512 / 2 ** 20
    return out


class Sampler:
    """typeperf in the background for the life of a group of runs (Windows), or the
    change in the system's running totals across it (Linux; no clock figure there)."""

    def __enter__(self):
        if sys.platform != "win32":
            self.start = _proc_snapshot()
            return self
        self.file = Path(tempfile.mkdtemp()) / "counters.csv"
        cmd = ["typeperf", *COUNTERS.values(), "-si", "2", "-f", "CSV", "-o", str(self.file), "-y"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self

    def __exit__(self, *exc):
        if sys.platform != "win32":
            self.end = _proc_snapshot()
            return
        self.proc.terminate()
        self.proc.wait()

    def means(self) -> dict:
        if sys.platform != "win32":
            dt = max(self.end["t"] - self.start["t"], 1e-6)
            return {"disk_write_mb_s": round((self.end["written_mb"] - self.start["written_mb"]) / dt, 2),
                    "hard_faults_s": round((self.end["hard_faults"] - self.start["hard_faults"]) / dt, 2)}
        return means_from_csv(self.file)


def means_from_csv(path: Path) -> dict:
    """Mean of each counter over the group, skipping typeperf's blank first sample."""
    if not Path(path).exists():
        return {}
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))
    if len(rows) < 2:
        return {}
    names = list(COUNTERS)
    vals = {k: [] for k in names}
    for row in rows[1:]:
        for k, cell in zip(names, row[1:]):
            try:
                vals[k].append(float(cell))
            except ValueError:
                pass
    out = {k: statistics.fmean(v) for k, v in vals.items() if v}
    for k in ("disk_write_mb_s", "disk_read_mb_s"):
        if k in out:
            out[k] /= 2 ** 20
    if "clock_pct" in out and "clock_base_mhz" in out:
        out["clock_mhz"] = out["clock_base_mhz"] * out["clock_pct"] / 100.0
    return {k: round(v, 2) for k, v in out.items()}


def check_floor(n: int, peak_gb: float = RUN_PEAK_GB) -> None:
    free = free_gb()
    if free - n * peak_gb < FLOOR_GB:
        sys.exit(f"STOP: {free:.2f} GB free; {n} runs need about {FLOOR_GB + n * peak_gb:.2f} GB (PROTOCOL.md section 6)")


def tree_group(n: int, lean: bool, pinned: bool, years: int, work: Path) -> dict:
    """n copies of the seed-1 tree at once; their times, hashes and the counters."""
    check_floor(n)
    masks = physical_core_masks() if pinned else []
    procs = []
    with Sampler() as sampler:
        for i in range(n):
            result = work / f"r{time.time_ns()}.json"
            cmd = [sys.executable, str(SCREEN), "--one", "", "--factor", "1.0", "--years", str(years), "--result", str(result)]
            if not lean:
                cmd.append("--full")
            p = subprocess.Popen(cmd, cwd=str(ROOT))
            if pinned:
                # cores 2, 4, ...: core 0 is where Windows keeps much of its own work
                pin(p, masks[(2 + 2 * i) % len(masks)])
            procs.append((p, result, time.time()))
        secs = [None] * n
        while any(s is None for s in secs):
            for i, (p, _, t0) in enumerate(procs):
                if secs[i] is None and p.poll() is not None:
                    if p.returncode != 0:
                        sys.exit("a run failed")
                    secs[i] = time.time() - t0
            time.sleep(0.1)
    results = [json.loads(r.read_text()) for _, r, _ in procs]
    hashes = [r["scored_digest"] for r in results]
    return {"runs": n, "lean": lean, "pinned": pinned, "seconds": [round(s, 1) for s in secs],
            "peak_mb": max(r.get("peak_mb") or 0 for r in results),
            "mean_s": round(statistics.fmean(secs), 1), "hashes": hashes, "counters": sampler.means()}


# -- the benchmark that isn't the model -------------------------------------------
MICRO = {"inside a core's cache (64 KB)": 64 * 1024, "in the shared cache (8 MB)": 8 * 2 ** 20, "in memory (512 MB)": 512 * 2 ** 20}


def micro_child(size: int, seconds: float) -> None:
    """Add arrays of this size for a fixed time; print gigabytes processed per second."""
    import numpy as np

    n = size // 8 // 3
    a, b, c = np.ones(n), np.full(n, 2.0), np.zeros(n)
    np.add(a, b, out=c)   # touch everything once before timing
    done = 0
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        np.add(a, b, out=c)
        done += 3 * n * 8
    print(done / (time.perf_counter() - t0) / 1e9)


def micro_group(size: int, n: int, seconds: float = 12.0) -> float:
    check_floor(n, peak_gb=size / 2 ** 30 + 0.05)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--micro-child", str(size), str(seconds)]
    procs = [subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, text=True) for _ in range(n)]
    rates = [float(p.communicate()[0].strip()) for p in procs]
    return round(statistics.fmean(rates), 2)


def report(doc: dict) -> str:
    lines = ["# Parallel slowdown: measurements", ""]
    if doc.get("scale"):
        one = doc["scale"][0]["mean_s"]
        lines += [f"Machine: {doc.get('machine', {}).get('cpu')}, {doc.get('machine', {}).get('cpu_threads')} threads.", "",
                  "| Runs at once | Mean run time (s) | Slowdown against 1 | Runs per hour | Peak memory, one run (MB) | Disk write (MB/s) | Hard faults (/s) |",
                  "|---|---|---|---|---|---|---|"]
        for g in doc["scale"]:
            c = g["counters"]
            lines.append(f"| {g['runs']} | {g['mean_s']} | {g['mean_s'] / one:.2f}x | {3600.0 * g['runs'] / g['mean_s']:.0f} | "
                         f"{g.get('peak_mb', '-')} | {c.get('disk_write_mb_s', '-')} | {c.get('hard_faults_s', '-')} |")
        lines += ["", f"Hashes: {doc['hashes_same']}", ""]
    if doc.get("trees"):
        lines += ["| Case | Runs at once | Mean run time (s) | Slowdown against 1 alone | Disk write (MB/s) | Hard faults (/s) | Clock (MHz) | CPU busy (%) |",
                  "|---|---|---|---|---|---|---|---|"]
        for label, g in doc["trees"].items():
            c = g["counters"]
            base = doc["trees"].get(label.replace("2 at once", "1 alone"), g)["mean_s"]
            lines.append(f"| {label} | {g['runs']} | {g['mean_s']} | {g['mean_s'] / base:.2f}x | {c.get('disk_write_mb_s', '-')} | "
                         f"{c.get('hard_faults_s', '-')} | {c.get('clock_mhz', '-')} | {c.get('cpu_busy_pct', '-')} |")
        lines += ["", f"Hashes: {doc['hashes_same']}", ""]
    if doc.get("micro"):
        lines += ["**Benchmark that isn't the model: speed of each copy, against 1 alone:**", "",
                  "| Workload | Copies at once | GB/s per copy | Against 1 alone |", "|---|---|---|---|"]
        for label, m in doc["micro"].items():
            for c, rate in m.items():
                lines.append(f"| {label} | {c} | {rate} | {rate / m['1']:.2f}x |")
    return "\n".join(lines) + "\n"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, default=60)
    ap.add_argument("--micro-only", action="store_true")
    ap.add_argument("--scale", default=None, help="comma-separated runs at once, e.g. 1,8,14: find the fastest number")
    ap.add_argument("--micro-copies", default="1,2,4", help="benchmark copies at once")
    ap.add_argument("--micro-child", nargs=2, default=None, help="internal")
    a = ap.parse_args()
    if a.micro_child:
        micro_child(int(a.micro_child[0]), float(a.micro_child[1]))
        return

    doc = {"trees": {}, "micro": {}, "machine": describe_machine()}
    if a.scale:
        doc["scale"] = []
        with tempfile.TemporaryDirectory() as tmp:
            for n in (int(x) for x in a.scale.split(",")):
                print(f"{n} at once...", flush=True)
                g = tree_group(n, True, False, a.years, Path(tmp))
                doc["scale"].append(g)
                print(f"  mean {g['mean_s']} s, {3600.0 * n / g['mean_s']:.0f} runs per hour", flush=True)
        hashes = {h for g in doc["scale"] for h in g["hashes"]}
        doc["hashes_same"] = "all the same" if len(hashes) == 1 else f"DIFFERENT: {len(hashes)} distinct, so this test is void"
    elif not a.micro_only:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            for label, n, lean, pinned in (("full, 1 alone", 1, False, False), ("full, 2 at once", 2, False, False),
                                           ("pinned, 1 alone", 1, False, True), ("pinned, 2 at once", 2, False, True),
                                           ("lean, 1 alone", 1, True, False), ("lean, 2 at once", 2, True, False)):
                print(f"{label}...", flush=True)
                doc["trees"][label] = tree_group(n, lean, pinned, a.years, work)
                print(f"  {doc['trees'][label]['seconds']} s", flush=True)
        all_hashes = {h for g in doc["trees"].values() for h in g["hashes"]}
        doc["hashes_same"] = "all the same" if len(all_hashes) == 1 else f"DIFFERENT: {len(all_hashes)} distinct, so this test is void"
    for label, size in MICRO.items():
        print(f"benchmark, {label}...", flush=True)
        doc["micro"][label] = {c: micro_group(size, int(c)) for c in a.micro_copies.split(",")}
    text = report(doc)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "parallel_diagnosis.md").write_text(text, encoding="utf-8")
    (OUT / "parallel_diagnosis.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
