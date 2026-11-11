"""The strict scorecard (DECISIONS 110, items 4, 5, 6a and 12): only an independent row that meets the
seven-part pass rule may print PASS; a by-design, tuned, seen or out-of-sample row never does; FAIL reads
FAIL in every block; the independent count never takes a row tied to a figure that isn't independent.

These tests read the working copy of reference/targets.yaml, as tests/test_scorecard_targets.py does, and
need no git: the facts about the runs (pass rule part 5) and the tag check (part 6) are given to the
functions directly."""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from tools.scorecard import (IN_BAND_WORDS, KINDS, PASS_BASES, ensemble_facts, evaluate_ensemble, evaluate_targets,
                             flatten_targets, independent_header, print_ensemble, print_scorecard)

ROOT = Path(__file__).resolve().parent.parent
NAME = "stand_canopy.lai_hagemeier"           # band 3.6-5.4, scored on stand trees by the LAI evaluator
CLEAN = {"runs": 20, "commit": "abc1234", "problems": []}


def _targets():
    with open(ROOT / "reference" / "targets.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tree_run(lai, year=50, manifest=None):
    stats = {"mode": "stand", "per_year": [{"year": year, "lai": lai}], "run_manifest": manifest or {}}
    return {"path": "mock_tree", "is_plot": False, "is_tree": True, "is_seedling": False, "plot_data": None,
            "tree_stats": stats, "seedling_data": None, "trees_py": {}}


def _untie(t, name, keep=()):
    """Take a target out of every other target's tied_to (but those in keep): ties are two-way, so a row named by
    another isn't clean."""
    for other, item in flatten_targets(t):
        if other != name and other not in keep and name in (item.get("tied_to") or []):
            item["tied_to"] = [x for x in item["tied_to"] if x != name]
    return t


def _as(targets, kind, **extra):
    """The LAI target made into a target of this kind that meets every other part of the pass rule (ties are
    two-way, so no other row may name it either)."""
    t = _untie(copy.deepcopy(targets), NAME)
    item = t["stand_canopy"]["lai_hagemeier"]
    item.update(kind=kind, values_set=[], tied_to=[], source_opened="read at the publisher, 2026-11-11", matched=True,
                band_basis=PASS_BASES[0], stands=3)
    item.pop("scoring", None)
    item.update(extra)
    if kind is None:
        item.pop("kind")
    return t


def _row(rows, age=50):
    return next(r for r in rows if r["target"] == f"{NAME} (age {age})")


def _ensemble(targets, lai, facts=CLEAN, frozen=True, n=20):
    return evaluate_ensemble(targets, [_tree_run(lai) for _ in range(n)], [50], facts=facts, frozen=frozen)


def test_only_an_independent_row_can_print_pass():
    base = _targets()
    rows = _ensemble(_as(base, "independent"), 4.0)
    assert _row(rows)["reads"] == "PASS"                       # all seven parts hold: the rule is not vacuous
    for kind in [k for k in KINDS if k != "independent"] + [None]:
        t = _as(base, kind)
        rows = _ensemble(t, 4.0)
        r = _row(rows)
        assert r["status"] == "PASS"                            # the band check alone is unchanged
        assert r["reads"] == IN_BAND_WORDS[kind], kind
        assert "PASS" not in r["reads"]
        out = print_ensemble(rows, "header", t)
        assert "**PASS**" not in out
        assert f"**{IN_BAND_WORDS[kind]}**" in out


def test_fail_reads_fail_in_every_block():
    base = _targets()
    for kind in list(KINDS) + [None]:
        t = _as(base, kind)
        rows = _ensemble(t, 6.0)
        assert _row(rows)["status"] == "FAIL"
        assert _row(rows)["reads"] == "FAIL", kind
        assert "**FAIL**" in print_ensemble(rows, "header", t)


@pytest.mark.parametrize("change, part", [
    ({"source_opened": False}, "2 ("),
    ({"matched": False}, "3 ("),
    ({"band_basis": "one or two stands"}, "4 ("),
    ({"scoring": "info"}, None),
    ({"values_set": ["pipe_model.stem_theory.wind_speed_m_s"]}, "1 ("),
])
def test_each_part_of_the_pass_rule_is_needed(change, part):
    rows = _ensemble(_as(_targets(), "independent", **change), 4.0)
    reads = _row(rows)["reads"]
    assert reads != "PASS"
    if part is None:
        assert reads == "INFO"
    else:
        assert reads.startswith("IN BAND, not a pass: rule ")
        assert reads.startswith(f"IN BAND, not a pass: rule {part}") or f", {part}" in reads


def test_runs_and_tag_are_needed():
    t = _as(_targets(), "independent")
    assert _row(_ensemble(t, 4.0, frozen=False))["reads"] != "PASS"                       # part 6
    assert _row(_ensemble(t, 4.0, facts={"runs": 20, "commit": None, "problems": ["runs not at one recorded commit"]}))["reads"] != "PASS"
    # one run is never a verdict, whatever the kind
    results, _ = evaluate_targets(t, [_tree_run(4.0)], ages=[50])
    r = next(x for x in results if x["target"] == f"{NAME} (age 50)")
    assert r["status"] == "PASS" and r["reads"] != "PASS"
    assert "**PASS**" not in print_scorecard(results, [], "header", t)


def test_ensemble_facts():
    man = {"git_commit": "abc1234", "overrides": ["plot.stand_measures=true", "mortality.enabled=true"]}
    runs = [_tree_run(4.0, manifest=man) for _ in range(20)]
    assert ensemble_facts(runs, check_git=False)["problems"] == []
    assert ensemble_facts(runs[:19], check_git=False)["problems"] == ["19 runs, not 20"]
    other = dict(man, overrides=man["overrides"] + ["crown_frame.chase=0.5"])
    assert any("defaults changed" in p for p in ensemble_facts(runs[:19] + [_tree_run(4.0, manifest=other)], check_git=False)["problems"])
    two = runs[:19] + [_tree_run(4.0, manifest=dict(man, git_commit="def5678"))]
    assert "runs not at one recorded commit" in ensemble_facts(two, check_git=False)["problems"]


def test_a_tied_row_is_never_counted():
    base = _targets()
    tuned = "stand_canopy.lai_baltic_chronosequence"
    assert dict(flatten_targets(base))[tuned]["kind"] == "tuned against"
    clean = _as(base, "independent")
    rows = _ensemble(clean, 4.0)
    assert "Independent passes: 1 of 1 at 50" in independent_header(rows, clean, ages=(50,))
    tied = _as(base, "independent", tied_to=[tuned])
    rows = _ensemble(tied, 4.0)
    assert _row(rows)["reads"] != "PASS" and "tied to " + tuned in _row(rows)["reads"]
    assert "Independent rows that apply: age 50: 0" in independent_header(rows, tied, ages=(50,))
    # a failing tied row isn't counted either
    rows = _ensemble(tied, 6.0)
    assert "Independent passes: 0 of 0 at 50" in independent_header(rows, tied, ages=(50,))


def test_a_row_needs_a_value_in_20_runs_of_its_own():
    """Part 5 is the row's, not the folder's: 20 runs of which only 2 give the row a value is not a pass, and the
    header doesn't count it (independent check of V1, 2026-11-11)."""
    t = _as(_targets(), "independent")
    runs = [_tree_run(4.0) for _ in range(2)] + [_tree_run(None) for _ in range(18)]
    assert len(runs) == 20
    rows = evaluate_ensemble(t, runs, [50], facts=CLEAN, frozen=True)
    r = _row(rows)
    assert r["seeds"] == 2 and r["status"] == "PASS"
    assert r["reads"] != "PASS" and "5 (a value in 2 of 20 runs, not 20)" in r["reads"]
    header = independent_header(rows, t, ages=(50,))
    assert "Independent rows that apply: age 50: 0" in header and "Independent passes: 0 of 0 at 50" in header
    assert "**PASS**" not in print_ensemble(rows, "header", t)
    # the same row with a value in all 20 runs still passes and counts: the rule is not vacuous
    rows = evaluate_ensemble(t, [_tree_run(4.0) for _ in range(20)], [50], facts=CLEAN, frozen=True)
    assert _row(rows)["reads"] == "PASS" and "Independent passes: 1 of 1 at 50" in independent_header(rows, t, ages=(50,))


def test_ties_are_followed_through_independent_rows():
    """A row tied to an independent row that is itself tied to a tuned one is not clean (independent check of V1)."""
    middle, tuned = "stand_canopy.subcanopy_light_transmittance", "stand_canopy.lai_baltic_chronosequence"
    t = _as(_targets(), "independent", tied_to=[middle])
    t["stand_canopy"]["subcanopy_light_transmittance"].update(kind="independent", values_set=[], tied_to=[tuned])
    rows = _ensemble(t, 4.0)
    assert _row(rows)["reads"] != "PASS" and f"tied to {middle} -> {tuned} (tuned against)" in _row(rows)["reads"]
    assert "Independent rows that apply: age 50: 0" in independent_header(rows, t, ages=(50,))
    # a tied independent row with a value set against it is not clean either
    t["stand_canopy"]["subcanopy_light_transmittance"].update(tied_to=[], values_set=["light.extinction_coefficient"])
    assert _row(_ensemble(t, 4.0))["reads"] != "PASS"
    # tied to a clean independent row only: still a pass (no other row names the middle one either: ties are two-way)
    t["stand_canopy"]["subcanopy_light_transmittance"].update(values_set=[])
    _untie(t, middle, keep=(NAME,))
    assert t["stand_canopy"]["lai_hagemeier"]["tied_to"] == [middle]
    assert _row(_ensemble(t, 4.0))["reads"] == "PASS"


def test_a_changed_start_or_mortality_off_is_not_run_setup():
    man = {"git_commit": "abc1234", "overrides": ["plot.stand_measures=true", "plot.natural_start.enabled=true",
                                                  "plot.natural_start.stems_per_ha=16000.0", "plot.natural_start.area_m2=1000.0",
                                                  "mortality.enabled=true"]}
    assert ensemble_facts([_tree_run(4.0, manifest=man) for _ in range(20)], check_git=False)["problems"] == []
    for bad in ("plot.natural_start.stems_per_ha=4000.0", "mortality.enabled=false"):
        other = dict(man, overrides=[o for o in man["overrides"] if o.split("=")[0] != bad.split("=")[0]] + [bad])
        problems = ensemble_facts([_tree_run(4.0, manifest=other) for _ in range(20)], check_git=False)["problems"]
        assert any("defaults changed" in p and bad in p for p in problems), bad


def test_the_independent_table_takes_the_wood_kinds_from_the_targets():
    from tools.scorecard import wood_kinds_from_targets
    rows = [{"what": "stem wood over Repola's at its own DBH and height (ratio)", "kind": "independent", "note": "x"},
            {"what": "branch wood over Repola's living branches (ratio)", "kind": "independent", "note": "x"},
            {"what": "spread of DBH: SD over mean", "kind": "independent", "note": "x"}]
    out = wood_kinds_from_targets(rows, _targets())
    assert [r["kind"] for r in out] == ["seen", "tuned against", "independent"]
    out = wood_kinds_from_targets(rows, {})          # a targets file with no kinds: the working copy gives them
    assert [r["kind"] for r in out][:2] == ["seen", "tuned against"]


def test_the_rows_once_called_independent_are_not_counted():
    """Foliage and the young-crown rows were the yardstick for values (independent check of V1): never counted.
    The seedlings' root:shoot ratio follows resource.root_share_min/max (treegen/growth.py:921), so it is by design
    until a seedling test shows otherwise (third check of V1)."""
    flat = dict(flatten_targets(_targets()))
    for name in ("tree_allometry.foliage_biomass", "stand_canopy.live_crown_ratio.dense_unmanaged_stand",
                 "stand_canopy.clear_stem_at_first_thinning", "juvenile_establishment.seedling_root_shoot_ratio"):
        assert flat[name]["kind"] != "independent", name
        assert flat[name]["values_set"], name
    rs = flat["juvenile_establishment.seedling_root_shoot_ratio"]
    assert rs["kind"] == "by design"
    assert set(rs["values_set"]) == {"resource.root_share_min", "resource.root_share_max"}
    assert "treegen/growth.py:921" in rs["kind_reason"]


def test_every_target_has_a_kind_and_a_reason():
    for name, item in flatten_targets(_targets()):
        assert item.get("kind") in KINDS, name
        assert item.get("kind_reason"), name
        for t in item.get("tied_to") or []:
            assert t in dict(flatten_targets(_targets())), (name, t)


def test_q40_rows_are_info_and_the_stand_trees_miss_is_printed():
    """5-7 m at top height 13-15 m: INFO until a measured source is opened; a stand tree at 0.89 m reads as a miss."""
    targets = _targets()
    flat = dict(flatten_targets(targets))
    assert flat["stand_canopy.clear_stem_at_first_thinning"]["scoring"] == "info"
    assert flat["stand_canopy.clear_stem_natural_plots"]["kind"] == "tuned against"
    py = [{"year": 24, "height_m": 12.9, "lowest_live_branch_m": 0.3},
          {"year": 25, "height_m": 13.46, "lowest_live_branch_m": 0.89},
          {"year": 26, "height_m": 13.97, "lowest_live_branch_m": 3.0}]
    run = {"path": "t", "is_plot": False, "is_tree": True, "is_seedling": False, "plot_data": None,
           "tree_stats": {"mode": "stand", "per_year": py}, "seedling_data": None, "trees_py": {}}
    rows = evaluate_ensemble(targets, [run] * 20, [50], facts=CLEAN, frozen=True)
    r = next(x for x in rows if x["target"] == "stand_canopy.clear_stem_at_first_thinning (top height 13-15 m)")
    assert r["mean"] == pytest.approx(0.89)
    assert r["status"] == "INFO" and r["reads"] == "INFO; outside the band (a miss)"


def test_plot_rows_are_read_from_the_tree_lists():
    """A plot with no per-tree stats is scored from its own tree list (review 2026-11-09, finding 9)."""
    trees = [{"alive": True, "dbh_cm": 20.0 + k, "height_m": 20.0, "crown_base_m": 10.0, "lowest_live_branch_m": 10.0}
             for k in range(8)]
    plot = {"area_m2": 1000.0, "mode": "natural", "stats": [{"year": 50, "stems_per_ha": 80, "lai": 4.0}]}
    run = {"path": "p", "is_plot": True, "is_tree": False, "is_seedling": False, "plot_data": plot, "tree_stats": None,
           "seedling_data": None, "trees_py": {}, "tree_lists": {50: {"area_m2": 1000.0, "trees": trees}}}
    results, _ = evaluate_targets(_targets(), [run], ages=[50])
    r = next(x for x in results if x["target"] == "stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)")
    assert r["value"] == pytest.approx(0.5)
    assert "tree list" in r["notes"]
    h = next(x for x in results if x["target"] == "tree_allometry.site_index_curves (age 50)")
    assert h["value"] == pytest.approx(20.0, abs=1e-6) and h["reads"] != "PASS"


def test_a_tie_written_only_on_the_other_row_counts():
    """Ties are two-way (third check of V1): an independent row with no ties of its own, named in a tuned row's
    tied_to, is not clean; it never reads PASS and is never counted."""
    tuned = "stand_canopy.lai_baltic_chronosequence"
    t = _as(_targets(), "independent")
    assert _row(_ensemble(t, 4.0))["reads"] == "PASS"                       # clean, as a control
    t["stand_canopy"]["lai_baltic_chronosequence"]["tied_to"].append(NAME)    # the tie on the tuned row only
    assert t["stand_canopy"]["lai_hagemeier"]["tied_to"] == []
    rows = _ensemble(t, 4.0)
    r = _row(rows)
    assert r["status"] == "PASS" and r["reads"] != "PASS"
    assert f"tied to {tuned} (tuned against)" in r["reads"]
    header = independent_header(rows, t, ages=(50,))
    assert "Independent rows that apply: age 50: 0" in header and "Independent passes: 0 of 0 at 50" in header
    assert "**PASS**" not in print_ensemble(rows, "header", t)
    # through a middle row: tied to a clean-looking independent row that a tuned row names on its own side only
    middle = "stand_canopy.subcanopy_light_transmittance"
    t = _untie(_as(_targets(), "independent", tied_to=[middle]), middle, keep=(NAME,))
    t["stand_canopy"]["subcanopy_light_transmittance"].update(kind="independent", values_set=[], tied_to=[])
    assert t["stand_canopy"]["lai_hagemeier"]["tied_to"] == [middle]
    assert _row(_ensemble(t, 4.0))["reads"] == "PASS"                       # control
    t["stand_canopy"]["lai_baltic_chronosequence"]["tied_to"].append(middle)
    reads = _row(_ensemble(t, 4.0))["reads"]
    assert reads != "PASS" and f"tied to {middle} -> {tuned} (tuned against)" in reads


def test_a_failing_row_never_leaves_the_header():
    """A failing independent row with a value in 19 of 20 runs is still counted (0 passes): too few runs only keeps
    a row from passing (third check of V1)."""
    t = _as(_targets(), "independent")
    rows = evaluate_ensemble(t, [_tree_run(6.0) for _ in range(19)] + [_tree_run(None)], [50], facts=CLEAN, frozen=True)
    r = _row(rows)
    assert r["seeds"] == 19 and r["reads"] == "FAIL"
    header = independent_header(rows, t, ages=(50,))
    assert "Independent rows that apply: age 50: 1" in header and "Independent passes: 0 of 1 at 50" in header
    # an in-band row with 19 runs is left out, and the list says what it reads
    rows = evaluate_ensemble(t, [_tree_run(4.0) for _ in range(19)] + [_tree_run(None)], [50], facts=CLEAN, frozen=True)
    header = independent_header(rows, t, ages=(50,))
    assert "Independent passes: 0 of 0 at 50" in header
    assert f"{NAME} (age 50), a value in 19 runs, reads IN BAND, not a pass" in header


@pytest.mark.parametrize("tie", [
    "stand_canopy.lai_hagemeier",                     # a plain string, not a list
    ["stand_canopy.lai_hagemeier "],                  # a trailing space
    ["lai_hagemeier"],                                # the short name
    ["STAND_CANOPY.LAI_HAGEMEIER"],                   # upper case
    ["stand_canopy.lai_hagemeir"],                    # misspelt
])
def test_a_mistyped_tie_fails_safe(tie):
    """A tie that can't be read can't be followed (fourth check of V1): with the tie on the tuned row written as a
    plain string or with the name misspelt, the independent row never reads PASS and is never counted, and the
    reason names the row and the text."""
    tuned = "stand_canopy.lai_baltic_chronosequence"
    t = _as(_targets(), "independent")
    rows = _ensemble(t, 4.0)
    assert _row(rows)["reads"] == "PASS"                                     # clean, as a control
    assert "Independent passes: 1 of 1 at 50" in independent_header(rows, t, ages=(50,))
    t["stand_canopy"]["lai_baltic_chronosequence"]["tied_to"] = tie
    rows = _ensemble(t, 4.0)
    r = _row(rows)
    assert r["status"] == "PASS" and r["reads"] != "PASS"
    assert r["reads"].startswith("IN BAND, not a pass: rule 1 (")
    text = repr(tie) if isinstance(tie, str) else repr(tie[0])
    assert f"tied_to on {tuned}" in r["reads"] and text in r["reads"]
    header = independent_header(rows, t, ages=(50,))
    assert "Independent rows that apply: age 50: 0" in header and "Independent passes: 0 of 0 at 50" in header
    assert f"tied_to on {tuned}" in header
    assert "**PASS**" not in print_ensemble(rows, "header", t)
    # a mistyped tie on a row that has nothing to do with this one still makes it unclean
    t = _as(_targets(), "independent")
    t["tree_allometry"]["bark_thickness"]["tied_to"] = tie
    r = _row(_ensemble(t, 4.0))
    assert r["reads"] != "PASS" and "tied_to on tree_allometry.bark_thickness" in r["reads"]


def test_a_tie_written_on_the_other_row_is_in_the_notes():
    """The notes print ties written on other rows as well as the row's own, so a row left out of the count says why."""
    tuned = "stand_canopy.lai_baltic_chronosequence"
    t = _as(_targets(), "independent")
    t["stand_canopy"]["lai_baltic_chronosequence"]["tied_to"].append(NAME)
    rows = _ensemble(t, 4.0)
    line = next(ln for ln in print_ensemble(rows, "header", t).splitlines() if f"{NAME} (age 50)" in ln)
    assert f"tied to (written on the other row): {tuned}" in line
    header = independent_header(rows, t, ages=(50,))
    assert "a clean independent row that reads FAIL always is" in header


@pytest.mark.parametrize("scoring", ["INFO", "Info", " info "])
def test_scoring_info_is_read_whatever_its_case(scoring):
    rows = _ensemble(_as(_targets(), "independent", scoring=scoring), 4.0)
    assert _row(rows)["status"] == "INFO" and _row(rows)["reads"] == "INFO"
    assert "Independent rows that apply: age 50: 0" in independent_header(rows, _as(_targets(), "independent", scoring=scoring), ages=(50,))


@pytest.mark.parametrize("opened", [True, "yes", "read at the publisher", 1,
                                    "not opened, checked 2026-11-11", "false 0000-00-00", "Not read, 2026-11-11",
                                    "FALSE 2026-11-11"])
def test_source_opened_must_say_where_and_when(opened):
    """Part 2: source_opened is text with the date the page was read; True, or text with no date, is not enough,
    nor is text that starts with 'not' or 'false'."""
    reads = _row(_ensemble(_as(_targets(), "independent", source_opened=opened), 4.0))["reads"]
    assert reads != "PASS" and "2 (source not opened" in reads


def test_the_environment_file_is_checked(monkeypatch):
    """Part 5: the runs' environment file must be the one at their commit, as the species file must."""
    import tools.scorecard as sc
    files = {"species/betula_pendula.yaml": "s" * 64, "environments/forest.yaml": "e" * 64}
    monkeypatch.setattr(sc, "file_sha_at", lambda commit, path: files.get(path) if commit == "abc1234" else None)
    man = {"git_commit": "abc1234", "overrides": [], "species_sha256": "s" * 64,
           "environment_file": "environments/forest.yaml", "environment_sha256": "e" * 64}
    good = [_tree_run(4.0, manifest=man) for _ in range(20)]
    assert ensemble_facts(good)["problems"] == []
    changed = good[:19] + [_tree_run(4.0, manifest=dict(man, environment_sha256="x" * 64))]
    assert "environment file not the one at abc1234" in ensemble_facts(changed)["problems"]
    other = good[:19] + [_tree_run(4.0, manifest=dict(man, environment_file="environments/open.yaml"))]
    assert "runs not on one recorded environment file" in ensemble_facts(other)["problems"]
    none = [_tree_run(4.0, manifest={k: v for k, v in man.items() if not k.startswith("environment")}) for _ in range(20)]
    assert "runs not on one recorded environment file" in ensemble_facts(none)["problems"]
    missing = [_tree_run(4.0, manifest=dict(man, environment_file="environments/gone.yaml")) for _ in range(20)]
    assert "environment file environments/gone.yaml not in commit abc1234" in ensemble_facts(missing)["problems"]
