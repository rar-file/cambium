"""Run outputs: the option list and run manifest, and the light read under the
canopy at the target's measurement heights (output only)."""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

from treegen.environment import make_environment
from treegen.light import SUBCANOPY_LIGHT_HEIGHTS_M, LightField, ShadowPropagation
from treegen.params import load_environment, load_species, option_values, run_manifest


def test_option_values_lists_switches_and_stages():
    ns = SimpleNamespace(a=SimpleNamespace(enabled=True, k=0.4), b=SimpleNamespace(stem=SimpleNamespace(stage=2)),
                         c=False, d=SimpleNamespace(name="x"))
    assert option_values(ns) == {"a.enabled": True, "b.stem.stage": 2, "c": False}


def test_run_manifest_species_options():
    sp, raw = load_species("betula_pendula")
    manifest, options = run_manifest("betula_pendula", "sweden_open_field", sp)
    assert manifest["species_file"] == "species/betula_pendula.yaml"
    assert len(manifest["species_sha256"]) == 64
    assert options["light.woody_shade.enabled"] is raw["light"]["woody_shade"]["enabled"]
    assert options["germination.enabled"] is raw["germination"]["enabled"]
    on = set(manifest["options_on"])
    assert all((k in on) == bool(v) for k, v in options.items() if isinstance(v, bool))


def _field(S, lo, C=1.0, vs=0.5, periodic=True):
    return LightField(SimpleNamespace(vs=vs, C=C), np.asarray(S, np.float32), np.asarray(lo), periodic)


def test_subcanopy_light_reads_exposure_without_own_shade():
    S = np.full((4, 4, 8), 0.7)
    f = _field(S, [0, 0, 0])
    assert f.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) == pytest.approx(math.exp(-0.7), rel=1e-5)
    assert _field(np.zeros((4, 4, 8)), [0, 0, 0]).relative_light_at_heights((1.0,)) == pytest.approx(1.0)


def test_subcanopy_light_not_reported_where_not_computed():
    # grid starting above the measurement heights, or not a stand cell: no value
    assert _field(np.zeros((4, 4, 8)), [0, 0, 10]).relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) is None
    assert _field(np.zeros((4, 4, 8)), [0, 0, 0], periodic=False).relative_light_at_heights((1.0,)) is None


class _Env:
    """Sky-and-sun weights on four directions: two sky, two sun."""
    full_light = 1.0

    def light_directions(self):
        d = np.array([[0.0, 0.0, -1.0], [0.3, 0.0, -0.954], [0.0, 0.5, -0.866], [0.0, -0.6, -0.8]])
        return d, np.array([0.3, 0.2, 0.3, 0.2])

    def diffuse_weights(self):
        return np.array([0.6, 0.4, 0.0, 0.0])


def _propagation():
    lp = SimpleNamespace(voxel_size=0.5, extinction_coefficient=0.37, leaf_area_m2=0.0015, leaf_spread=0.0,
                         shadow_decay_length=50.0, shadow_horizontal_reach=50.0, penumbra_diffusion=0.05,
                         horizontal_margin=1.0, perception_radius=1.0, perception_cone_deg=60.0,
                         perception_softmin=0.1, perception_samples=8)
    return ShadowPropagation(_Env(), lp)


def _sources():
    rng = np.random.default_rng(1)
    pos = np.column_stack([rng.uniform(0, 4, 400), rng.uniform(0, 4, 400), rng.uniform(4, 8, 400)])
    pos[0, 2] = 0.1   # as the stems do in a run: the grid then reaches the ground
    return pos, np.full(len(pos), 8.0), np.array([[0.0, 0.0, 0.0], [4.0, 4.0, 8.0]])


def test_diffuse_output_leaves_the_growth_field_unchanged():
    pos, w, region = _sources()
    cell = (0.0, 0.0, 8, 8)
    plain = _propagation().compute(pos, w, region, periodic=cell)
    both = _propagation().compute(pos, w, region, periodic=cell, diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
    assert np.array_equal(plain.S, both.S)
    assert plain.diffuse_layers is None
    assert plain.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) is None


def test_diffuse_output_with_the_full_weights_equals_the_weighted_light():
    """Same calculation as the weighted light: same weights, same number."""
    pos, w, region = _sources()
    p = _propagation()
    p.diffuse_w = p.light_w.copy()
    f = p.compute(pos, w, region, periodic=(0.0, 0.0, 8, 8), diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
    assert f.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) == pytest.approx(
        f.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M), rel=1e-5)


def test_diffuse_output_differs_from_the_weighted_light_and_stays_a_fraction():
    pos, w, region = _sources()
    f = _propagation().compute(pos, w, region, periodic=(0.0, 0.0, 8, 8), diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
    d = f.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)
    assert 0.0 < d < 1.0
    assert d != pytest.approx(f.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M), rel=1e-6)


def test_environment_diffuse_weights_are_the_sky_alone():
    env = make_environment(load_environment("sweden_open_field")[0])
    d, w = env.light_directions()
    dw = env.diffuse_weights()
    assert len(dw) == len(d)
    assert dw.sum() == pytest.approx(1.0)
    n_sky = len(env.sky_samples()[0])
    assert (dw[n_sky:] == 0.0).all()
    assert dw[:n_sky] == pytest.approx(env.sky_samples()[1])
