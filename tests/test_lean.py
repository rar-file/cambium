"""Lean mode skips only what growth never reads back: the tree and every scored
output come out the same, and the skipped history really is gone."""
from __future__ import annotations

import numpy as np

import cli
from treegen.growth import GrowthModel
from treegen.runhash import SCORED_KEYS, output_digest, scored_digest

YEARS = 8


def _grow(lean):
    sp, _ = cli.load_species("betula_pendula")
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), 1, stand=True, soil=cli.make_soil(env_p), lean=lean)
    return m.run(YEARS)


def test_lean_changes_no_scored_output_and_no_part_of_the_tree():
    full, lean = _grow(False), _grow(True)
    assert scored_digest(full) == scored_digest(lean)
    for a, b in zip(full.stats, lean.stats):
        assert {k: a.get(k) for k in SCORED_KEYS} == {k: b.get(k) for k in SCORED_KEYS}
    for name in ("pos", "radius", "parent", "death", "birth", "axis", "order"):
        assert np.array_equal(getattr(full.tree, name)[:full.tree.n], getattr(lean.tree, name)[:lean.tree.n]), name
    assert full.rng.bit_generator.state == lean.rng.bit_generator.state
    assert full.roots.rng.bit_generator.state == lean.roots.rng.bit_generator.state


def test_lean_really_drops_the_history():
    full, lean = _grow(False), _grow(True)
    assert len(full.radius_history) > 0 and len(full.keyframes) > 0
    assert lean.radius_history == [] and lean.keyframes == {} and lean.roots.radius_history == []
    assert lean.stats[-1]["scaffold"] is None and lean.stats[-1]["roots"] is None
    # the full digest does differ, or this test would prove nothing about what was skipped
    assert output_digest(full) != output_digest(lean)


def test_full_mode_still_keeps_everything():
    full = _grow(False)
    assert full.stats[-1]["roots"] is not None
    assert full.stats[-1]["branches_by_order"]
    assert len(full.radius_history) == YEARS + 1   # year 0 too
