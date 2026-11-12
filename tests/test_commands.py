"""Strict names and commands: a misspelt setting or a slip in an argument stops a run before anything
grows, with one plain line and exit code 2.  None of these tests grows a tree."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import cli  # noqa: E402
from cambium.cli import main as cambium_main  # noqa: E402
from treegen import names  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.params import SettingError, check_names, load_environment, load_species, setting_names  # noqa: E402

BIRCH = ROOT / "species" / "betula_pendula.yaml"
SITE = ROOT / "environments" / "sweden_open_field.yaml"


@pytest.fixture
def no_growth(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("a tree started to grow")
    monkeypatch.setattr(GrowthModel, "__init__", refuse)


def _known(names_list):
    return names_list | {k.rsplit(".", i)[0] for k in names_list for i in range(1, k.count(".") + 1)}


def test_every_name_in_the_shipped_files_is_known():
    """Every species file, the template a new species is copied from included, and every site file."""
    files = [(p, names.SPECIES) for p in sorted((ROOT / "species").glob("*.yaml"))] +             [(p, names.ENVIRONMENT) for p in sorted((ROOT / "environments").glob("*.yaml"))]
    assert ROOT / "species" / "_template.yaml" in [p for p, _ in files]
    for path, known in files:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        check_names(raw, known, path.name)                      # rows, dots and blocks as well as names
        assert setting_names(raw) <= _known(known), path.name
    load_species(ROOT / "species" / "_template.yaml")


def _birch_with(tmp_path, change):
    raw = yaml.safe_load(BIRCH.read_text(encoding="utf-8"))
    change(raw)
    (tmp_path / "sp.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    return tmp_path / "sp.yaml"


@pytest.mark.parametrize("change, says", [
    (lambda r: r.__setitem__("resource.alpha", 9.9), "'resource.alpha' has a dot in its name"),
    (lambda r: r["resource"].__setitem__("x.alpah", 9.9), "'resource.x.alpah' has a dot in its name"),
    (lambda r: r.__setitem__("speed", True), "speed is a block of settings, not one value"),
    (lambda r: r["resource"].__setitem__("alpha", {"value": 4.8}), "resource.alpha is one value, not a block"),
    (lambda r: r["stand"].__setitem__("thinning", 3000), "stand.thinning is a list of records"),
    (lambda r: r["stand"]["thinning"][0].__setitem__("stem_per_ha", 1), "unknown name 'stem_per_ha' in a row of stand.thinning; nearest: stems_per_ha"),
    (lambda r: r["stand"]["thinning"][0].pop("stems_per_ha"), "a row of stand.thinning must hold stems_per_ha"),
    (lambda r: r["appearance"]["game"]["lods"][0].__setitem__("budgt", 1), "unknown name 'budgt' in a row of appearance.game.lods; nearest: budget"),
    (lambda r: r["appearance"]["bark"]["stages"][0]["lenticels"].__setitem__("colur", 1), "'lenticels.colur' in a row of appearance.bark.stages"),
])
def test_a_species_file_that_cant_mean_what_it_says_is_refused(tmp_path, change, says):
    with pytest.raises(SettingError, match=re.escape(says)):
        load_species(_birch_with(tmp_path, change))


def test_dotted_names_are_kept_for_the_provenance_map_alone(tmp_path):
    assert names.FREE_MAPS == {"appearance.provenance"}
    raw = yaml.safe_load(BIRCH.read_text(encoding="utf-8"))
    assert any("." in k for k in raw["appearance"]["provenance"])        # birch's file loads with them
    sp, _ = load_species(_birch_with(tmp_path, lambda r: r["appearance"]["provenance"].__setitem__("new.value", "TUNED: x")))
    assert sp.resource.alpha == raw["resource"]["alpha"]


def test_a_misspelt_name_in_a_species_or_site_file_is_refused_with_the_nearest(tmp_path):
    raw = yaml.safe_load(BIRCH.read_text(encoding="utf-8"))
    raw["speed"]["light_row"] = raw["speed"].pop("light_rows")
    (tmp_path / "sp.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    with pytest.raises(SettingError, match="unknown setting 'speed.light_row'; nearest: speed.light_rows"):
        load_species(tmp_path / "sp.yaml")
    env = yaml.safe_load(SITE.read_text(encoding="utf-8"))
    env["soil"]["depth_mm"] = env["soil"].pop("depth_m")
    (tmp_path / "site.yaml").write_text(yaml.safe_dump(env), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown setting 'soil.depth_mm'; nearest: soil.depth_m"):
        load_environment(tmp_path / "site.yaml")


def test_a_value_whose_default_lives_in_code_is_filled_in_and_can_be_set():
    sp, raw = load_species("betula_pendula")
    for key, value in names.DEFAULTS.items():
        assert key not in setting_names(raw)          # birch leaves them out: the code's value is used
        holder = sp
        for part in key.split("."):
            holder = getattr(holder, part)
        assert holder == value
    cli.checkpoint.set_values(sp, ["shoot.max_tree_height=30"])
    assert sp.shoot.max_tree_height == 30


@pytest.mark.parametrize("args, says", [
    (["grow", "--years", "0"], "--years must be a whole number from 1"),
    (["grow", "--seed", "-1"], "--seed must be a whole number from 0"),
    (["grow", "--set", "resource.alpah=4.5"], "nearest: resource.alpha"),
    (["grow", "--set", "resource.alpha=abc"], "isn't JSON"),
    (["grow", "--export", "glb", "--lod", "lod9"], "unknown level"),
    (["grow", "--export", "glb", "--seasons", "fall"], "--seasons must be some of"),
    (["forest", "--area", "0"], "--area must be a number above 0"),
    (["forest", "--stems", "-1"], "--stems must be a number above 0"),
    (["forest", "--years", "20", "--tree-lists", "10,30"], "--tree-lists must be whole numbers from 1 to 20"),
    (["export", "--ages", "15,30"], "give --out"),
    (["export", "--ages", "15,30", "--format", "usd", "--out", "{tmp}"], "--format usd writes one age"),
    (["grow", "--environment", "mars"], "unknown environment"),
])
def test_the_cambium_command_refuses_a_slip_before_anything_grows(args, says, tmp_path, capsys, no_growth):
    args = [a.replace("{tmp}", str(tmp_path / "e")) for a in args]
    assert cambium_main(args + ["--quiet"] + ([] if "--out" in args or args[0] == "export" else ["--out", str(tmp_path / "o")])) == 2
    err = capsys.readouterr().err
    assert says in err and err.count("\n") == 1


def test_an_output_folder_that_cant_be_written_is_refused_before_anything_grows(tmp_path, capsys, no_growth):
    (tmp_path / "a_file").write_text("x")
    assert cambium_main(["grow", "--out", str(tmp_path / "a_file"), "--quiet"]) == 2
    assert "is a file" in capsys.readouterr().err


@pytest.mark.parametrize("main, args, says", [
    (cli.main, ["--years", "0"], "--years must be"),
    (cli.main, ["--set", "nosuch.alpha=1"], "no such parameter: nosuch.alpha"),
    (cli.main, ["--save-at", "70", "--years", "60"], "--save-at must be whole numbers from 1 to 60"),
    ("plot", ["--trees", "0"], "--trees must be"),
    ("plot", ["--set", "stand.thinnning=[]"], "nearest: stand.thinning"),
    ("sweep", ["nudge", "--param", "resource.alpah"], "nearest: resource.alpha"),
    ("sweep", ["seeds", "--modes", "open,forest"], "--modes must be"),
])
def test_the_research_commands_refuse_a_slip_before_anything_grows(main, args, says, tmp_path, capsys, no_growth):
    if isinstance(main, str):
        main = __import__(main).main
    out = ["--out", str(tmp_path / ("s.json" if main.__module__ == "sweep" else "o"))]
    with pytest.raises(SystemExit) as e:
        main(args + out)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert says in err and err.count("\n") == 1


@pytest.mark.parametrize("main, args, says", [
    (cambium_main, ["grow", "--seed", "abc"], "cambium grow: argument --seed: invalid int value: 'abc'"),
    (cambium_main, ["grow", "--export", "fbx"], "cambium grow: argument --export: invalid choice: 'fbx'"),
    (cambium_main, ["forest", "--area", "big"], "cambium forest: argument --area: invalid float value: 'big'"),
    (cambium_main, ["plant"], "invalid choice: 'plant'"),
    (cli.main, ["--seed", "abc"], "argument --seed: invalid int value: 'abc'"),
])
def test_a_slip_argparse_finds_is_one_plain_line_too(main, args, says, capsys, no_growth):
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert says in err and err.count("\n") == 1 and "usage:" not in err


def _no_runs(monkeypatch, module, *names_):
    def refuse(*a, **k):
        raise AssertionError("a run started")
    for name in names_:
        monkeypatch.setattr(module, name, refuse)


@pytest.mark.parametrize("argv, says", [
    (["trees", "--label", "x", "--years", "0"], "--years must be a whole number from 1"),
    (["trees", "--label", "x", "--first-seed", "-1"], "--first-seed must be a whole number from 0"),
    (["trees", "--label", "x", "--set", "resource.alpah=1"], "nearest: resource.alpha"),
    (["trees", "--label", "x", "--species", "quercus_nosuch"], "no parameter file for 'quercus_nosuch'"),
    (["plots", "--label", "x", "--mode", "wild"], "--mode must be natural or managed"),
    (["plots", "--label", "x", "--trees", "0"], "--trees must be a whole number of at least 1"),
    (["median", "--label", "no_such_ensemble_label"], "no ensemble 'no_such_ensemble_label'"),
    (["trees", "--label", "x", "--seeds", "abc"], "argument --seeds: invalid int value"),
])
def test_the_ensemble_tool_refuses_a_slip_before_any_seed_runs(argv, says, monkeypatch, capsys, no_growth):
    import ensemble
    _no_runs(monkeypatch, ensemble, "run_trees", "run_plots")
    monkeypatch.setattr(sys, "argv", ["ensemble.py", *argv])
    with pytest.raises(SystemExit) as e:
        ensemble.main()
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert says in err and err.count("\n") == 1


@pytest.mark.parametrize("argv, says", [
    (["--seed", "-1"], "--seed must be a whole number from 0"),
    (["--ages", "0"], "--ages must be whole numbers from 1"),
    (["--seasons", "fall"], "--seasons must be some of"),
    (["--budget", "lod9=5"], "unknown level 'lod9'"),
    (["--budget", "lod1=lots"], "--budget 'lod1=lots': give LEVEL=TRIANGLES"),
    (["--levels", "lod7"], "unknown level 'lod7'"),
    (["--look", "bark.nosuch=1"], "--look bark.nosuch: no such look value"),
    (["--timelapse", "--look", "leaves.each_year=1"], "--timelapse sets leaves.each_year itself"),
    (["--set", "resource.alpah=1"], "nearest: resource.alpha"),
    (["--sets", "{tmp}/missing.txt"], "--sets"),
    (["--target", "fbx"], "argument --target: invalid choice"),
])
def test_the_game_export_tool_refuses_a_slip_before_anything_grows(argv, says, tmp_path, monkeypatch, capsys, no_growth):
    import game_export
    _no_runs(monkeypatch, game_export, "main_export")
    argv = [x.replace("{tmp}", str(tmp_path)) for x in argv]
    monkeypatch.setattr(sys, "argv", ["game_export.py", "export", "--out", str(tmp_path / "out"), *argv])
    with pytest.raises(SystemExit) as e:
        game_export.main()
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert says in err and err.count("\n") == 1
    assert not (tmp_path / "out").exists()
