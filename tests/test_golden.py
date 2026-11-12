"""The golden-run hashes: run metadata stays out, model output stays in."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from golden import RUNS, check, compare, hash_file, hash_tree, record, track  # noqa: E402


def _glb(path, extras, payload=b"12345678"):
    doc = {"asset": {"version": "2.0", "extras": extras}}
    js = json.dumps(doc).encode()
    js += b" " * (-len(js) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(payload)))
        f.write(struct.pack("<I4s", len(js), b"JSON"))
        f.write(js)
        f.write(struct.pack("<I4s", len(payload), b"BIN\x00"))
        f.write(payload)


def test_an_option_that_is_off_leaves_the_hash_alone(tmp_path):
    a, b, c, d, e = (tmp_path / f"{n}.json" for n in "abcde")
    a.write_text(json.dumps({"x": 1.5, "options": {"old": True}}))
    b.write_text(json.dumps({"x": 1.5, "options": {"old": True, "new": False}}))
    c.write_text(json.dumps({"x": 1.5, "options": {"old": True, "new": True}}))
    d.write_text(json.dumps({"x": 1.5, "options": {"old": True, "new": 2}}))
    e.write_text(json.dumps({"x": 1.6, "options": {"old": True, "new": False}}))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)   # on counts
    assert hash_file(a) != hash_file(d)   # a value counts
    assert hash_file(b) != hash_file(e)   # a number still counts


def test_json_hash_ignores_run_metadata_only(tmp_path):
    a, b, c = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "c.json"
    a.write_text(json.dumps({"x": 1.5, "run_manifest": {"git_commit": "aaa"}, "nested": {"peak_mb": 10, "y": 2}}))
    b.write_text(json.dumps({"nested": {"y": 2, "peak_mb": 99}, "run_manifest": {"git_commit": "bbb"}, "x": 1.5}))
    c.write_text(json.dumps({"x": 1.5000000000000002, "run_manifest": {"git_commit": "aaa"}, "nested": {"peak_mb": 10, "y": 2}}))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)   # one bit in the last digit counts


def test_glb_hash_ignores_the_manifest_in_extras_but_not_the_mesh(tmp_path):
    a, b, c = tmp_path / "a.glb", tmp_path / "b.glb", tmp_path / "c.glb"
    _glb(a, {"run_manifest": {"git_commit": "aaa"}, "seed": 1})
    _glb(b, {"run_manifest": {"git_commit": "bbb"}, "seed": 1})
    _glb(c, {"run_manifest": {"git_commit": "aaa"}, "seed": 1}, payload=b"12345679")
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)


def test_npz_hash_covers_values_types_and_shapes(tmp_path):
    a, b, c, d = (tmp_path / f"{n}.npz" for n in "abcd")
    np.savez(a, x=np.arange(4.0))
    np.savez(b, x=np.arange(4.0))
    np.savez(c, x=np.arange(4.0, dtype=np.float32))
    np.savez(d, x=np.arange(4.0).reshape(2, 2))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)
    assert hash_file(a) != hash_file(d)


def test_tree_hash_skips_metadata_files_and_checkpoints(tmp_path):
    (tmp_path / "history").mkdir()
    (tmp_path / "history" / "history_005.npz").write_bytes(b"x")
    (tmp_path / "manifest.json").write_text("{}")
    (tmp_path / "checkpoint.pkl").write_bytes(b"x")
    (tmp_path / "run.log").write_text("x")
    (tmp_path / "stats.json").write_text("{}")
    assert list(hash_tree(tmp_path)) == ["stats.json"]


def test_compare_finds_a_changed_and_a_missing_file():
    a = {"runs": {"r": {"files": {"x": "1", "y": "2"}, "seconds": 1, "peak_mb": 1}}}
    b = {"runs": {"r": {"files": {"x": "1", "y": "3", "z": "4"}, "seconds": 2, "peak_mb": 2}}}
    same, lines, _ = compare(a, b)
    assert not same
    assert any("differs: y" in x for x in lines) and any("in one only: z" in x for x in lines)
    assert compare(a, a)[0]


def test_the_four_golden_runs_are_defined():
    assert set(RUNS) == {"tree60", "mesh30", "plot25", "regen10"}


def test_a_forest_years_seconds_and_memory_are_left_out_but_not_its_trees(tmp_path):
    a, b, c = (tmp_path / f"{n}.json" for n in "abc")
    a.write_text(json.dumps({"year_log": [[1, 5.4, 571, 3, 40, 170, 40]]}))
    b.write_text(json.dumps({"year_log": [[1, 9.9, 999, 3, 40, 170, 40]]}))
    c.write_text(json.dumps({"year_log": [[1, 5.4, 571, 3, 41, 170, 40]]}))
    assert hash_file(a) == hash_file(b)
    assert hash_file(a) != hash_file(c)


def _recording(files, python="3.14.7"):
    return {"commit": "abc1234", "machine": {"cpu": "Some CPU", "architecture": "x", "cpu_threads": 4, "numpy_openblas_kernel": "k",
                                             "math_libraries": {"python": python, "numpy": "2", "scipy": "1", "numba": "0", "llvmlite": "0"}},
            "runs": {name: {"seconds": 1.0, "peak_mb": 10.0, "files": f} for name, f in files.items()}}


def test_check_passes_only_on_an_exact_match(tmp_path):
    tracked = track(_recording({"a": {"x.json": "1", "y.npz": "2"}, "b": {"z.json": "3"}}), path=tmp_path / "server.json")
    same, lines = check(_recording({"a": {"x.json": "1", "y.npz": "2"}, "b": {"z.json": "3"}}), tracked)
    assert same and lines == ["same: a, 2 files tracked; 1.0 s and 10.0 MB (tracked: 1.0 s, 10.0 MB)",
                              "same: b, 1 files tracked; 1.0 s and 10.0 MB (tracked: 1.0 s, 10.0 MB)"]
    same, lines = check(_recording({"a": {"x.json": "1", "y.npz": "9", "w.json": "4"}, "c": {"z.json": "3"}}), tracked)
    assert not same
    assert "  DIFFERS: a/y.npz" in lines and "  NEW: a/w.json" in lines
    assert "MISSING: b, tracked but not in the recording" in lines and "NEW: c, in the recording but not tracked" in lines
    same, lines = check(_recording({"a": {"x.json": "1"}, "b": {"z.json": "3"}}), tracked)
    assert not same and "  MISSING: a/y.npz" in lines


def test_check_fails_when_nothing_is_compared(tmp_path):
    empty = {"runs": {}}
    same, lines = check(empty, empty)
    assert not same and "NOTHING COMPARED: the tracked file has no runs" in lines
    tracked = track(_recording({"a": {"x.json": "1"}}), path=tmp_path / "server.json")
    same, lines = check(_recording({}), tracked)
    assert not same and "NOTHING COMPARED: the recording has no runs" in lines
    same, lines = check({"runs": {"a": {"files": {"x.json": "1"}}}}, {"runs": {}})
    assert not same and "NOTHING COMPARED: the tracked file has no runs" in lines
    tracked = track(_recording({"a": {}, "b": {"z.json": "3"}}), path=tmp_path / "server2.json")
    same, lines = check(_recording({"a": {}, "b": {"z.json": "3"}}), tracked)
    assert not same and "  NOTHING COMPARED: a has no files on either side" in lines


def test_a_recording_from_another_commit_is_not_added_to(tmp_path):
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "hashes.json").write_text(json.dumps({"commit": "0000000", "runs": {"tree60": {"files": {"x": "1"}}}}))
    with pytest.raises(SystemExit, match="use a new label"):
        record("old", ["mesh30"], root=tmp_path)     # refused before anything runs


def test_check_says_so_when_python_or_a_library_differs(tmp_path):
    tracked = track(_recording({"a": {"x.json": "1"}}), path=tmp_path / "server.json")
    same, lines = check(_recording({"a": {"x.json": "1"}}, python="3.13.0"), tracked)
    assert same      # the hashes still decide
    assert lines[0].startswith("Python is 3.13.0 in this recording and 3.14.7 in the tracked file")
    other = _recording({"a": {"x.json": "1"}})
    other["machine"]["math_threads"] = {"numpy_openblas": 4}
    same, lines = check(other, tracked)
    assert same and lines[0].startswith("the number of maths threads is {'numpy_openblas': 4} in this recording and not recorded")


def test_adding_runs_to_the_tracked_file_keeps_the_others(tmp_path):
    path = tmp_path / "server.json"
    track(_recording({"a": {"x.json": "1"}}), path=path)
    doc = track(_recording({"a": {"x.json": "changed"}, "b": {"z.json": "3"}}), only=["b"], path=path)
    assert doc["runs"]["a"]["files"] == {"x.json": "1"} and doc["runs"]["b"]["files"] == {"z.json": "3"}
    assert json.loads(path.read_text(encoding="utf-8")) == doc
    with pytest.raises(SystemExit):
        track(_recording({"c": {"z.json": "3"}}, python="3.13.0"), only=["c"], path=path)


def test_the_tracked_file_holds_every_golden_run_and_its_commit():
    doc = json.loads((Path(__file__).resolve().parent.parent / "cases" / "golden_server.json").read_text(encoding="utf-8"))
    assert set(RUNS) <= set(doc["runs"]) and all(r["commit"] and r["files"] for r in doc["runs"].values())


# -- the exports among the golden runs, and a tracked file that 'track' alone writes ---------------------------------------
from golden import MORE_RUNS, made_on, main, unsaid  # noqa: E402


def _whole_recording(files, label="node_x_gold"):
    """A recording as 'record' writes one now: with its label, and every part of made_on."""
    rec = _recording(files)
    rec["label"] = label
    rec["machine"]["math_libraries"].update(numpy_blas="openblas 1", scipy_blas="openblas 2")
    rec["machine"]["math_threads"] = {"numpy_openblas": 1, "scipy_openblas": 1}
    return rec


def test_the_exports_are_golden_runs():
    unreal, usd = MORE_RUNS["unreal30"][0], MORE_RUNS["usd_open30"][0]
    assert unreal[:2] == ["tools/game_export.py", "export"] and "unreal" in unreal and "--no-textures" in unreal and "--open" not in unreal
    # the public command, as a user types it, on an open-grown tree
    assert usd[:3] == ["-m", "cambium", "export"] and usd[usd.index("--format") + 1] == "usd" and not {"--forest", "--stand"} & set(usd)


def test_the_tracked_file_is_rebuilt_from_a_recording_alone(tmp_path):
    path = tmp_path / "server.json"
    path.write_text(json.dumps({"about": "old", "note": "written by hand", "made_on": {"libraries": {"llvmlite": "by hand"}}, "runs": {"gone": {"files": {"x": "1"}}}}))
    rec = _whole_recording({"a": {"x.json": "1"}, "b": {"z.json": "3"}})
    assert unsaid(rec) == []
    doc = track(rec, path=path)
    assert set(doc) == {"about", "made_on", "runs"} and set(doc["runs"]) == {"a", "b"}        # nothing of the old file is left
    assert doc["made_on"] == made_on(rec) and doc["made_on"]["libraries"]["llvmlite"] == "0"
    assert doc["runs"]["a"] == {"commit": "abc1234", "recording": "node_x_gold", "seconds": 1.0, "cpu_seconds": None, "peak_mb": 10.0, "files": {"x.json": "1"}}
    assert json.loads(path.read_text(encoding="utf-8")) == doc and check(rec, doc) == (True, [
        "same: a, 1 files tracked; 1.0 s and 10.0 MB (tracked: 1.0 s, 10.0 MB)", "same: b, 1 files tracked; 1.0 s and 10.0 MB (tracked: 1.0 s, 10.0 MB)"])
    # a run added later from another recording says where it came from, and the rest stay
    doc = track(_whole_recording({"c": {"w.json": "4"}}, label="node_y_gold"), only=["c"], path=path)
    assert [doc["runs"][k]["recording"] for k in "abc"] == ["node_x_gold", "node_x_gold", "node_y_gold"] and doc["runs"]["a"]["files"] == {"x.json": "1"}


def test_the_tracked_file_is_as_track_writes_it():
    doc = json.loads((Path(__file__).resolve().parent.parent / "cases" / "golden_server.json").read_text(encoding="utf-8"))
    assert set(doc) == {"about", "made_on", "runs"}                      # no note beside what 'track' writes
    assert set(doc["runs"]) <= set(RUNS) | set(MORE_RUNS) and {"unreal30", "usd_open30"} <= set(doc["runs"])
    assert all(r["recording"].startswith("node_") and r["commit"] for r in doc["runs"].values())
    assert doc["made_on"]["python"] and all(doc["made_on"]["libraries"].values())


def test_track_refuses_a_recording_that_leaves_something_out(tmp_path, monkeypatch):
    rec = _whole_recording({"a": {"x.json": "1"}})
    del rec["label"], rec["machine"]["math_libraries"]["llvmlite"]
    assert unsaid(rec) == ["label", "llvmlite"]
    (tmp_path / "hashes.json").write_text(json.dumps(rec))
    monkeypatch.setattr(sys, "argv", ["golden.py", "track", str(tmp_path / "hashes.json"), "--file", str(tmp_path / "server.json")])
    with pytest.raises(SystemExit, match="Not tracked: the recording doesn't say its label, llvmlite, and nothing in the tracked file is written in by hand"):
        main()
    assert not (tmp_path / "server.json").exists()
