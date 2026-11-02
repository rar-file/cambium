"""Soil-water bucket option (BILJOU, Granier et al. 1999), off by default."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from treegen.growth import GrowthModel
from treegen.params import load_species


def _swb(rain, **kw):
    base = dict(awc_mm=75.0, rew_threshold=0.4, transpiration_lai_slope=0.125, transpiration_ratio_max=0.75,
                precipitation_mm=rain, dry_year_precipitation_mm=[0.0] * 5, pet_mm=[80.0, 99.0, 103.0, 69.0, 30.0],
                drought_scenario=False)
    base.update(kw)
    return SimpleNamespace(**base)


def _run(swb, lai):
    return GrowthModel._run_soil_water_balance(SimpleNamespace(SWB_MONTH_DAYS=GrowthModel.SWB_MONTH_DAYS), swb, lai)


def test_wet_season_never_limits():
    assert _run(_swb([1000.0] * 5), 3.0) == (1.0, 1.0)


def test_transpiration_ratio_capped_at_lai_6():
    """Granier 1999 Eq. 2: r = 0.125 LAI up to 0.75."""
    dry = _swb([0.0] * 5)
    assert _run(dry, 6.0) == _run(dry, 10.0)
    assert _run(dry, 3.0) != _run(dry, 6.0)


def test_dry_season_cuts_transpiration_below_threshold():
    min_rew, ratio = _run(_swb([0.0] * 5), 6.0)
    assert min_rew < 0.4
    assert 0.0 < ratio < 1.0
    # the dry-year rain is used only when the scenario is on
    assert _run(_swb([1000.0] * 5, drought_scenario=True), 6.0) == (min_rew, ratio)


def test_option_off_by_default():
    sp, _ = load_species("betula_pendula")
    assert sp.soil_water_balance.enabled is False
    assert sp.soil_water_balance.drought_scenario is False
