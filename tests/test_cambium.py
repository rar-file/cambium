"""The cambium package: a facade that must change nothing about the tree it grows."""
from __future__ import annotations

import csv
import io
import json
import sys
import tomllib
from argparse import Namespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cambium  # noqa: E402
from cambium import _engine  # noqa: E402
from cambium._forest import plot_settings  # noqa: E402
from cambium._species import species_file  # noqa: E402
from cambium._stats import Stats  # noqa: E402
from cambium._tree import settings_items  # noqa: E402
from cambium.cli import main  # noqa: E402

# small textures and budgets, so a whole game export takes seconds (as tests/test_game_export.py)
SMALL_LOOK = {"bark.tile_px": 256, "bark.stem_texture_px": [128, 512], "bark.atlas_px": [512, 256], "game.leaf_card.texture_px": 256,
              "game.lods": [{"name": "lod0", "kind": "full", "budget": None, "stem_texture_scale": 1.0, "atlas_scale": 1.0, "leaf_kind": "blades", "peel_strips": 1},
                            {"name": "lod1", "kind": "reduced", "budget": 4000, "wood_share": 0.4, "stem_texture_scale": 0.5, "atlas_scale": 0.5, "leaf_kind": "cards", "peel_strips": 0},
                            {"name": "lod2", "kind": "far", "budget": 12, "cards": 3, "texture_px": 128}]}


@pytest.fixture(scope="module")
def tree():
    return cambium.grow(seed=1, years=5)


def test_the_version_is_the_one_in_pyproject():
    with open(ROOT / "pyproject.toml", "rb") as f:
        assert tomllib.load(f)["project"]["version"] == cambium.__version__


def test_a_checkout_uses_its_own_files():
    assert _engine.SOURCE
    assert _engine.SPECIES_DIR == ROOT / "species"
    assert _engine.script_path("cli") == ROOT / "cli.py"


def test_species_are_listed_with_their_labels():
    sp = {s.name: s for s in cambium.species()}
    birch = sp["betula_pendula"]
    assert birch.scientific_name.startswith("Betula pendula")
    assert "birch" in birch.aliases
    assert set(birch.labels) == {"sourced", "DERIVED", "TUNED", "VERIFY"} and sum(birch.labels.values()) > 0
    assert "_template" not in sp


def test_names_aliases_and_paths_find_the_same_file():
    f = ROOT / "species" / "betula_pendula.yaml"
    assert species_file("betula_pendula") == species_file("birch") == species_file("Silver_Birch") == species_file(str(f)) == f.resolve()
    with pytest.raises(ValueError, match="unknown species"):
        species_file("oak")
    with pytest.raises(ValueError):
        species_file("_template")


def test_settings_become_the_engines_items():
    assert settings_items({"resource__alpha": 4.5, "light.woody_shade.enabled": True, "x.y": [1, 2]}) == \
        ["resource.alpha=4.5", "light.woody_shade.enabled=true", "x.y=[1, 2]"]


def test_grow_gives_the_same_tree_as_cli_grow(tree):
    cli = _engine.load("cli")
    model, _ = cli.grow("betula_pendula", 1, 5, "sweden_open_field")
    assert json.dumps(tree.stats) == json.dumps(model.stats)


def test_keeping_leaves_at_earlier_ages_changes_nothing(tree):
    staged = cambium.grow(seed=1, years=5, stages=(2, 4))
    assert json.dumps(staged.stats) == json.dumps(tree.stats)
    assert sorted(staged._snapshots) == [2, 4, 5]


def test_a_tree_reads_its_last_year(tree):
    last = tree.stats[-1]
    assert tree.age == 5 == last["year"] and len(tree.stats) == 6
    assert tree.height_m == last["height_m"] > 0 and tree.dbh_cm == last["dbh_cm"]
    assert "seed 1" in repr(tree)


def test_a_setting_that_isnt_there_is_refused():
    with pytest.raises(KeyError, match="no such parameter"):
        cambium.grow(seed=1, years=1, resource__no_such_value=1)


def test_stats_as_json_and_csv(tmp_path):
    s = Stats([{"year": 0, "height_m": 0.1, "dbh_cm": None, "water": {}, "five": [1, 2]},
               {"year": 1, "height_m": 0.3, "dbh_cm": 0.2, "water": {"psi": -0.5}, "five": [3]}])
    assert json.loads(s.to_json()) == list(s)
    rows = list(csv.DictReader(io.StringIO(s.to_csv(tmp_path / "a.csv"))))
    assert list(rows[0]) == ["year", "height_m", "dbh_cm", "five", "water.psi"]
    assert rows[0]["dbh_cm"] == "" and rows[1]["water.psi"] == "-0.5" and json.loads(rows[0]["five"]) == [1, 2]
    assert (tmp_path / "a.csv").read_text(encoding="utf-8") == s.to_csv()


