"""A finished case isn't run twice, and anything its result depends on changes the key."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from run_cache import Cache, case_key, code_version  # noqa: E402


def test_cache_key_changes_with_everything_a_result_depends_on():
    sp, env = SimpleNamespace(a=SimpleNamespace(b=1.0)), {"e": 1}
    code, mach = "code", {"math_threads": {"x": 1}}
    k = case_key("screen", sp, env, 1, 60, True, code=code, machine=mach)
    assert k == case_key("screen", SimpleNamespace(a=SimpleNamespace(b=1.0)), {"e": 1}, 1, 60, True, code=code, machine=mach)
    assert k != case_key("screen", SimpleNamespace(a=SimpleNamespace(b=1.0000000000000002)), env, 1, 60, True, code=code, machine=mach)
    assert k != case_key("screen", sp, {"e": 2}, 1, 60, True, code=code, machine=mach)
    assert k != case_key("screen", sp, env, 2, 60, True, code=code, machine=mach)
    assert k != case_key("screen", sp, env, 1, 30, True, code=code, machine=mach)
    assert k != case_key("screen", sp, env, 1, 60, False, code=code, machine=mach)
    assert k != case_key("screen", sp, env, 1, 60, True, code="other", machine=mach)
    assert k != case_key("screen", sp, env, 1, 60, True, code=code, machine={"math_threads": {"x": 16}})


def test_code_version_changes_with_the_model_code(tmp_path):
    (tmp_path / "treegen").mkdir()
    (tmp_path / "treegen" / "a.py").write_text("x = 1\n")
    (tmp_path / "cli.py").write_text("y = 1\n")
    v = code_version(tmp_path)
    (tmp_path / "treegen" / "a.py").write_text("x = 2\n")
    assert code_version(tmp_path) != v


def test_cache_returns_what_was_stored(tmp_path):
    c = Cache(tmp_path)
    assert c.get("ab" * 32) is None
    c.put("ab" * 32, {"30": {"height_m": 1.5}})
    assert c.get("ab" * 32) == {"30": {"height_m": 1.5}}
