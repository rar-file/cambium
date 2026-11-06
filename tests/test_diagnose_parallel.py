"""The parallel diagnosis's parsing and report, without launching any runs."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from diagnose_parallel import core_masks_from, means_from_csv, physical_core_masks, report  # noqa: E402


def test_core_masks_keep_only_physical_cores():
    entries = [SimpleNamespace(mask=0b1100, relation=0), SimpleNamespace(mask=0b11, relation=0),
               SimpleNamespace(mask=0b1111, relation=2)]   # 2 is a cache, not a core
    assert core_masks_from(entries) == [0b11, 0b1100]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_this_pc_reports_physical_cores():
    masks = physical_core_masks()
    assert masks and all(m > 0 for m in masks)
    # no thread belongs to two cores
    combined = 0
    for m in masks:
        assert combined & m == 0
        combined |= m


def test_counter_means_skip_the_blank_first_sample_and_compute_the_clock(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text('"time","a","b","c","d","e","f"\n'
                 '"t0"," "," "," "," "," "," "\n'
                 f'"t1","{2 ** 20}","{2 ** 21}","4","50","110","3800"\n'
                 f'"t2","{3 * 2 ** 20}","{2 ** 21}","6","70","110","3800"\n')
    m = means_from_csv(p)
    assert m["disk_write_mb_s"] == 2.0
    assert m["disk_read_mb_s"] == 2.0
    assert m["hard_faults_s"] == 5.0
    assert m["cpu_busy_pct"] == 60.0
    assert m["clock_mhz"] == 4180.0


def test_report_shows_the_slowdown_against_one_run_alone():
    g1 = {"runs": 1, "mean_s": 50.0, "counters": {}}
    g2 = {"runs": 2, "mean_s": 80.0, "counters": {"clock_mhz": 4000}}
    text = report({"trees": {"full, 1 alone": g1, "full, 2 at once": g2}, "hashes_same": "all the same",
                   "micro": {"x": {"1": 10.0, "2": 5.0, "4": 2.5}}})
    assert "1.60x" in text and "0.50x" in text and "0.25x" in text


def test_report_finds_the_fastest_number_at_once():
    groups = [{"runs": 1, "mean_s": 50.0, "counters": {}}, {"runs": 8, "mean_s": 100.0, "counters": {}}]
    text = report({"scale": groups, "hashes_same": "all the same", "machine": {"cpu": "x", "cpu_threads": 16}})
    assert "| 8 | 100.0 | 2.00x | 288 |" in text
