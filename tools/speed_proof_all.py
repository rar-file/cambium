"""On the node, one job: the proof that the six speed settings change nothing, on the settings the model is really run on.

    CORES=4 tools/node/submit.sh <commit> node_speed_proof tools/speed_proof_all.py node_speed_proof

Golden runs off and on (default settings); then stand trees on the Crown agent's settings, seeds 1-6 to 60; then a 25-tree plot on
them to 60.  Results in out/bench/ensemble/<label>: golden_compare.txt and drift.txt.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

label = sys.argv[1]
workers = os.environ.get("ORIGIN_MAX_WORKERS", "2")
SIX = ["speed.compiled_carbon=true", "speed.compiled_mechanics=true", "speed.light_layers=true", "speed.keep_soil_grids=true", "speed.quick_solve=true", "speed.quick_levels=true"]
codes = []
codes.append(subprocess.run([sys.executable, "tools/speed_node_proof.py", label] + [x for s in SIX for x in ("--set", s)], cwd=ROOT).returncode)
codes.append(subprocess.run([sys.executable, "tools/speed_drift.py", "--seeds", "1,2,3,4,5,6", "--years", "60", "--only", "six", "--workers", workers, "--label", label], cwd=ROOT).returncode)
codes.append(subprocess.run([sys.executable, "tools/speed_drift.py", "--seeds", "1", "--years", "60", "--plot-trees", "25", "--only", "six", "--workers", "2", "--label", label], cwd=ROOT).returncode)
print("exit codes", codes, flush=True)
sys.exit(max(codes))
