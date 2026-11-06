"""Run independent light runs in parallel (campaign P0, step 3).

Each job is a separate, unchanged process: nothing is shared between them, and
this file only decides when to start them.  PROTOCOL.md section 6: on the main PC
light runs (single trees, under 1 GB each) may run in parallel within the free-memory
floor, and heavy runs (plots, mesh exports) stay one at a time, so don't send them
here.  On the node, ORIGIN_FLOOR_GB and ORIGIN_MAX_WORKERS set its limits.

Before every launch it reads free memory, allows for what the jobs already running
may still grow to, and doesn't launch if that would break the floor.  If nothing is
running and the floor still blocks a launch, it waits, then gives up with exit code
3.  A job counts as done when its result file exists, so a batch can be stopped and
started again.
"""
from __future__ import annotations

import csv
import ctypes
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FLOOR_GB = float(os.environ.get("ORIGIN_FLOOR_GB", 4.0))  # PROTOCOL.md section 6


@dataclass
class Job:
    name: str
    cmd: list
    done: Path


def free_gb() -> float:
    """Physical memory available now (GB): what the system reports as available."""
    if sys.platform != "win32":
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 1024 ** 2
        raise OSError("no MemAvailable in /proc/meminfo")

    class M(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 1024 ** 3


def process_memory_gb(proc: subprocess.Popen, peak: bool = False) -> float | None:
    """Memory a running child holds now, or its peak so far (GB); None if unreadable."""
    if sys.platform != "win32":
        try:
            key = "VmHWM:" if peak else "VmRSS:"
            for line in Path(f"/proc/{proc.pid}/status").read_text().splitlines():
                if line.startswith(key):
                    return int(line.split()[1]) / 1024 ** 2
        except OSError:
            pass
        return None
    import ctypes.wintypes as wt

    class PMC(ctypes.Structure):
        _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t)]
    f = ctypes.WinDLL("kernel32").K32GetProcessMemoryInfo
    f.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
    f.restype = wt.BOOL
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    if not f(wt.HANDLE(int(proc._handle)), ctypes.byref(c), c.cb):
        return None
    return (c.PeakWorkingSetSize if peak else c.WorkingSetSize) / 1024 ** 3


def working_set_gb(proc: subprocess.Popen) -> float:
    """Memory a running child holds now (GB); 0 if it can't be read."""
    return process_memory_gb(proc) or 0.0


def default_workers() -> int:
    """CPU cores minus one; os.cpu_count() counts threads, two per core on the main
    PC.  ORIGIN_MAX_WORKERS replaces this on the node."""
    if os.environ.get("ORIGIN_MAX_WORKERS"):
        return int(os.environ["ORIGIN_MAX_WORKERS"])
    return max(1, (os.cpu_count() or 2) // 2 - 1)


def run_batch(jobs: list, peak_gb: float, workers: int | None = None, floor_gb: float = FLOOR_GB,
              log: Path | None = None, settle_s: float = 3.0, max_wait_s: float = 1800.0) -> int:
    """Run the jobs not yet done.  Returns 0, or 3 if the floor blocked everything
    for max_wait_s with nothing running.  peak_gb: one job's peak memory."""
    workers = workers or default_workers()
    pending = [j for j in jobs if not j.done.exists()]
    total = len(pending)
    print(f"{total} jobs to run, {len(jobs) - total} already done; up to {workers} at once, "
          f"{peak_gb:.2f} GB each, floor {floor_gb:g} GB", flush=True)
    new_log = log is not None and not log.exists()
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
    running: list = []
    t_start = time.time()
    t_blocked = None
    last_launch = 0.0
    finished = 0
    while pending or running:
        for item in running[:]:
            job, proc, t0, stamp, free0, n0 = item
            code = proc.poll()
            if code is None:
                continue
            running.remove(item)
            finished += 1
            secs = time.time() - t0
            if code != 0:
                job.done.with_name(job.done.name + ".failed").write_text(f"exit {code}\n")
            print(f"[{finished}/{total}] {job.name}: {'ok' if code == 0 else f'FAILED, exit {code}'} in {secs:.0f} s, "
                  f"{free0:.2f} GB free at launch, {n0} others running", flush=True)
            if log is not None:
                with open(log, "a", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    if new_log:
                        w.writerow(["job", "started", "seconds", "exit", "free_gb_at_launch", "others_running"])
                        new_log = False
                    w.writerow([job.name, stamp, f"{secs:.1f}", code, f"{free0:.2f}", n0])
        if pending and len(running) < workers and time.time() - last_launch >= settle_s:
            # memory the running jobs may still take, on top of what they hold
            still = sum(max(0.0, peak_gb - working_set_gb(p)) for _, p, *_ in running)
            free = free_gb()
            if free - still - peak_gb >= floor_gb:
                job = pending.pop(0)
                job.done.parent.mkdir(parents=True, exist_ok=True)
                proc = subprocess.Popen(job.cmd, cwd=str(ROOT))
                running.append((job, proc, time.time(), datetime.now().isoformat(timespec="seconds"), free, len(running)))
                last_launch = time.time()
                t_blocked = None
            elif not running:
                t_blocked = t_blocked or time.time()
                if time.time() - t_blocked > max_wait_s:
                    print(f"STOP: {free:.2f} GB free for {max_wait_s / 60:.0f} minutes, and a run needs "
                          f"{floor_gb + peak_gb:.2f} GB free (PROTOCOL.md section 6). Finished runs are kept.", flush=True)
                    return 3
        time.sleep(0.5)
    took = time.time() - t_start
    if total:
        print(f"batch done: {total} jobs in {took:.0f} s, {took / total:.1f} s per job", flush=True)
    return 0


if __name__ == "__main__":
    print(f"free now {free_gb():.2f} GB; default workers {default_workers()}")
    sys.exit(0)
