"""The lossless speed settings change no number.  Each kernel against the numpy form it copies, then whole short runs, off and on:
every yearly stat and every tree array, bit for bit.  tools/golden.py does the same on the four long runs."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import cli  # noqa: E402
from speed_compare import ARRAYS, TEST_A  # noqa: E402
from treegen import checkpoint, fast  # noqa: E402
from treegen.growth import GrowthModel  # noqa: E402
from treegen.plot import Plot  # noqa: E402

LOSSLESS = ["speed.compiled_carbon=true", "speed.compiled_mechanics=true", "speed.light_layers=true", "speed.keep_soil_grids=true", "speed.quick_solve=true", "speed.quick_levels=true"]


def test_sum_is_numpys_sum():
    rng = np.random.default_rng(3)
    for n in list(range(0, 300)) + [1000, 1024, 4096, 8193, 100001]:
        x = rng.normal(size=n) * 10 ** rng.uniform(-6, 6, n)
        assert float(x.sum()) == float(fast.np_sum(x, n)), n


@pytest.mark.parametrize("wrap,shape,sigma", [(True, (94, 94, 40), 0.6), (False, (60, 70, 35), 0.6), (True, (60, 40, 30), 1.5), (True, (3, 4, 9), 0.6), (False, (3, 4, 9), 1.5)])
def test_blur_is_scipys_blur(wrap, shape, sigma):
    from scipy.ndimage import gaussian_filter

    rng = np.random.default_rng(1)
    d = np.zeros(shape, np.float32)
    n = int(np.prod(shape)) // 4 + 1
    np.add.at(d, tuple(rng.integers(0, s, n) for s in shape), rng.uniform(0, 0.03, n).astype(np.float32))
    want = gaussian_filter(d, sigma, mode=("wrap", "wrap", "constant") if wrap else "constant", truncate=3.0)
    a = d.transpose(2, 0, 1).copy()
    b = np.zeros_like(a)
    has = fast.blur_layers(a, b, fast.gaussian_weights(sigma), wrap)
    assert np.ascontiguousarray(b.transpose(1, 2, 0)).tobytes() == want.tobytes()
    assert (has | ~want.any(axis=(0, 1))).all()


def digest(model) -> str:
    h = hashlib.sha256()
    for name in ARRAYS:
        h.update(getattr(model.tree, name)[: model.tree.n].tobytes())
    if model.roots is not None:
        for name in ("pos", "radius", "death"):
            h.update(getattr(model.roots.tree, name)[: model.roots.tree.n].tobytes())
    return h.hexdigest()


def tree(seed, years, sets):
    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, sets)
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), seed, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(years):
        m.step()
    return json.dumps(m.stats, sort_keys=True, default=str), digest(m)


@pytest.mark.parametrize("base", [[], TEST_A], ids=["default", "testA"])
def test_a_tree_is_the_same_with_the_settings_on(base):
    assert tree(2, 16, base) == tree(2, 16, base + LOSSLESS)


@pytest.mark.parametrize("base", [[], TEST_A], ids=["default", "testA"])
def test_dropping_dead_nodes_keeps_every_yearly_stat(base):
    sets = base + ["speed.compiled_carbon=true"]
    assert tree(3, 24, sets)[0] == tree(3, 24, sets + ["speed.drop_dead=true"])[0]


def test_a_dropped_tree_holds_only_what_it_needs():
    sp, _ = cli.load_species("betula_pendula")
    checkpoint.set_values(sp, ["speed.drop_dead=true"])
    env_p, _ = cli.load_environment("sweden_open_field")
    m = GrowthModel(sp, cli.make_environment(env_p), 2, stand=True, soil=cli.make_soil(env_p), lean=True)
    for _ in range(24):
        m.step()
    T = m.tree
    alive = T.death[: T.n] < 0
    assert alive.sum() > 0.2 * T.n                   # most of what's left lives
    par = T.parent[: T.n]
    assert par[0] == -1 and (par[1:] >= 0).all() and (par[1:] < T.n).all()
    assert alive[par[alive & (par >= 0)]].all()      # a living node's parent lives
    for link in (T.main_child[: T.n], T.lat_child[: T.n]):
        ok = alive & (link >= 0)
        assert (T.parent[link[ok]] == np.nonzero(ok)[0]).all()


def test_a_plot_is_the_same_with_the_settings_on():
    def run(sets):
        sp, _ = cli.load_species("betula_pendula")
        checkpoint.set_values(sp, sets)
        env_p, _ = cli.load_environment("sweden_open_field")
        stages = sorted(sp.stand.thinning, key=lambda s: float(s.from_height_m))
        n_final = 6 * float(stages[-1].stems_per_ha) / float(stages[0].stems_per_ha)
        p = Plot(sp, cli.make_environment(env_p), lambda: cli.make_soil(env_p), n_final, 1, "natural", lean=True)
        for _ in range(9):
            p.step()
        return json.dumps(p.stats, sort_keys=True, default=str), {k: digest(p.trees[k]) for k in p.alive}

    assert run([]) == run(LOSSLESS)