def test_save_writes_stats_as_cli_does(tree, tmp_path):
    files = tree.save(tmp_path)
    doc = json.loads((tmp_path / "stats.json").read_text(encoding="utf-8"))
    assert doc["format"] == "treegen.stats/1" and doc["per_year"] == json.loads(tree.to_json())
    assert doc["reference"] and doc["run_manifest"]["cambium_version"] == cambium.__version__
    assert [p.name for p in files] == ["stats.json", "stats.csv"]


def test_loading_the_engine_scripts_leaves_no_trace():
    path, before = list(sys.path), {n: sys.modules.get(n) for n in ("cli", "tree_list")}
    _engine.load.cache_clear()
    ge = _engine.load("game_export")
    assert hasattr(ge, "export_stage") and ge.cli is _engine.load("cli")
    assert sys.path == path and {n: sys.modules.get(n) for n in ("cli", "tree_list")} == before


def test_usd_export(tree, tmp_path):
    files = tree.export(tmp_path, format="usd")
    assert [p.name for p in files] == ["tree.usdc", "tree_reduced.usdc"] and all(p.is_file() for p in files)
    assert (tmp_path / "tree.glb").is_file()
    assert [p.name for p in tree.export(tmp_path / "b", format="usd", lod="lod1")] == ["tree_reduced.usdc"]
    with pytest.raises(ValueError):
        tree.export(tmp_path, format="usd", lod="lod2")
    with pytest.raises(ValueError):
        tree.export(tmp_path, format="fbx")


def test_glb_export_every_level_and_stage(tmp_path):
    import game_export as ge

    t = cambium.grow(seed=1, years=6, stand=True, stages=(4,))
    files = t.export(tmp_path, ages=(4, 6), seasons=("summer", "winter"), look=SMALL_LOOK)
    glbs = sorted(p.name for p in files if p.suffix == ".glb")
    assert len(glbs) == 2 * 2 * 3 and "betula_pendula_age006_winter_lod2.glb" in glbs
    assert len(ge.check_files(tmp_path, log=lambda s: None)) == len(glbs)
    doc = json.loads((tmp_path / "game_manifest.json").read_text(encoding="utf-8"))
    assert [s["age"] for s in doc["stages"]] == [4, 6] and doc["mode"] == "stand"
    # the far level is drawn from the first level's file, so asking for it brings lod0 along
    far = t.export(tmp_path / "far", lod="lod2", look=SMALL_LOOK)
    assert sorted(p.name for p in far if p.suffix == ".glb") == ["betula_pendula_age006_summer_lod0.glb", "betula_pendula_age006_summer_lod2.glb"]
    with pytest.raises(ValueError, match="stages"):
        t.export(tmp_path / "x", ages=(5,), look=SMALL_LOOK)


def test_forest_uses_the_settings_tools_forest_uses():
    import forest as tool

    a = Namespace(stems=16000.0, mortality_off=False, strip=None, patch=None, area=250.0, spread=True, set=["x.y=1"])
    assert plot_settings(250, 16000, True, True, ["x.y=1"]) == tool.settings(a)
    a.mortality_off, a.spread = True, False
    assert plot_settings(250.0, 16000.0, False, False, ["x.y=1"]) == tool.settings(a)


def test_a_small_forest(tmp_path):
    f = cambium.forest(seed=1, years=3, area_m2=100, tree_list_years=(2,))
    assert f.year == 3 and f.stats[-1]["year"] == 3 and f.trees and set(f.tree_lists) == {2}
    assert {"x_m", "y_m", "height_m", "dbh_cm", "alive"} <= set(f.trees[0])
    assert [p.name for p in f.save(tmp_path)] == ["forest.json", "stats.csv", "trees.csv"]
    assert json.loads((tmp_path / "forest.json").read_text(encoding="utf-8"))["stats"] == json.loads(f.to_json())


def test_the_command(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0 and capsys.readouterr().out.strip() == f"cambium {cambium.__version__}"
    assert main(["species"]) == 0 and "betula_pendula (also: birch" in capsys.readouterr().out
    assert main(["grow", "--species", "birch", "--seed", "2", "--years", "3", "--forest", "--out", str(tmp_path), "--quiet"]) == 0
    doc = json.loads((tmp_path / "stats.json").read_text(encoding="utf-8"))
    assert doc["mode"] == "stand" and doc["seed"] == 2 and len(doc["per_year"]) == 4
    assert doc["per_year"] == json.loads(cambium.grow(seed=2, years=3, stand=True).to_json())
    assert main(["grow", "--species", "oak", "--out", str(tmp_path / "x")]) == 2
    assert main(["grow", "--years", "1", "--set", "resource.no_such=1", "--out", str(tmp_path / "y"), "--quiet"]) == 2
