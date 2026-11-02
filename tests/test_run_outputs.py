"""Run outputs: the option list and run manifest, and the light read under the
canopy at the target's measurement heights (output only)."""
from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

from treegen.light import SUBCANOPY_LIGHT_HEIGHTS_M, LightField
from treegen.params import load_species, option_values, run_manifest


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
