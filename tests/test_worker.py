"""The second-PC kit: same commands as the golden runs, and it refuses different versions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from golden import RUNS  # noqa: E402
from worker import load_cases, locked_versions, version_problems  # noqa: E402


def test_golden_case_list_is_the_same_as_the_golden_runs():
    cases = {c["name"]: c for c in load_cases(ROOT / "cases" / "golden.json")}
    assert set(cases) == set(RUNS)
    for name, (command, peak) in RUNS.items():
        assert cases[name]["args"] == command
        assert cases[name]["peak_gb"] == peak


def test_the_lock_file_pins_the_versions_that_can_change_results():
    locked = locked_versions()
    for name in ("numpy", "scipy", "numba", "llvmlite", "usd-core"):
        assert name in locked, name


def test_a_different_version_is_reported():
    assert version_problems({"numpy": "0.0.1"}, python="3.14.7") == [f"numpy is {__import__('numpy').__version__}, needs 0.0.1"]
    assert any("isn't installed" in p for p in version_problems({"no-such-package-here": "1"}, python="3.14.7"))
    assert any(p.startswith("Python is 3.12") for p in version_problems({}, python="3.12.0"))


def test_this_pc_matches_the_lock_file():
    assert version_problems() == []


def test_a_case_may_only_run_the_model(tmp_path):
    p = tmp_path / "cases.json"
    p.write_text(json.dumps({"cases": [{"name": "x", "args": ["something_else.py"]}]}))
    with pytest.raises(SystemExit):
        load_cases(p)
