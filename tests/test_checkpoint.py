"""A run saved partway and resumed is the same run."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import cli
from treegen import checkpoint
from treegen.growth import GrowthModel
from treegen.plot import Plot
from treegen.runhash import output_digest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from golden import hash_tree  # noqa: E402

YEARS, AT = 8, 4


def _model():
    sp, _ = cli.load_species("betula_pendula")
    env_p, _ = cli.load_environment("sweden_open_field")
    return GrowthModel(sp, cli.make_environment(env_p), 1, stand=True, soil=cli.make_soil(env_p))


def test_a_tree_saved_and_resumed_is_the_same_tree(tmp_path):
    straight = _model().run(YEARS)
    m = _model()
    for _ in range(AT):
        m.step()
    path = checkpoint.save_model(m, tmp_path / "state.pkl")
    resumed = checkpoint.load_model(path)
    assert resumed.rng.bit_generator.state == m.rng.bit_generator.state
    assert resumed._dmg_rng.bit_generator.state == m._dmg_rng.bit_generator.state
    resumed.run(YEARS - AT)
    assert output_digest(resumed) == output_digest(straight)
    assert sorted(resumed.keyframes) == sorted(straight.keyframes)
    assert all(np.array_equal(resumed.keyframes[k], straight.keyframes[k]) for k in straight.keyframes)
    assert all(np.array_equal(a, b) for a, b in zip(resumed.radius_history, straight.radius_history))


def test_saving_leaves_the_running_model_untouched(tmp_path):
    straight = _model().run(YEARS)
    m = _model()
    for _ in range(AT):
        m.step()
    checkpoint.save_model(m, tmp_path / "state.pkl")
    m.run(YEARS - AT)
    assert output_digest(m) == output_digest(straight)


def test_a_plot_saved_and_resumed_is_the_same_plot(tmp_path):
    def plot():
        sp, _ = cli.load_species("betula_pendula")
        env_p, _ = cli.load_environment("sweden_open_field")
        return Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), 1, 1, "natural")

    a = plot()
    for _ in range(5):
        a.step()
    b = plot()
    for _ in range(3):
        b.step()
    b.checkpoint(tmp_path)
    b = Plot.resume(tmp_path)
    for _ in range(2):
        b.step()
    assert a.stats == b.stats
    for k in a.alive:
        assert a.trees[k].stats == b.trees[k].stats
        assert np.array_equal(a.trees[k].tree.pos[:a.trees[k].tree.n], b.trees[k].tree.pos[:b.trees[k].tree.n])


def test_scenario_values_change_only_what_they_name():
    ns = SimpleNamespace(a=SimpleNamespace(b=1), c=2)
    checkpoint.set_values(ns, ["a.b=5"])
    assert ns.a.b == 5 and ns.c == 2
    with pytest.raises(KeyError):
        checkpoint.set_values(ns, ["a.nope=5"])


def test_states_are_left_out_of_the_output_hash(tmp_path):
    (tmp_path / "stats.json").write_text("{}")
    (tmp_path / "state_010").mkdir()
    (tmp_path / "state_010" / "stats.json").write_text("{}")
    (tmp_path / "states").mkdir()
    (tmp_path / "states" / "x.json").write_text("{}")
    assert list(hash_tree(tmp_path)) == ["stats.json"]


def test_spilling_twice_keeps_the_first_file(tmp_path):
    sp, _ = cli.load_species("betula_pendula")
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), 1, stand=True, soil=cli.make_soil(env_p))
    for _ in range(3):
        m.step()
    m.spill_history(tmp_path)
    size = (tmp_path / "history_003.npz").stat().st_size
    assert size > 1000
    m.spill_history(tmp_path)
    assert (tmp_path / "history_003.npz").stat().st_size == size


def test_resume_sweeps_only_what_the_checkpoint_does_not_know(tmp_path):
    from treegen.plot import sweep_after_stop

    def touch(rel):
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"x")
        return f

    keep = [touch("tree_001/history/history_005.npz"), touch("tree_001/history/history_010.npz"), touch("checkpoint.pkl"),
            touch("tree_002/stats.json"), touch("state_010/tree_002/history/history_010.npz"),
            touch("tree_003/history/history_007.npz")]   # germinated 3 years late: 7 years old in plot year 10
    gone = [touch("tree_001/history/history_015.npz"),     # a later checkpoint that never finished
            touch("tree_002/history/history_010.npz"),     # a tree the checkpoint counts as dead
            touch("tree_001/history/history_015.npz.tmp"),
            touch("tree_003/history/history_009.npz"),     # the late tree's part of the checkpoint that never finished,
                                                           # whose number is still under the plot's year
            touch("checkpoint.pkl.tmp")]
    removed = sweep_after_stop(tmp_path, {1: 10, 3: 7})
    assert sorted(removed) == sorted(gone)
    assert all(f.exists() for f in keep) and not any(f.exists() for f in gone)
