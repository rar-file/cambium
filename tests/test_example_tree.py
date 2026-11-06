"""The example tree tool: the meshes are made only if the run matches the scored one."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import example_tree  # noqa: E402


def test_differences_read_only_the_scored_values():
    a = [{"year": 1, "height_m": 1.0, "hanging_twigs": 2}]
    b = [{"year": 1, "height_m": 1.0, "hanging_twigs": 0}]
    assert example_tree.differences(a, b) == []
    b[0]["height_m"] = 1.1
    assert len(example_tree.differences(a, b)) == 1
    assert example_tree.differences(a, a + a) == ["1 years here, 2 there"]


def test_export_then_render(tmp_path):
    first = tmp_path / "first"
    example_tree.export_ages(1, [4, 8], first, None, "betula_pendula", "sweden_open_field", [], 400_000)
    info = json.loads((first / "example.json").read_text())
    assert sorted(info["ages"]) == ["4", "8"]
    png = tmp_path / "sheet.png"
    example_tree.render(first, png, 200)
    assert png.stat().st_size > 1000
    # a mesh read back has what was written, in the model's axes, with height along z
    mesh = example_tree.load_mesh(first / "tree_age08.glb")
    assert len(mesh.vertices) == info["ages"]["8"]["crown"]["vertices"]
    assert mesh.vertices[:, 2].max() == pytest.approx(info["ages"]["8"]["height_m"], abs=0.5)
    # the check passes against itself, and stops before exporting against another seed
    again = tmp_path / "again"
    example_tree.export_ages(1, [8], again, first, "betula_pendula", "sweden_open_field", [], 400_000)
    assert (again / "tree_age08.glb").exists()
    other = tmp_path / "other"
    with pytest.raises(SystemExit):
        example_tree.export_ages(2, [8], other, first, "betula_pendula", "sweden_open_field", [], 400_000)
    assert not (other / "tree_age08.glb").exists()
