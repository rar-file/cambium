"""How many runs at once on the node (PROTOCOL.md section 6; the maintainer, 2026-11-06).

Before each batch, measure the CPU used by every process that isn't ours, averaged over a
minute.  Above 1 core, run 8 at once; otherwise 14.  The node runs other services, and
they come first.  Reads /proc only; changes nothing.

    python tools/node_limit.py          # prints the number, for ORIGIN_MAX_WORKERS
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ABOVE_LIMIT, NORMAL = 8, 14
THRESHOLD_CORES = 1.0
WINDOW_S = 60.0


def total_busy_ticks(text: str) -> int:
    """All busy CPU time from /proc/stat's first line: everything but idle and I/O wait."""
    fields = text.splitlines()[0].split()
    if fields[0] != "cpu":
        raise ValueError("unexpected /proc/stat")
    v = [int(x) for x in fields[1:9]]   # user nice system idle iowait irq softirq steal
    return v[0] + v[1] + v[2] + v[5] + v[6] + v[7]


def own_ticks_of(stat_line: str) -> int:
    """utime + stime from one /proc/PID/stat line; the name may hold spaces and brackets."""
    after = stat_line[stat_line.rindex(")") + 2:].split()
    return int(after[11]) + int(after[12])


def our_ticks(uid: int, proc: Path = Path("/proc")) -> dict:
    out = {}
    for d in proc.iterdir():
        if not d.name.isdigit():
            continue
        try:
            if d.stat().st_uid == uid:
                out[d.name] = own_ticks_of((d / "stat").read_text())
        except OSError:   # gone already
            pass
    return out


def others_cores(window_s: float = WINDOW_S) -> float:
    """Cores used by processes that aren't this user's, averaged over the window."""
    uid = os.getuid()
    hz = os.sysconf("SC_CLK_TCK")
    busy0, ours0 = total_busy_ticks(Path("/proc/stat").read_text()), our_ticks(uid)
    t0 = time.time()
    time.sleep(window_s)
    busy1, ours1 = total_busy_ticks(Path("/proc/stat").read_text()), our_ticks(uid)
    ours = sum(v - ours0.get(k, 0) for k, v in ours1.items())
    return max(0.0, busy1 - busy0 - ours) / hz / (time.time() - t0)


def runs_at_once(cores_used_by_others: float) -> int:
    return ABOVE_LIMIT if cores_used_by_others > THRESHOLD_CORES else NORMAL


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--window", type=float, default=WINDOW_S)
    a = ap.parse_args()
    if sys.platform == "win32":
        sys.exit("this is for the node")
    cores = others_cores(a.window)
    n = runs_at_once(cores)
    print(f"others use {cores:.2f} cores over {a.window:.0f} s: {n} at once", file=sys.stderr)
    print(n)


if __name__ == "__main__":
    main()
