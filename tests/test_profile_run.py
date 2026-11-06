"""The profiler measures from outside: wrapped functions return what they returned,
and no time or memory is counted twice."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from profile_run import Clock, memory_by_attribute, top_entries  # noqa: E402


def test_clock_counts_each_function_only_its_own_time():
    clock = Clock()

    def inner():
        time.sleep(0.05)
        return 7

    inner_t = clock.wrap(inner, "inner")

    def outer():
        time.sleep(0.02)
        return inner_t() + 1

    assert clock.wrap(outer, "outer")() == 8
    assert clock.totals["inner"] >= 0.04
    assert clock.totals["outer"] < clock.totals["inner"]
    assert clock.calls["outer"] == clock.calls["inner"] == 1


def test_clock_keeps_exceptions_and_the_stack():
    clock = Clock()

    def boom():
        raise ValueError("x")

    try:
        clock.wrap(boom, "b")()
    except ValueError:
        pass
    assert clock._stack == []
    assert clock.calls["b"] == 1


def test_memory_counts_a_shared_array_once_and_merges_list_positions():
    a = np.zeros(1000)
    view = a[:10]
    o = SimpleNamespace(first=a, second=a, view=view, many=[np.zeros(100), np.zeros(100)])
    s = memory_by_attribute(o, "m")
    assert s["m.first"] == a.nbytes
    assert "m.second" not in s and "m.view" not in s
    assert s["m.many[*]"] >= 2 * 800
    assert top_entries(s, 1)[0]["what"] == "m.first"
