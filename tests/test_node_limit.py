"""The node's CPU check: over 1 core used by others means 8 at once, otherwise 14."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from node_limit import own_ticks_of, runs_at_once, total_busy_ticks  # noqa: E402


def test_the_rule():
    assert runs_at_once(0.0) == 14
    assert runs_at_once(1.0) == 14   # "above 1 core"
    assert runs_at_once(1.01) == 8
    assert runs_at_once(7.0) == 8


def test_busy_time_leaves_out_idle_and_io_wait():
    text = "cpu  100 20 30 5000 40 5 6 7 0 0\ncpu0 1 2 3 4 5 6 7 8 0 0\n"
    assert total_busy_ticks(text) == 100 + 20 + 30 + 5 + 6 + 7


def test_process_time_survives_a_name_with_spaces_and_brackets():
    line = "123 (a b) c) S 1 2 3 4 5 6 7 8 9 10 111 222 13 14 15\n"
    assert own_ticks_of(line) == 111 + 222
