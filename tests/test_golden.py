"""The golden-run hashes: run metadata stays out, model output stays in."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from golden import RUNS, compare, hash_file, hash_tree  # noqa: E402


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
