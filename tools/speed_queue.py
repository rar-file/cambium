"""The speed study's runs, one set after another, on the cores the job was given (node: tools/node/submit.sh with CORES=5).

    python tools/speed_queue.py list
    python tools/speed_queue.py trees A_base A_base2 A_rows ...     # names from SETS below
    python tools/speed_queue.py plots A_base A_rows ...

Every set runs with the lossless settings on, which give the same bits and take less time.  Trees: 20 seeds, to 60, through
tools/tree_table.py.  Plots: 5 plots of 100 trees, natural, to 60, no saves, through tools/ensemble.py.  Labels are
node_speed_t_<name> and node_speed_p_<name>.  A set that's finished is skipped, so a job can be run again.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from speed_compare import TEST_A  # noqa: E402

LOSSLESS = ["speed.compiled_carbon=true", "speed.compiled_mechanics=true", "speed.light_layers=true", "speed.keep_soil_grids=true", "speed.quick_solve=true", "speed.quick_levels=true"]
ROWS = ["speed.light_rows=true"]
DROP = ["speed.drop_dead=true"]
K26 = ["speed.sky_elevations_deg=[15,45,75]", "speed.sky_azimuth_count=8", "speed.sun_hour_step=2.0"]     # 16 sky, 8 sun at this site
K14 = ["speed.sky_elevations_deg=[25,65]", "speed.sky_azimuth_count=6", "speed.sun_hour_step=3.0"]        # 8 sky, 6 sun

# name -> (settings, first seed)
SETS = {
    "D_base": ([], 1), "D_base2": ([], 21),
    "A_base": (TEST_A, 1), "A_base2": (TEST_A, 21), "A_base3": (TEST_A, 41),
    "D_rows": (ROWS, 1), "D_rows2": (ROWS, 21),
    "A_rows": (TEST_A + ROWS, 1), "A_rows2": (TEST_A + ROWS, 21),
    "A_droponly": (TEST_A, 1), "D_droponly": ([], 1),
    "A_k26": (TEST_A + ROWS + K26, 1), "A_k14": (TEST_A + ROWS + K14, 1),
    "A_every2": (TEST_A + ROWS + ["speed.light_every=2"], 1), "A_every3": (TEST_A + ROWS + ["speed.light_every=3"], 1),
    "A_vox15": (TEST_A + ROWS + ["light.voxel_size=0.15"], 1), "A_vox20": (TEST_A + ROWS + ["light.voxel_size=0.2"], 1),
    "A_cell3": (TEST_A + ROWS + ["stand.cell_trees=3"], 1), "A_probe16": (TEST_A + ROWS + ["light.perception_samples=16"], 1),
    "D_k26": (ROWS + K26, 1), "D_every2": (ROWS + ["speed.light_every=2"], 1), "D_vox20": (ROWS + ["light.voxel_size=0.2"], 1),
}


def speedy(name: str) -> list:
    """Every set runs on the lossless settings; all but the two baselines the drop is checked against also drop dead nodes."""
    return LOSSLESS if name in ("A_base", "D_base") else LOSSLESS + DROP


PREFIX = "pc_speed" if sys.platform == "win32" else "node_speed"      # PC and server results are never compared


def trees(name: str) -> int:
    sets, first = SETS[name]
    label = f"{PREFIX}_t_{name}"
    cmd = [sys.executable, str(ROOT / "tools" / "tree_table.py"), "run", "--label", label, "--seeds", "20", "--first-seed", str(first), "--years", "60"]
    for s in speedy(name) + sets:
        cmd += ["--set", s]
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def plots(name: str) -> int:
    sets, first = SETS[name]
    label = f"{PREFIX}_p_{name}"
    cmd = [sys.executable, str(ROOT / "tools" / "ensemble.py"), "plots", "--label", label, "--seeds", "5", "--first-seed", str(1 if first == 1 else 6), "--years", "60",
           "--mode", "natural", "--trees", "25", "--no-saves"]
    for s in speedy(name) + sets:
        cmd += ["--set", s]
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def main():
    what, names = sys.argv[1], sys.argv[2:]
    if what == "list":
        for k, v in SETS.items():
            print(k, v)
        return
    for name in names:
        print(f"=== {what} {name}", flush=True)
        code = (trees if what == "trees" else plots)(name)
        print(f"=== {what} {name}: exit {code}", flush=True)


if __name__ == "__main__":
    main()
