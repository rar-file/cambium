"""A species is data: the schema says what it needs, every value says where it came from, its
accuracy is reported per species, and a species that isn't birch grows with no birch file in reach."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from tools import species_report
from treegen import species_schema as schema

ROOT = Path(__file__).resolve().parent.parent
BIRCH = ROOT / "species" / "betula_pendula.yaml"


def birch() -> dict:
    return yaml.safe_load(BIRCH.read_text(encoding="utf-8"))


def errors_of(raw) -> list:
    return schema.validate(raw).errors


def make_testus(raw: dict) -> dict:
    """A throwaway species: birch's file with another name, other values and other traits (no hanging
    twigs, a straight axis, spiral side shoots, a lasting taproot, no browsing, no old-age limbs)."""
    t = copy.deepcopy(raw)
    t["species"] = {"scientific_name": "Testus arbor Nobody", "common_name": "test tree"}
    changes = {
        "shoot": {"internode_length": 0.03, "max_shoot_length": 0.9},
        "resource": {"alpha": 5.5, "apical_dominance": 0.7, "apical_control_young": 0.65, "apical_control_old": 0.55,
                     "gravimorphism": 0.6, "branch_aging_years": 30, "stem_aging_years": 70, "root_share_min": 0.3},
        "bud_fate": {"long_shoot_threshold": 2.0, "short_shoot_light": 0.25, "short_shoot_survival_light": 0.15, "dormant_bud_lifespan": 5},
        "shedding": {"light_per_leaf_threshold": 0.15},
        "architecture": {"phyllotaxis_plagiotropic_deg": 137.5, "distichous_jitter_deg": 0, "branch_angle_deg": [60, 55, 50],
                         "sympodial_deviation_deg": 0},
        "tropism": {"phototropism_per_m": [0.5, 0.5, 1.0], "gravitropism_per_m": [3.0, 2.0, 1.0], "setpoint_angle_deg": [0, 60, 70]},
        "mechanics": {"wood_density": 700.0, "pendulous_radius": 0.001, "youngs_modulus_wood": 8.0e9},
        "pipe_model": {"exponent": 2.3, "tip_radius": 0.0015},
        "hydraulics": {"psi_stomata_open": -1.2, "psi_stomata_closed": -2.6, "psi_turgor_loss": -2.8, "xylem_conductivity": 3.0},
        "roots": {"trim_taproot": False, "taproot_fade_years": 40, "taproot_max_depth": 1.0, "lateral_setpoint_deg": 110},
        "reference": {"height": {"site_index_low": 14, "site_index_high": 18}, "crown": {"intercept_m": 1.5, "slope_m_per_m": 20.0}},
        "stand": {"thinning": [{"from_height_m": 0.0, "stems_per_ha": 2500}, {"from_height_m": 12.0, "stems_per_ha": 700}]},
    }

    def merge(into, new):
        for k, v in new.items():
            if isinstance(v, dict):
                merge(into[k], v)
            else:
                into[k] = v

    merge(t, changes)
    t["light"]["foliage_weight"]["spur"] = 3.0
    t["light"]["extinction_coefficient"] = 0.5
    t["leader_damage"]["enabled"] = False
    t["resource"]["reiteration"]["enabled"] = False
    return t


# -- the schema ----------------------------------------------------------------
def test_birch_passes_and_nothing_in_the_schema_is_missing_from_it():
    assert errors_of(birch()) == []
    flat = schema.flatten(birch())
    assert [f.path for f in schema.FIELDS if not f.optional and f.path not in flat] == []


def test_a_missing_value_is_an_error_and_a_missing_optional_block_only_a_warning():
    raw = birch()
    del raw["shoot"]["internode_length"]
    assert any(e.startswith("shoot.internode_length: missing") for e in errors_of(raw))
    raw = birch()
    del raw["stats"]
    assert any(e.startswith("stats.crown_base_min_leaf_share: missing") for e in errors_of(raw))
    raw = birch()
    del raw["leader_damage"]
    report = schema.validate(raw)
    assert report.errors == [] and any("no leader_damage block" in w for w in report.warnings)


@pytest.mark.parametrize("path, value, words", [
    (("shoot", "internode_length"), 2.5, "outside"),            # metres typed as centimetres
    (("light", "leaf_area_m2"), 15.0, "outside"),               # cm2 typed as m2
    (("mechanics", "youngs_modulus_wood"), 10.0, "outside"),    # GPa typed as Pa
    (("pipe_model", "growth"), "lignin", "one of"),
    (("mechanics", "enabled"), "yes", "true or false"),
    (("shoot", "internode_length"), None, "needs a value"),
    (("bud_fate", "dormant_bud_lifespan"), 2.5, "whole number"),
    (("tropism", "gravitropism_per_m"), ["a"], "list of numbers"),
])
def test_a_slip_of_unit_or_type_is_caught(path, value, words):
    raw = birch()
    raw[path[0]][path[1]] = value
    assert any(words in e for e in errors_of(raw)), errors_of(raw)


def test_values_that_must_agree_are_checked_together():
    raw = birch()
    raw["hydraulics"]["psi_stomata_open"] = -3.0
    assert any("psi_stomata_closed" in e for e in errors_of(raw))
    raw = birch()
    raw["plot"]["germination_weights"] = [0.5, 0.5, 0.5, 0.5]
    assert any("add up to 1" in e for e in errors_of(raw))
    raw = birch()
    raw["stand"]["thinning"][0]["from_height_m"] = 3.0
    assert any("start at from_height_m 0" in e for e in errors_of(raw))
    raw = birch()
    raw["stand"]["thinning"][1]["stems_per_ha"] = 5000
    assert any("must not rise" in e for e in errors_of(raw))


def test_a_new_setting_gives_a_warning_so_it_can_be_added_before_the_schema_knows_it():
    raw = birch()
    raw["bark"] = {"colour": 1.0}
    report = schema.validate(raw)
    assert report.errors == [] and any(w.startswith("bark.colour") for w in report.warnings)


def test_the_template_is_complete_and_valid_and_doesnt_count_as_a_species():
    t = yaml.safe_load((ROOT / "species" / "_template.yaml").read_text(encoding="utf-8"))
    assert errors_of(t) == []
    flat = schema.flatten(t)
    assert [f.path for f in schema.FIELDS if f.path not in flat] == []
    assert t["species"]["scientific_name"] == "Genus species Author"
    assert all(not p.name.startswith("_") for p in species_report.species_files())


# -- where each value came from ------------------------------------------------
def test_birchs_labels_are_well_formed():
    labels = schema.load_labels(ROOT / "reference" / "betula_pendula" / "labels.yaml")
    assert labels
    # a value another branch has since removed isn't a fault of the label's form
    problems = [p for p in schema.check_labels(birch(), labels) if "no such value" not in p]
    assert problems == []


def test_the_label_rules():
    raw = {"a": {"x": 1.0, "y": 2.0, "z": 3.0, "on": True, "w": 4.0}}
    labels = {"a.x": {"status": "sourced", "value": 1.0, "source": "Someone 2000", "checked": "page"},
              "a.y": {"status": "TUNED", "value": 2.0, "against": "height at 50"},
              "a.z": {"status": "sourced", "value": 9.0, "source": "Someone 2000"}}
    got = schema.read_labels(raw, "", labels)
    assert got["a.x"].status == "sourced" and got["a.x"].checked == "page"
    assert got["a.y"].status == "TUNED" and got["a.y"].note == "height at 50"
    assert got["a.z"].status == "VERIFY" and got["a.z"].changed       # changed since it was labelled
    assert got["a.w"].status == "VERIFY" and got["a.w"].note == "no label"
    assert "a.on" not in got                                          # a switch has no source to check
    assert schema.check_labels(raw, {"a.x": {"status": "sourced"}}) == ["a.x: sourced must name the source"]
    assert schema.check_labels(raw, {"a.y": {"status": "TUNED"}}) == ["a.y: TUNED must say what it was tuned against"]
    assert schema.check_labels(raw, {"a.q": {"status": "VERIFY"}}) == ["a.q: no such value in the species file"]
    assert "status must be" in schema.check_labels(raw, {"a.x": {"status": "tuned"}})[0]


def test_the_appearance_blocks_provenance_is_read_as_its_labels():
    """The look values carry their labels in appearance.provenance (SOURCE, DERIVED, TUNED); the counts read them
    there, the longest name that covers a value first (final check (a), finding 5)."""
    raw = {"appearance": {"provenance": {"a": "SOURCE: x", "a.b": "DERIVED: y", "c": "TUNED: z"},
                          "a": {"b": 1.0, "d": 2.0}, "c": {"e": [1, 2]}, "f": 3.0}}
    got = schema.read_labels(raw, "", {})
    assert got["appearance.a.b"].status == "DERIVED" and got["appearance.a.b"].note == "DERIVED: y"
    assert got["appearance.a.d"].status == "sourced"
    assert got["appearance.c.e"].status == "TUNED"
    assert got["appearance.f"].status == "VERIFY" and got["appearance.f"].note == "no label"
    assert "appearance.provenance.a" not in got                       # a label's text isn't a value
    assert schema.check_labels({"a": {"x": 1.0}}, {"a.x": {"status": "DERIVED"}}) == ["a.x: DERIVED must name the source"]
    # birch: every look value is labelled by its provenance
    look = {p: lab for p, lab in schema.read_labels(birch(), "", {}).items() if p.startswith("appearance.")}
    assert look and all(lab.note != "no label" for lab in look.values())


def test_a_tuned_comment_in_the_species_file_is_read_and_comes_first():
    text = textwrap.dedent("""\
        shoot:
          # the rule of the reset: TUNED against height at 5
          length: 0.1
          # tuned by eye long ago, in small letters: not a label
          other: 0.2
          inline: 0.3  # TUNED against crown width
        next:

          after_a_gap: 0.4
        """)
    raw = yaml.safe_load(text)
    got = schema.read_labels(raw, text, {"shoot.length": {"status": "sourced", "value": 0.1, "source": "x"}})
    assert got["shoot.length"].status == "TUNED" and "height at 5" in got["shoot.length"].note
    assert got["shoot.inline"].status == "TUNED"
    assert got["shoot.other"].status == "VERIFY"
    assert got["next.after_a_gap"].status == "VERIFY"


# -- the report ----------------------------------------------------------------
def _saved_runs(folder: Path, heights: list) -> Path:
    for seed, h in enumerate(heights):
        d = folder / f"{seed}_stand"
        d.mkdir(parents=True)
        per_year = [{"year": a, "height_m": h * a / 10.0, "dbh_cm": 5.0, "lai": 2.0} for a in (10, 50, 60)]
        (d / "stats.json").write_text(json.dumps({"mode": "stand", "per_year": per_year}))
    return folder


TARGETS = {
    "growth": {
        "height": {"metric": "height_m", "target_range": [5.0, 8.0], "source": "A paper", "conditions": {"scenario": ["stand-tree"]}},
        "leaves": {"metric": "lai", "target_range": [3.0, 4.0], "source": "B paper", "conditions": {"scenario": ["stand-tree"]}},
        "note": {"metric": "dbh_cm", "target_range": [1.0, 2.0], "source": "C paper", "scoring": "info", "conditions": {"scenario": ["stand-tree"]}},
        "open_only": {"metric": "height_m", "target_range": [1.0, 2.0], "source": "D paper", "conditions": {"scenario": ["single-tree"]}},
    }
}


def test_a_new_species_carries_its_own_targets_and_they_are_scored(tmp_path, capsys):
    raw = make_testus(birch())
    sp = tmp_path / "testus_arbor.yaml"
    sp.write_text(yaml.safe_dump(raw, sort_keys=False))
    ref = tmp_path / "ref"
    ref.mkdir()
    (ref / "targets.yaml").write_text(yaml.safe_dump(TARGETS))
    (ref / "labels.yaml").write_text(yaml.safe_dump({"shoot.internode_length": {"status": "TUNED", "value": 0.03, "against": "height at 10"}}))
    runs = _saved_runs(tmp_path / "runs", [6.0, 7.0, 7.5])
    assert species_report.main(["--species", str(sp), "--reference", str(ref), "--ensemble", str(runs), "--age", "10"]) == 0
    out = capsys.readouterr().out
    line = next(ln for ln in out.splitlines() if ln.startswith("ACCURACY"))
    assert "testus_arbor: 1 of 2 scored targets inside their band at ages 10, over 3 runs (targets not approved)" in line
    assert "1 tuned" in line
    assert "`growth.height`" in out and "6.83" in out and "`growth.note`" in out
    assert "growth.open_only" in out.split("Not scored")[1]     # another scenario: not scored, not filled in


def test_the_report_scores_ages_50_and_60_by_default_and_a_target_must_pass_at_both(tmp_path, capsys):
    runs = _saved_runs(tmp_path / "runs", [1.0, 1.0])       # 5 m at 50, 6 m at 60
    ref = tmp_path / "ref"
    ref.mkdir()
    (ref / "targets.yaml").write_text(yaml.safe_dump({"g": {"h": {"metric": "height_m", "target_range": [5.5, 8.0], "source": "A", "conditions": {"scenario": ["stand-tree"]}}}}))
    species_report.main(["--species", "betula_pendula", "--reference", str(ref), "--ensemble", str(runs)])
    out = capsys.readouterr().out
    assert "| At 50 | At 60 |" in out and "FAIL, inside" in out
    assert "PASS" not in next(ln for ln in out.splitlines() if ln.startswith("| `g.h`"))
    assert "0 of 1 scored targets inside their band at ages 50 and 60" in out and "1 of 2 age checks inside the band" in out


def test_a_target_scored_on_two_ensembles_counts_for_each(tmp_path):
    good = _saved_runs(tmp_path / "good", [6.0, 7.0])
    bad = _saved_runs(tmp_path / "bad", [20.0, 20.0])
    rows, n = species_report.score_targets(TARGETS, [good, bad], [10])
    assert n == 4
    verdicts = species_report.target_verdicts(rows)
    assert verdicts["growth.height [good]"] == ["PASS"] and verdicts["growth.height [bad]"] == ["FAIL"]
    # a target neither can score is listed once, without a name
    assert [r["target"] for r in rows].count("growth.open_only (age 10)") == 1


def test_birchs_targets_are_read_through_the_approved_tag():
    targets, where, approved = species_report.load_targets(ROOT / "reference" / "betula_pendula", "betula_pendula")
    assert approved and where == "reference/targets.yaml at targets-approved"
    assert "site_index_curves" in targets["tree_allometry"]


def test_new_labels_start_as_unchecked_and_wont_overwrite(tmp_path):
    sp = tmp_path / "x.yaml"
    sp.write_text(yaml.safe_dump(birch()))
    f = species_report.init_labels(sp, tmp_path / "ref")
    got = yaml.safe_load(f.read_text())
    assert got["resource.alpha"] == {"status": "VERIFY", "value": birch()["resource"]["alpha"]}
    assert "mechanics.enabled" not in got
    with pytest.raises(SystemExit):
        species_report.init_labels(sp, tmp_path / "ref")


# -- a species that isn't birch ------------------------------------------------
NO_BIRCH = """
import builtins, sys
real = builtins.open
def guarded(file, *a, **k):
    if "betula_pendula" in str(file):
        raise RuntimeError(f"read a birch file: {file}")
    return real(file, *a, **k)
builtins.open = guarded
import cli
sys.exit(cli.main(sys.argv[1:]))
"""


@pytest.mark.parametrize("stand", [True, False])
def test_a_species_that_isnt_birch_grows_ten_years_with_no_birch_file_in_reach(tmp_path, stand):
    raw = make_testus(birch())
    assert errors_of(raw) == []
    sp = tmp_path / "testus_arbor.yaml"
    sp.write_text(yaml.safe_dump(raw, sort_keys=False))
    args = ["--species", str(sp), "--seed", "1", "--years", "10", "--no-preview", "--quiet", "--out", str(tmp_path / "out")]
    if stand:
        args.append("--stand")
    proc = subprocess.run([sys.executable, "-c", NO_BIRCH, *args], cwd=str(ROOT), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]
    out = tmp_path / "out" / ("1_stand" if stand else "1")
    stats = json.loads((out / "stats.json").read_text())
    assert stats["species"] == "Testus arbor Nobody"
    last = stats["per_year"][-1]
    assert last["year"] == 10 and last["height_m"] > 1.0 and last["leaves"] > 100
    assert stats["reference"]["site_index_h50_bh_m"] == [14, 18]
    assert (out / "tree.glb").stat().st_size > 1000
