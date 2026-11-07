"""On the node, through submit.sh: copy another commit's out/bench/speed/*.json into this copy's out/bench/ensemble/<label>,
where tools/node/fetch.sh can reach them.

    tools/node/submit.sh <commit> node_speed_prof tools/speed_collect.py node_speed_prof a12ff3b
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

label, commits = sys.argv[1], sys.argv[2:]
out = ROOT / "out" / "bench" / "ensemble" / label
out.mkdir(parents=True, exist_ok=True)
for commit in commits:
    src = ROOT.parent / f"repo_{commit}" / "out" / "bench" / "speed"
    for f in sorted(src.glob("*.json")):
        shutil.copy(f, out / f.name)
        print("copied", f.name, flush=True)
