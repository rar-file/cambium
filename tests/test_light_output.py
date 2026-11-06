"""The light under the canopy can be read with wood shade off too (output only)."""
import numpy as np

from treegen.environment import make_environment
from treegen.light import SUBCANOPY_LIGHT_HEIGHTS_M, ShadowPropagation
from treegen.params import load_environment, load_species


def _field(wood: bool):
    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    prop = ShadowPropagation(make_environment(env), sp.light)
    rng = np.random.default_rng(1)
    leaves = rng.uniform((0.0, 0.0, 6.0), (4.0, 4.0, 12.0), (400, 3))
    weights = np.full(len(leaves), 2.5)
    wood_pos = np.array([[2.0, 2.0, z] for z in np.arange(0.05, 12.0, 0.1)]) if wood else None
    wood_area = np.full(len(wood_pos), 1e-3) if wood else None
    all_pts = leaves if not wood else np.concatenate([leaves, wood_pos])
    region = np.stack([all_pts.min(0), all_pts.max(0)])
    cell = (0.0, 0.0, 40, 40)
    return prop.compute(leaves, weights, region, periodic=cell, wood_pos=wood_pos, wood_area=wood_area, k_wood=0.40,
                        diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M), leaves


def test_light_is_read_below_the_crown_without_wood():
    field, _ = _field(False)
    diffuse = field.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)
    total = field.relative_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)
    assert diffuse is not None and 0.0 < diffuse < 1.0
    assert total is not None and 0.0 < total < 1.0


def test_wood_still_shades_more_than_no_wood():
    with_wood, _ = _field(True)
    without, _ = _field(False)
    assert with_wood.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M) < without.diffuse_light_at_heights(SUBCANOPY_LIGHT_HEIGHTS_M)


def test_reading_low_layers_does_not_change_the_light_at_the_crown():
    """The field growth reads is the same whether or not the low layers are kept."""
    sp, _ = load_species("betula_pendula")
    env, _ = load_environment("sweden_open_field")
    prop = ShadowPropagation(make_environment(env), sp.light)
    rng = np.random.default_rng(2)
    leaves = rng.uniform((0.0, 0.0, 6.0), (4.0, 4.0, 12.0), (400, 3))
    weights = np.full(len(leaves), 2.5)
    region = np.stack([leaves.min(0), leaves.max(0)])
    cell = (0.0, 0.0, 40, 40)
    plain = prop.compute(leaves, weights, region, periodic=cell)
    kept = prop.compute(leaves, weights, region, periodic=cell, diffuse_heights=SUBCANOPY_LIGHT_HEIGHTS_M)
    probe = leaves[:50]
    assert np.allclose(plain.sample(probe), kept.sample(probe), rtol=1e-4, atol=1e-4)
