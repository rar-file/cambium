"""What a species file must hold, with units and ranges, and where each value came from.

Nothing in the growth model reads this file.  ``validate`` checks a species file;
``read_labels`` says of each value whether it's sourced, TUNED or VERIFY.
tools/species_report.py and docs/adding_a_species.md are how it's used.

The ranges are limits of sense, not targets: a value outside one is almost certainly a
slip of a unit or a digit.  A value inside one can still be wrong.

A key this table doesn't know gives a warning, not an error, so a new setting can
be added to a species file before it's added here.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

STATUSES = ("sourced", "TUNED", "VERIFY")

# Blocks a species can go without, and what's lost.  Everything else is required.
OPTIONAL_BLOCKS = {
    "damage": "no old age, wind or snow damage",
    "field_layer_competition": "no clear-cut field layer option",
    "germination": "no germination option",
    "leader_damage": "no browsing of the leader",
    "plot": "tools/plot.py can't run",
    "regeneration": "no natural regeneration in plots",
    "soil_water_balance": "no soil water balance option",
    "speed": "no speed settings: everything runs the plain way",
}


@dataclass(frozen=True)
class Field:
    path: str
    kind: str                     # number | integer | switch | choice | text | numbers | table
    unit: str = ""
    lo: float | None = None
    hi: float | None = None
    what: str = ""
    optional: bool = False        # the code does without it
    nullable: bool = False        # null is a meaningful value
    choices: tuple = ()
    length: tuple | None = None   # numbers: (shortest, longest)
    columns: tuple = ()           # table: the keys of each row


FIELDS: list[Field] = []


def _n(path, unit, lo, hi, what, **k):
    FIELDS.append(Field(path, "number", unit, lo, hi, what, **k))


def _i(path, unit, lo, hi, what, **k):
    FIELDS.append(Field(path, "integer", unit, lo, hi, what, **k))


def _b(path, what, **k):
    FIELDS.append(Field(path, "switch", what=what, **k))


def _c(path, choices, what, **k):
    FIELDS.append(Field(path, "choice", what=what, choices=tuple(choices), **k))


def _t(path, what, **k):
    FIELDS.append(Field(path, "text", what=what, **k))


def _l(path, unit, lo, hi, what, length=(1, 16), **k):
    FIELDS.append(Field(path, "numbers", unit, lo, hi, what, length=length, **k))


def _r(path, columns, what, **k):
    FIELDS.append(Field(path, "table", what=what, columns=tuple(columns), **k))


# ---------------------------------------------------------------------- species
_t("species.scientific_name", "scientific name, with authority")
_t("species.common_name", "common name", optional=True)
# ------------------------------------------------------------------------ shoot
_n("shoot.internode_length", "m", 0.001, 0.2, "long-shoot internode length; one model node is one real node")
_n("shoot.short_shoot_internode_length", "m", 0.0001, 0.05, "short-shoot internode length; recorded, no code reads it", optional=True)
_n("shoot.max_shoot_length", "m", 0.05, 5.0, "longest annual shoot")
_n("shoot.min_expansion", "-", 0.0, 1.0, "smallest share of full expansion a dry year allows")
_n("shoot.min_height_above_ground", "m", 0.0, 1.0, "shoots stay this far above the ground")
_n("shoot.ground_contact_height", "m", 0.0, 3.0, "a descending tip below this has reached the herb layer")
_b("shoot.stop_at_ground", "a shoot reaching the ground stops, instead of turning along it")
# --------------------------------------------------------------------- resource
_n("resource.alpha", "carbon units per leaf per year", 0.1, 50.0, "carbon one reference leaf fixes in full light")
_n("resource.apical_dominance", "-", 0.0, 1.0, "share of a split going to the apex where the lateral is a bud or spur")
_n("resource.apical_control_young", "-", 0.0, 1.0, "the same where the lateral is a branch, young tree")
_n("resource.apical_control_old", "-", 0.0, 1.0, "the same, old tree")
_n("resource.apical_control_transition_age", "years", 0.0, 1000.0, "middle of the change from young to old")
_n("resource.apical_control_transition_width", "years", 0.01, 500.0, "width of that change")
_n("resource.gravimorphism", "-", 0.0, 5.0, "how much more vigour an upward shoot has")
_n("resource.branch_aging_years", "years", 0.1, 2000.0, "vigour of a limb's buds decays with this time constant")
_n("resource.stem_aging_years", "years", 0.1, 5000.0, "the same for the stem's buds")
_b("resource.limbs_inherit_stem_age", "a limb's buds start at the age the stem had when it made them")
_b("resource.reiteration.enabled", "old crowns rebuild from upper limbs")
_n("resource.reiteration.min_age", "years", 0.0, 2000.0, "from this tree age")
_n("resource.reiteration.decline_fraction", "-", 0.0, 1.0, "the leader's growth below this share of its peak")
_n("resource.reiteration.upper_crown_fraction", "-", 0.0, 1.0, "limb attached in this upper share of the crown")
_n("resource.reiteration.min_light", "relative light", 0.0, 1.0, "limb tip lit at least this much")
_n("resource.reiteration.min_relative_vigour", "-", 0.0, 10.0, "at least this share of the leader's vigour")
_n("resource.reiteration.interval_years", "years", 0.0, 200.0, "years between new complexes")
_n("resource.reiteration.rejuvenation", "-", 0.0, 1.0, "a complex's bud age is multiplied by this")
_n("resource.reiteration.setpoint_angle_deg", "deg from vertical", 0.0, 180.0, "direction a complex then seeks")
_n("resource.maintenance_per_internode", "carbon units per year", 0.0, 10.0, "upkeep of one living internode")
_n("resource.growth_respiration_coefficient", "g C per g C built", 0.0, 2.0, "respired while building tissue")
_b("resource.leaf_costs.enabled", "leaves and fine roots cost carbon")
_n("resource.leaf_costs.wood_basic_density_kg_m3", "kg/m3", 150.0, 1300.0, "wood basic density")
_n("resource.leaf_costs.carbon_fraction", "g C/g", 0.3, 0.65, "carbon in dry matter")
_n("resource.leaf_costs.leaf_maintenance_gc_per_g", "g C/g/year", 0.0, 10.0, "leaf maintenance respiration")
_n("resource.leaf_costs.fine_root_to_leaf_mass", "g/g", 0.0, 20.0, "fine root per leaf dry mass")
_b("resource.leaf_costs.charge_fresh_laterals", "charge next spring's clusters on fresh lateral buds")
_n("resource.leaf_costs.fine_root_maintenance_gc_per_g", "g C/g/year", 0.0, 10.0, "fine-root maintenance respiration")
_n("resource.branch_export_fraction", "-", 0.0, 1.0, "share a limb exports to the stem; null = one shared pool", nullable=True)
_b("resource.young_limbs_import", "young limbs draw on the stem pool until they export")
_n("resource.root_share_min", "-", 0.0, 1.0, "root share of carbon without water stress")
_n("resource.root_share_max", "-", 0.0, 1.0, "root share with stomata shut")
_n("resource.root_segments_per_unit", "per carbon unit", 0.0, 10.0, "root segments built per carbon unit")
# --------------------------------------------------------------------- bud_fate
_n("bud_fate.long_shoot_threshold", "nodes", 0.0, 100.0, "a lateral bud makes a long shoot with at least this many nodes of resource")
_n("bud_fate.min_tip_extension", "nodes", 0.0, 1.0, "below this share of a node a tip doesn't extend")
_b("bud_fate.axillary_buds_below_one_metamer", "an increment below one node still makes an axillary bud")
_b("bud_fate.density_control.enabled", "dense local foliage suppresses buds")
_n("bud_fate.density_control.af_full", "m2/m3", 0.0, 50.0, "leaf density below which no bud is lost")
_n("bud_fate.density_control.af_zero", "m2/m3", 0.0, 100.0, "leaf density above which no bud grows")
_n("bud_fate.density_control.cell_m", "m", 0.01, 10.0, "grid cell for leaf density")
_b("bud_fate.density_control.after_growth", "density read after this year's growth")
_n("bud_fate.short_shoot_light", "relative light", 0.0, 5.0, "a bud that doesn't extend makes a short shoot at this light; above 1 no short shoots form")
_n("bud_fate.short_shoot_survival_light", "relative light", 0.0, 1.0, "a short shoot dies below this")
_n("bud_fate.spur_release_threshold", "nodes", 0.0, 1000.0, "resource a short shoot needs to become a long shoot")
_b("bud_fate.short_shoots_self_financing", "short shoots are no sink in the split")
_b("bud_fate.idle_buds_no_sink", "buds that won't grow this year take no share")
_b("bud_fate.borchert_honda_published", "the split as published, without this model's weights")
_i("bud_fate.spur_lifespan", "years", 1, 500, "short-shoot lifespan; null = dies only of light", nullable=True)
_i("bud_fate.dormant_bud_lifespan", "years", 0, 500, "years an unbroken lateral bud stays viable")
# ------------------------------------------------------------------------ light
_n("light.voxel_size", "m", 0.02, 1.0, "voxel edge for shade")
_n("light.extinction_coefficient", "-", 0.1, 1.5, "canopy K_PAR")
_n("light.leaf_area_m2", "m2", 1e-6, 0.5, "one-sided area of one reference leaf")
_b("light.sun_shade.enabled", "leaf size and mass follow the leaf's light")
_n("light.sun_shade.lma_shade_g_m2", "g/m2", 5.0, 500.0, "leaf mass per area in deep shade")
_n("light.sun_shade.lma_sun_increase_g_m2", "g/m2", 0.0, 500.0, "added in full sun")
_n("light.sun_shade.lma_exponent", "-", 0.0, 20.0, "shape of that rise")
_n("light.sun_shade.lma_reference_g_m2", "g/m2", 5.0, 500.0, "leaf mass per area where leaf_area_m2 applies")
_n("light.sun_shade.size_lma_exponent", "-", 0.0, 5.0, "leaf size goes as (reference / LMA) to this")
_n("light.leaf_spread", "m", 0.0, 2.0, "SD of a bud's leaf area around its node")
_b("light.exclude_own_shoot", "no shoot shades itself")
_n("light.shadow_decay_length", "m", 1.0, 1e6, "shade fades with this length going down")
_n("light.shadow_horizontal_reach", "m", 0.5, 1e6, "shade fades over this sideways travel")
_n("light.penumbra_diffusion", "m", 0.0, 5.0, "how fast a shadow's edge widens")
_n("light.horizontal_margin", "m", 0.0, 200.0, "keeps the grid's wrap off the crown")
_n("light.foliage_weight.new_leaf", "leaves", 0.0, 100.0, "leaves at a fresh node")
_n("light.foliage_weight.spur", "leaves", 0.0, 100.0, "leaves on a short shoot")
_n("light.foliage_weight.dormant", "leaves", 0.0, 100.0, "leaves at a dormant bud")
_n("light.foliage_weight.early_leaves", "leaves", 0.0, 100.0, "extra cluster at the base of a season's shoot")
_n("light.foliage_weight.late_leaf_season_fraction", "-", 0.0, 1.0, "share of the season late leaves work")
_n("light.perception_radius", "m", 0.01, 20.0, "how far a bud senses light")
_n("light.perception_cone_deg", "deg", 1.0, 180.0, "half-angle it senses in")
_i("light.perception_samples", "directions", 1, 4096, "directions it probes")
_n("light.perception_softmin", "shade units", 1e-6, 10.0, "softness of choosing the lightest direction")
_b("light.woody_shade.enabled", "wood casts shade of its own")
_n("light.woody_shade.k_wood", "-", 0.0, 3.0, "extinction by wood")
# --------------------------------------------------------------------- shedding
_n("shedding.light_per_leaf_threshold", "relative light", 0.0, 1.0, "a limb is shed when its leaves' mean light falls below this")
_i("shedding.min_branch_age", "years", 0, 500, "younger limbs aren't shed")
_b("shedding.carbon_balance", "a limb that can't pay its upkeep is shed")
# ----------------------------------------------------------------- architecture
_n("architecture.phyllotaxis_orthotropic_deg", "deg", 0.0, 360.0, "divergence on the upright leader")
_n("architecture.phyllotaxis_plagiotropic_deg", "deg", 0.0, 360.0, "divergence on side shoots")
_n("architecture.distichous_jitter_deg", "deg", 0.0, 180.0, "scatter around the side shoot's plane")
_l("architecture.branch_angle_deg", "deg", 0.0, 180.0, "insertion angle by the new lateral's order")
_n("architecture.sympodial_deviation_deg", "deg", 0.0, 180.0, "yearly deflection of the axis; 0 = monopodial")
_n("architecture.sympodial_bend_length_m", "m", 0.0, 10.0, "over this length; null = a kink", nullable=True)
_n("architecture.direction_noise_per_sqrt_m", "1/sqrt(m)", 0.0, 10.0, "random wander of a growing shoot")
_n("architecture.direction_noise_correlation_m", "m", 0.0, 50.0, "correlation length of that wander; null = independent", nullable=True)
# ---------------------------------------------------------------------- tropism
_l("tropism.phototropism_per_m", "1/m", 0.0, 100.0, "turning towards light, by order")
_l("tropism.gravitropism_per_m", "1/m", 0.0, 100.0, "turning to the set-point, by order")
_b("tropism.stem_crown_phototropism", "the leader turns to the lit side of the crown")
_l("tropism.setpoint_angle_deg", "deg from vertical", 0.0, 180.0, "direction sought, by order")
# -------------------------------------------------------------------- mechanics
_b("mechanics.enabled", "bending under load and posture control")
_n("mechanics.wood_density", "kg/m3", 200.0, 1600.0, "fresh wood density")
_n("mechanics.leaf_mass", "kg", 1e-7, 0.1, "fresh mass of one leaf")
_n("mechanics.youngs_modulus_wood", "Pa", 1e8, 5e10, "bending stiffness of wood")
_n("mechanics.youngs_modulus_shoot", "Pa", 1e7, 5e10, "stiffness of thin new shoots")
_n("mechanics.reaction_wood_coefficient", "-", 0.0, 1.0, "yearly posture correction")
_b("mechanics.sine_law", "correction follows the sine of the error")
_n("mechanics.sine_law_saturation_deg", "deg", 0.1, 90.0, "full correction from this error on")
_n("mechanics.pendulous_radius", "m", 1e-5, 0.5, "shoots thinner than this hang; very small = none hang")
_n("mechanics.pendulous_sharpness", "-", 0.0, 50.0, "how sharply")
_i("mechanics.substeps", "steps", 1, 100, "load steps per year")
_n("mechanics.max_rotation_per_step", "rad", 0.001, 3.2, "most an internode turns in a step")
# ------------------------------------------------------------------- pipe_model
_b("pipe_model.sapwood_for_next_season", "diagnosis only")
_n("pipe_model.exponent", "-", 1.0, 5.0, "r_parent^g = sum r_child^g")
_n("pipe_model.tip_radius", "m", 1e-5, 0.05, "radius of a new long-shoot tip")
_n("pipe_model.spur_radius", "m", 1e-6, 0.05, "pipe added by a short shoot")
_c("pipe_model.growth", ("pipe", "stem_rings", "rings", "lignum"), "how radii grow")
_n("pipe_model.sapwood_senescence_per_year", "per year", 0.0, 1.0, "share of conducting wood that stops each year")
_b("pipe_model.sapwood", "the requirement is on conducting wood, with senescence")
_b("pipe_model.crown_rise_heartwood", "sapwood below the crown retires to heartwood")
_b("pipe_model.sapwood_replacement_is_upkeep", "ring replacement counts as upkeep in the death test")
_n("pipe_model.huber_radius_exponent", "-", 0.0, 5.0, "Huber value's rise with radius", nullable=True)
_n("pipe_model.huber_path_exponent", "-", 0.0, 5.0, "Huber value's rise with path length", nullable=True)
_n("pipe_model.huber_path_reference_m", "m", 1e-3, 50.0, "path length where huber_value was measured")
_n("pipe_model.wood_volume_per_carbon", "m3 per carbon unit", 1e-9, 1e-2, "the size of the model's carbon unit")
_b("pipe_model.stress_floor.enabled", "rings at least keep self-weight stress safe")
_n("pipe_model.stress_floor.wood_mor_green_mpa", "MPa", 1.0, 300.0, "green modulus of rupture")
_n("pipe_model.stress_floor.safety_factor", "-", 1.0, 50.0, "strength over working stress")
_b("pipe_model.wind_load.enabled", "rings at least keep wind stress safe")
_n("pipe_model.wind_load.wind_speed_m_s", "m/s", 0.0, 90.0, "design wind speed")
_n("pipe_model.wind_load.wood_mor_green_mpa", "MPa", 1.0, 300.0, "green modulus of rupture")
_n("pipe_model.wind_load.knot_factor", "-", 0.0, 2.0, "strength lost to knots")
_n("pipe_model.wind_load.safety_factor", "-", 1.0, 50.0, "strength over working stress")
_n("pipe_model.wind_load.air_density_kg_m3", "kg/m3", 0.8, 1.6, "air density")
_n("pipe_model.wind_load.streamlining_c", "-", 0.0, 50.0, "crown drag coefficient")
_n("pipe_model.wind_load.streamlining_n", "-", 0.0, 5.0, "its fall with wind speed")
_n("pipe_model.wind_load.streamlining_min_wind_m_s", "m/s", 0.0, 90.0, "streamlining starts")
_n("pipe_model.wind_load.streamlining_max_wind_m_s", "m/s", 0.0, 90.0, "streamlining ends")
_n("pipe_model.wind_load.deflection_loading_factor", "-", 1.0, 5.0, "extra load from the stem's deflection")
_i("pipe_model.stem_theory.stage", "stage", 0, 2, "0 off; 1 plain pipe model below the crown; 2 plus the wind envelope")
_n("pipe_model.stem_theory.wind_speed_m_s", "m/s", 0.0, 90.0, "wind at the canopy top")
_n("pipe_model.stem_theory.canopy_wind_attenuation", "-", 0.0, 20.0, "wind's fall below the canopy top")
# --------------------------------------------------------------------- geometry
_c("geometry.root_flare_mode", ("buttress", "bell"), "shape of the stem base")
_l("geometry.root_collar_height_coef", "cm per cm, cm per m", 0.0, 10.0, "root collar height from DBH and height", length=(2, 2))
_n("geometry.root_flare_extra", "-", 0.0, 10.0, "radius gain at the ground, bell shape")
_n("geometry.root_flare_height", "m", 0.01, 20.0, "its decay height")
_n("geometry.junction_blend", "-", 0.0, 10.0, "junction fillet, per child radius")
_n("geometry.collar_extra", "-", 0.0, 10.0, "branch collar's extra radius")
_n("geometry.collar_length", "child radii", 0.0, 50.0, "its decay length")
# -------------------------------------------------------------------- reference
_n("reference.height.site_index_low", "m", 1.0, 80.0, "lower site index of the height check")
_n("reference.height.site_index_high", "m", 1.0, 80.0, "upper site index of the height check")
_n("reference.height.asi", "-", 0.01, 1000.0, "Hossfeld IV curve: asi")
_n("reference.height.beta", "-", 0.01, 1e6, "Hossfeld IV curve: beta")
_n("reference.height.b2", "-", 0.01, 10.0, "Hossfeld IV curve: b2")
_n("reference.height.years_to_breast_height", "years", 0.0, 100.0, "germination to 1.3 m")
_n("reference.crown.intercept_m", "m", -10.0, 30.0, "crown diameter from DBH: intercept")
_n("reference.crown.slope_m_per_m", "m/m", 0.0, 100.0, "crown diameter from DBH: slope")
_l("reference.dbh.open_grown_band_cm", "cm", 0.0, 500.0, "open-grown DBH band", length=(2, 2))
_n("reference.dbh.band_age", "years", 1.0, 5000.0, "at this age")
# ---------------------------------------------------------------- leader_damage
_b("leader_damage.enabled", "the leader's last shoot can be lost")
_i("leader_damage.replacement_leaders", "shoots", 0, 20, "side shoots that become leaders")
_n("leader_damage.replacement_zone_m", "m", 0.0, 20.0, "from this far below the wound")
_n("leader_damage.bite_diameter_m", "m", 0.0, 0.2, "browsing clips down to this diameter", nullable=True)
_r("leader_damage.events", ("name", "min_height_m", "max_height_m", "probability_per_year"), "what can take the leader")
# ----------------------------------------------------------------------- damage
_b("damage.enabled", "old age, wind and snow can act (treegen/damage.py)")
_n("damage.dbh_over_bark_factor", "cm/cm", 1.0, 2.0, "over-bark DBH per wood DBH")
_n("damage.stem_form_factor", "-", 0.2, 1.0, "stem volume over pi/4 DBH^2 H")
_b("damage.old_age.enabled", "ageing can kill")
_n("damage.old_age.amax_b0", "-", -20.0, 30.0, "ln(maximum age) = b0 + b1 SIS + b2 ln(n)")
_n("damage.old_age.amax_b1", "per m", -1.0, 1.0, "b1")
_n("damage.old_age.amax_b2", "-", -2.0, 2.0, "b2")
_n("damage.old_age.amax_n", "trees", 1.0, 1e7, "n the maximum age is read at")
_n("damage.old_age.site_index_sis_m", "m", 1.0, 80.0, "site index on the top-height-at-100 scale")
_n("damage.old_age.ageing_a", "-", 0.0, 100.0, "p = 1 / (1 + exp(a - b A / AMAX)): a")
_n("damage.old_age.ageing_b", "-", 0.0, 100.0, "b")
_n("damage.old_age.years_to_breast_height", "years", 0.0, 100.0, "A counts rings at breast height")
_b("damage.wind.enabled", "storms can snap and uproot")
_n("damage.wind.intercept", "logit", -20.0, 20.0, "chance of wind damage per period on the mean tree")
_n("damage.wind.site_effect", "logit", -10.0, 10.0, "soil type's effect")
_n("damage.wind.prior_damage", "logit", -10.0, 10.0, "effect of earlier stem damage")
_n("damage.wind.period_years", "years", 0.1, 100.0, "the period the chance is per")
_n("damage.wind.population_offset", "logit", -10.0, 10.0, "brings the mean tree to the observed damage")
_n("damage.wind.storm_return_years", "years", 1.0, 1000.0, "years between storms")
_n("damage.wind.wind_from_deg", "deg", 0.0, 360.0, "where storms come from")
_n("damage.wind.wind_from_sd_deg", "deg", 0.0, 180.0, "scatter of that")
_n("damage.wind.min_dbh_cm", "cm", 0.0, 100.0, "smaller trees take no wind damage")
for _group, _unit, _hi in (("age", "years", 5000.0), ("stems_per_ha", "stems/ha", 1e6), ("basal_area_m2_ha", "m2/ha", 500.0), ("slenderness", "m/cm", 10.0)):
    _n(f"damage.wind.{_group}.per_sd", "logit per SD", -10.0, 10.0, f"effect of {_group}, per standard deviation")
    _n(f"damage.wind.{_group}.mean", _unit, 0.0, _hi, "mean in the data")
    _n(f"damage.wind.{_group}.sd", _unit, 1e-6, _hi, "standard deviation in the data")
    _l(f"damage.wind.{_group}.range", _unit, 0.0, _hi, "kept inside the data's range", length=(2, 2))
_n("damage.failure.mor_green_mpa", "MPa", 1.0, 300.0, "stem strength under short loads")
_n("damage.failure.even_odds_log_ratio", "-", -10.0, 10.0, "ln(root moment / stem moment) at even odds of uprooting")
_n("damage.failure.spread", "-", 0.01, 10.0, "width of that choice")
_n("damage.snap.intercept", "-", 0.0, 1.0, "relative snapping height = intercept + slenderness x H/D + prior damage")
_n("damage.snap.slenderness", "per m/cm", -1.0, 1.0, "slenderness")
_n("damage.snap.prior_damage", "-", -1.0, 1.0, "prior damage")
_n("damage.snap.beta_concentration", "-", 0.1, 1000.0, "spread of the snapping height")
_b("damage.snow.enabled", "wet snow can break and bend")
_n("damage.snow.return_years", "years", 1.0, 1000.0, "years between damaging snowfalls")
_l("damage.snow.load_range_kg_m2", "kg/m2 of crown", 0.0, 500.0, "load of a damaging snowfall", length=(2, 2))
_n("damage.snow.crown_catch_fraction", "-", 0.0, 1.0, "share of the crown's area that holds the load")
_n("damage.snow.lever_fraction", "-", 0.0, 1.0, "the load's offset from the stem, per height")
_n("damage.snow.spread", "-", 0.01, 10.0, "width of the break")
_n("damage.snow.bend_buckling_factor", "-", 0.0, 1000.0, "stems below this buckling factor bend")
_n("damage.snow.bend_max_dbh_cm", "cm", 0.0, 500.0, "only stems under this DBH bend")
_n("damage.snow.min_break_dbh_cm", "cm", 0.0, 500.0, "stems under this DBH bend and don't break")
_n("damage.uproot.mound_radius_factor", "-", 0.1, 10.0, "mound radius per plate radius")
_n("damage.uproot.mound_distance_factor", "-", 0.0, 10.0, "mound's distance past the hinge per plate radius")
_n("damage.uproot.relief_half_life_years", "years", 0.1, 5000.0, "how fast pit and mound fade")
# ------------------------------------------------------------------------- plot
_l("plot.germination_years", "years", 0.0, 100.0, "germination delays, with weights below")
_l("plot.germination_weights", "-", 0.0, 1.0, "their shares, adding up to 1")
_n("plot.vigour_sd", "-", 0.0, 2.0, "heritable spread of carbon gain, lognormal SD")
# ----------------------------------------------------------------- regeneration
_n("regeneration.seeds_ref", "seeds/year", 0.0, 1e9, "seeds of a tree of dbh_ref_m")
_n("regeneration.dbh_ref_m", "m", 0.01, 5.0, "that tree's DBH")
_n("regeneration.fecundity_exponent", "-", 0.0, 10.0, "seeds go as DBH to this")
_i("regeneration.maturity_years", "years", 0, 1000, "first seed at this age")
_n("regeneration.dispersal_mean_m", "m", 0.1, 20000.0, "mean seed flight")
_n("regeneration.establishment_mineral", "per seed", 0.0, 1.0, "one-year seedlings per seed on bare mineral soil")
_n("regeneration.establishment_organic", "per seed", 0.0, 1.0, "the same on the organic layer")
_n("regeneration.cell_m", "m", 0.05, 20.0, "ground grid cell")
_n("regeneration.mineral_initial", "-", 0.0, 1.0, "bare soil share at the start")
_n("regeneration.mineral_new_per_year", "per year", 0.0, 1.0, "newly bared each year")
_n("regeneration.mineral_half_life_years", "years", 0.01, 1000.0, "half-life of bare soil")
# ------------------------------------------------------------------------ stand
_i("stand.cell_trees", "trees", 1, 50, "trees across the light grid's cell")
_n("stand.shadow_horizontal_reach", "m", 0.5, 1e6, "sideways fading in a closed stand")
_n("stand.shadow_decay_length", "m", 1.0, 1e6, "downward fading; null = as light", nullable=True)
_c("stand.layout", ("lattice", "random"), "how neighbours stand")
_n("stand.min_distance", "-", 0.0, 1.0, "closest neighbours, per mean spacing")
_n("stand.size_cv", "-", 0.0, 2.0, "spread of neighbours' size")
_r("stand.thinning", ("from_height_m", "stems_per_ha"), "stem density by top height")
# ------------------------------------------------------------------------ stats
_n("stats.crown_base_min_leaf_share", "-", 0.0, 1.0, "a limb counts for the crown base with this share of the leaves")
_n("stats.hanging_twig_min_length", "m", 0.0, 50.0, "shorter hanging runs aren't counted")
# ------------------------------------------------------------------- hydraulics
_n("hydraulics.transpiration_max", "kg/m2/s", 1e-7, 1e-2, "transpiration of a fully lit leaf at midday")
_n("hydraulics.xylem_conductivity", "kg/m/s/MPa", 1e-3, 500.0, "xylem-specific conductivity")
_n("hydraulics.huber_value", "m2/m2", 1e-7, 0.1, "xylem area per leaf area; null = from the visible wood", nullable=True)
_n("hydraulics.conductivity_reference_radius", "m", 1e-4, 5.0, "conductivity is full from this radius")
_n("hydraulics.conductivity_exponent", "-", 0.0, 10.0, "its fall in thin wood")
_n("hydraulics.root_xylem_conductivity", "kg/m/s/MPa", 1e-3, 500.0, "the same for roots")
_n("hydraulics.psi_stomata_open", "MPa", -50.0, 0.0, "stomata start closing")
_n("hydraulics.psi_stomata_closed", "MPa", -50.0, 0.0, "stomata shut")
_n("hydraulics.psi_full_expansion", "MPa", -50.0, 0.0, "expansion full above this")
_n("hydraulics.psi_turgor_loss", "MPa", -50.0, 0.0, "expansion stops")
_c("hydraulics.expansion_water_potential", ("predawn", "midday"), "which water potential drives expansion")
# ------------------------------------------------------------------------ roots
_n("roots.segment_length", "m", 0.005, 1.0, "structural root segment")
_n("roots.max_extension_per_year", "m", 0.01, 20.0, "longest annual extension of a root tip")
_i("roots.radicle_segments", "segments", 1, 100, "the germinating seed's root")
_n("roots.tip_radius", "m", 1e-5, 0.05, "root tip radius")
_n("roots.min_depth", "m", 0.0, 2.0, "roots stay this deep")
_n("roots.taproot_fade_years", "years", 0.01, 5000.0, "the taproot's downward pull fades over this")
_n("roots.taproot_max_depth", "m", 0.0, 50.0, "and stops at this depth")
_n("roots.taproot_setpoint_deg", "deg from up", 0.0, 180.0, "taproot direction")
_n("roots.taproot_gravitropism_per_m", "1/m", 0.0, 100.0, "taproot's pull")
_n("roots.lateral_setpoint_deg", "deg from up", 0.0, 180.0, "lateral direction")
_n("roots.lateral_setpoint_spread_deg", "deg", 0.0, 90.0, "scatter of that")
_n("roots.lateral_gravitropism_per_m", "1/m", 0.0, 100.0, "lateral's pull")
_n("roots.sinker_setpoint_deg", "deg from up", 0.0, 180.0, "sinker direction")
_n("roots.sinker_gravitropism_per_m", "1/m", 0.0, 100.0, "sinker's pull")
_n("roots.sinker_probability", "-", 0.0, 1.0, "chance a lateral near the stem is a sinker")
_n("roots.sinker_zone_radius", "m", 0.0, 50.0, "within this of the stem")
_n("roots.hydrotropism_per_m", "1/m", 0.0, 100.0, "turning to wetter soil")
_n("roots.direction_noise_per_sqrt_m", "1/sqrt(m)", 0.0, 10.0, "random wander")
_n("roots.probe_radius", "m", 0.01, 5.0, "how far a root tip senses")
_n("roots.branch_angle_deg", "deg", 0.0, 180.0, "lateral root insertion angle")
_n("roots.apical_dominance", "-", 0.0, 1.0, "split for roots: at a primordium")
_n("roots.apical_control", "-", 0.0, 1.0, "split for roots: at a branch")
_n("roots.primordium_weight", "-", 0.0, 100.0, "a primordium's weight in the split")
_n("roots.lateral_threshold", "segments", 0.0, 1000.0, "a primordium forms a root with this much resource")
_i("roots.primordium_lifespan", "years", 0, 1000, "and dies unused after this")
_n("roots.collar_primordium_weight", "-", 0.0, 100.0, "the same at the root collar")
_n("roots.collar_lateral_threshold", "segments", 0.0, 1000.0, "the same at the root collar")
_i("roots.collar_primordium_lifespan", "years", 0, 1000, "the same at the root collar")
_n("roots.collar_divergence_deg", "deg", 0.0, 360.0, "angle between collar roots")
_n("roots.collar_apical_control", "-", 0.0, 1.0, "split along the taproot")
_n("roots.depletion_coefficient", "m3/m", 0.0, 10.0, "water availability falls with root density")
_n("roots.depletion_radius", "m", 0.0, 5.0, "over this radius around a root")
_i("roots.absorbing_years", "years", 0, 1000, "younger roots carry the fine-root cloud")
_n("roots.uptake_conductance_per_m", "kg/s/MPa/m", 0.0, 1.0, "uptake per metre of absorbing root")
_b("roots.fine_root_uptake.enabled", "water enters through the fine roots the tree pays for")
_n("roots.fine_root_uptake.specific_root_length_m_per_g", "m/g", 1.0, 1000.0, "fine-root length per mass")
_n("roots.fine_root_uptake.root_conductance_per_leaf_area", "kg/m2/s/MPa", 1e-7, 1.0, "root-system conductance per leaf area")
_n("roots.fine_root_uptake.fine_root_per_leaf_mass", "g/g", 0.0, 20.0, "fine root per leaf mass of the same trees")
_n("roots.fine_root_uptake.leaf_mass_per_area_g_m2", "g/m2", 5.0, 500.0, "their leaf mass per area")
_n("roots.tip_survival_availability", "-", 0.0, 1.0, "root tips die below this water availability")
_n("roots.shed_availability", "-", 0.0, 1.0, "lateral roots are shed below this")
_n("roots.field_margin", "m", 0.0, 20.0, "soil grid's margin")
_n("roots.zrt_radius_per_dbh", "m/m", 0.0, 50.0, "zone of rapid taper reaches this far, per DBH")
_n("roots.zrt_fade_fraction", "-", 0.01, 5.0, "fade length, per zone radius")
_n("roots.avoid_clearance_m", "m", 0.0, 2.0, "growing roots keep this clear; null = off", nullable=True)
_n("roots.avoid_zone_radius_m", "m", 0.0, 50.0, "within this of the stem")
_n("roots.avoid_weight", "-", 0.0, 100.0, "strength of that push")
_n("roots.max_turn_deg_per_segment", "deg", 0.0, 180.0, "most a root turns per segment; null = no limit", nullable=True)
_b("roots.trim_taproot", "the taproot decays below the deepest main lateral")
# -------------------------------------------------------------------- anchorage
_n("anchorage.plate_root_diameter", "m", 1e-3, 1.0, "a main root counts up to where it thins below this")
_n("anchorage.plate_structural_share", "-", 0.0, 1.0, "share of main-root area the plate is measured from")
_c("anchorage.plate_radius_rule", ("taper_zone_end", "structural_roots_2cm", "median_all_main_roots_2cm", "structural_roots_quarter_base"), "plate radius rule")
_n("anchorage.tensile_strength_1mm_mpa", "MPa", 0.1, 500.0, "root tensile strength at 1 mm")
_n("anchorage.tensile_strength_exponent", "-", 0.0, 5.0, "its fall with diameter")
_n("anchorage.root_strength_mobilised", "-", 0.0, 1.0, "share of root strength in use when the plate turns")
_n("anchorage.h_dbh2_coefficient_knm_per_m3", "kN m/m3", 0.0, 1000.0, "pulling resistance per H DBH^2")
_l("anchorage.h_dbh2_coefficient_range", "kN m/m3", 0.0, 1000.0, "its range", length=(2, 2))
_n("anchorage.critical_moment_per_stem_volume_knm_per_m3", "kN m/m3", 1.0, 2000.0, "critical turning moment per stem volume")
_n("anchorage.rooting_depth_radius_m", "m", 0.0, 50.0, "deepest root within this of the stem")
_n("anchorage.reference_rooting_depth_m", "m", 0.01, 20.0, "plate depth of the pulled trees")
_n("anchorage.depth_factor_min", "-", 0.0, 10.0, "depth factor's limits")
_n("anchorage.depth_factor_max", "-", 0.0, 10.0, "depth factor's limits")
_n("anchorage.root_tension_share", "-", 0.0, 1.0, "share of the moment from windward roots")
# ------------------------------------------------------ field_layer_competition
_b("field_layer_competition.enabled", "clear-cut field layer competes for light")
_n("field_layer_competition.max_height_m", "m", 0.0, 10.0, "mature sward height")
_n("field_layer_competition.max_lai", "-", 0.0, 20.0, "mature sward LAI")
_n("field_layer_competition.extinction", "-", 0.0, 3.0, "its light extinction")
_n("field_layer_competition.years_to_mature", "years", 0.01, 100.0, "years to the mature sward")
# ------------------------------------------------------------------ germination
_b("germination.enabled", "seedling emergence from seed reserves")
_n("germination.seed_dry_mass_mg", "mg", 0.001, 1e5, "seed dry mass")
_n("germination.cotyledon_area_cm2", "cm2", 0.0, 100.0, "cotyledon area; no code reads it", optional=True)
_n("germination.germination_respiration_fraction", "-", 0.0, 1.0, "share of reserves respired")
_n("germination.hypocotyl_height_m", "m", 0.0, 1.0, "height at emergence")
_n("germination.initial_taproot_depth_m", "m", 0.0, 2.0, "taproot at emergence; no code reads it", optional=True)
_n("germination.first_year_effective_leaves", "leaves", 0.0, 100.0, "first year's leaf equivalent")
_n("germination.juvenile_scale_bh_m", "m", 0.01, 50.0, "juvenile leaves reach adult size at this height")
_n("germination.min_juvenile_scale", "-", 0.0, 1.0, "smallest juvenile leaf scale")
# ----------------------------------------------------------- soil_water_balance
_b("soil_water_balance.enabled", "season soil-water bucket")
_n("soil_water_balance.awc_mm", "mm", 1.0, 2000.0, "extractable water at field capacity")
_n("soil_water_balance.rew_threshold", "-", 0.0, 1.0, "below this share transpiration falls")
_n("soil_water_balance.transpiration_lai_slope", "per LAI", 0.0, 2.0, "transpiration over PET per LAI")
_n("soil_water_balance.transpiration_ratio_max", "-", 0.0, 2.0, "its limit")
_l("soil_water_balance.precipitation_mm", "mm", 0.0, 3000.0, "May-September rain", length=(5, 5))
_l("soil_water_balance.pet_mm", "mm", 0.0, 3000.0, "May-September PET", length=(5, 5))
_l("soil_water_balance.dry_year_precipitation_mm", "mm", 0.0, 3000.0, "the drought year's rain", length=(5, 5))
_b("soil_water_balance.drought_scenario", "use the drought year's rain")
# ---------------------------------------------------------------- speed (ways of running; reports/speed_research.md)
_b("speed.compiled_carbon", "carbon solve compiled; same bits")
_b("speed.quick_solve", "carbon solve in fewer evaluations; same bits on the runs tested")
_b("speed.compiled_mechanics", "bending compiled; same bits")
_b("speed.quick_levels", "the order of passes from a compiled count; same bits")
_b("speed.light_layers", "light grids held layer first; same bits")
_b("speed.keep_soil_grids", "soil grids kept between years; same bits")
_b("speed.light_rows", "light by frequency rows, scipy's ffts; new rounding")
_b("speed.drop_dead", "lean runs drop dead nodes; same yearly stats on the runs tested")
_i("speed.light_every", "years", 1, 10, "years one light field lasts; lossy")
_l("speed.sky_elevations_deg", "deg", 0.0, 90.0, "fewer sky directions; lossy", nullable=True)
_i("speed.sky_azimuth_count", "-", 1, 64, "fewer sky directions; lossy", nullable=True)
_n("speed.sun_hour_step", "h", 0.25, 6.0, "fewer sun directions; lossy", nullable=True)

BY_PATH = {f.path: f for f in FIELDS}
SWITCH_KINDS = ("switch", "choice", "text")


def flatten(raw, prefix: str = "") -> dict:
    """Dotted path -> value; a list is one value, as in reports/parameter_audit.csv."""
    out = {}
    for k, v in (raw or {}).items():
        path = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, path + "."))
        else:
            out[path] = v
    return out


def is_setting(path: str, value) -> bool:
    """A switch or choice of the model, with no source to check: not counted among the values."""
    f = BY_PATH.get(path)
    if f is not None and (f.kind in SWITCH_KINDS or path.endswith(".stage")):
        return True
    return f is None and (isinstance(value, (bool, str)) or value is None)


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _check_field(f: Field, v, errors: list) -> None:
    where = f"{f.path}: {v!r}"
    unit = f" {f.unit}" if f.unit and f.unit != "-" else ""
    if v is None:
        if not f.nullable:
            errors.append(f"{where}: needs a value ({f.what})")
        return
    if f.kind == "switch":
        if not isinstance(v, bool):
            errors.append(f"{where}: must be true or false")
    elif f.kind == "choice":
        if v not in f.choices:
            errors.append(f"{where}: must be one of {list(f.choices)}")
    elif f.kind == "text":
        if not isinstance(v, str) or not v.strip():
            errors.append(f"{where}: must be text")
    elif f.kind in ("number", "integer"):
        if not _number(v) or (f.kind == "integer" and float(v) != int(v)):
            errors.append(f"{where}: must be {'a whole number' if f.kind == 'integer' else 'a number'}{unit}")
        elif not f.lo <= float(v) <= f.hi:
            errors.append(f"{where}: outside {f.lo:g} to {f.hi:g}{unit} ({f.what})")
    elif f.kind == "numbers":
        if not isinstance(v, list) or not all(_number(x) for x in v):
            errors.append(f"{where}: must be a list of numbers{unit}")
            return
        if f.length and not f.length[0] <= len(v) <= f.length[1]:
            errors.append(f"{where}: must have {f.length[0]} to {f.length[1]} values")
        for x in v:
            if not f.lo <= float(x) <= f.hi:
                errors.append(f"{where}: {x} is outside {f.lo:g} to {f.hi:g}{unit} ({f.what})")
    elif f.kind == "table":
        if not isinstance(v, list) or not v:
            errors.append(f"{where}: must be a list of rows with {list(f.columns)}")
            return
        for row in v:
            missing = [c for c in f.columns if not isinstance(row, dict) or c not in row]
            if missing:
                errors.append(f"{f.path}: a row lacks {missing}")


def _cross_checks(flat: dict, errors: list) -> None:
    """Values that must agree with each other."""

    def order(lo, hi, why):
        a, b = flat.get(lo), flat.get(hi)
        if _number(a) and _number(b) and float(a) > float(b):
            errors.append(f"{lo} ({a}) must not be above {hi} ({b}): {why}")

    order("hydraulics.psi_stomata_closed", "hydraulics.psi_stomata_open", "stomata shut after they start closing")
    order("hydraulics.psi_turgor_loss", "hydraulics.psi_full_expansion", "expansion stops after it starts falling")
    order("resource.root_share_min", "resource.root_share_max", "the range of the root share")
    order("reference.height.site_index_low", "reference.height.site_index_high", "the range of site index")
    order("anchorage.depth_factor_min", "anchorage.depth_factor_max", "the depth factor's limits")
    order("pipe_model.wind_load.streamlining_min_wind_m_s", "pipe_model.wind_load.streamlining_max_wind_m_s", "streamlining's range")
    order("bud_fate.short_shoot_survival_light", "bud_fate.short_shoot_light", "a short shoot must be able to live where it forms")
    for path in ("reference.dbh.open_grown_band_cm", "anchorage.h_dbh2_coefficient_range", "damage.snow.load_range_kg_m2"):
        v = flat.get(path)
        if isinstance(v, list) and len(v) == 2 and _number(v[0]) and _number(v[1]) and v[0] > v[1]:
            errors.append(f"{path}: {v} must run low to high")
    years, weights = flat.get("plot.germination_years"), flat.get("plot.germination_weights")
    if isinstance(years, list) and isinstance(weights, list):
        if len(years) != len(weights):
            errors.append("plot.germination_years and plot.germination_weights must be the same length")
        elif abs(sum(weights) - 1.0) > 1e-6:
            errors.append(f"plot.germination_weights must add up to 1, not {sum(weights)}")
    thinning = flat.get("stand.thinning")
    if isinstance(thinning, list) and all(isinstance(r, dict) and "stems_per_ha" in r and "from_height_m" in r for r in thinning):
        rows = sorted(thinning, key=lambda r: float(r["from_height_m"]))
        if not rows or float(rows[0]["from_height_m"]) != 0.0:
            errors.append("stand.thinning must start at from_height_m 0: the first row sets the plot's starting density")
        if any(float(a["stems_per_ha"]) < float(b["stems_per_ha"]) for a, b in zip(rows, rows[1:])):
            errors.append("stand.thinning: stems_per_ha must not rise with height")
    events = flat.get("leader_damage.events")
    if isinstance(events, list):
        for e in events:
            if isinstance(e, dict) and _number(e.get("probability_per_year")) and not 0.0 <= float(e["probability_per_year"]) <= 1.0:
                errors.append(f"leader_damage.events: {e.get('name')}: probability_per_year must be 0 to 1")


@dataclass
class Report:
    errors: list
    warnings: list

    @property
    def ok(self) -> bool:
        return not self.errors


def validate(raw: dict) -> Report:
    """Check a species' values.  Errors mean it can't be trusted to run; warnings don't."""
    errors, warnings = [], []
    if not isinstance(raw, dict):
        return Report(["the file holds no settings"], [])
    flat = flatten(raw)
    missing_blocks = {b for b in OPTIONAL_BLOCKS if b not in raw}
    for b in sorted(missing_blocks):
        warnings.append(f"no {b} block: {OPTIONAL_BLOCKS[b]}")
    for f in FIELDS:
        if f.path.split(".")[0] in missing_blocks:
            continue
        if f.path not in flat:
            if not f.optional and not any(p.startswith(f.path + ".") for p in flat):
                errors.append(f"{f.path}: missing ({f.what}{', ' + f.unit if f.unit and f.unit != '-' else ''})")
            continue
        _check_field(f, flat[f.path], errors)
    for path in flat:
        if path not in BY_PATH:
            warnings.append(f"{path}: not in treegen/species_schema.py, so unchecked")
    _cross_checks(flat, errors)
    return Report(errors, warnings)


def validate_file(path) -> Report:
    with open(path, encoding="utf-8") as f:
        return validate(yaml.safe_load(f))


# -- where each value came from ------------------------------------------------
@dataclass
class Label:
    status: str          # sourced | TUNED | VERIFY
    note: str = ""       # the source, what it was tuned against, or why it's unchecked
    checked: str = ""    # sourced values: "page" if someone read the page and it supports the value
    changed: bool = False   # the value isn't what it was when labelled, so the label no longer speaks for it


KEY_LINE = re.compile(r"^(\s*)([A-Za-z_]\w*):(?:\s+(.*))?$")


def tuned_in_comments(text: str) -> dict:
    """Values the species file itself labels TUNED, in capitals, in the comment on the value's
    line or the comment lines directly above it (reset_brief.md, rule 1)."""
    stack, pending, out = [], [], {}
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith("#"):
            pending.append(s.lstrip("#").strip())
            continue
        if not s or s.startswith("- "):
            if not s:
                pending = []
            continue
        m = KEY_LINE.match(raw)
        if not m:
            continue
        indent, key, rest = len(m.group(1)), m.group(2), m.group(3) or ""
        while stack and stack[-1][0] >= indent:
            stack.pop()
        comment = " ".join(pending) + (" " + rest.split(" # ", 1)[1] if " # " in rest else "")
        if re.search(r"\bTUNED\b", comment):
            out[".".join([k for _, k in stack] + [key])] = comment.strip()
        stack.append((indent, key))
        pending = []
    return out


def read_labels(raw: dict, species_text: str = "", labels: dict | None = None) -> dict:
    """Dotted path -> Label for every value that isn't a switch.  A TUNED comment in the species
    file comes first, because it's the rule for anyone tuning a value; then the labels file; a
    value with neither is VERIFY.  A value that changed since its label was written is VERIFY
    too, until someone looks at it."""
    labels = labels or {}
    tuned = tuned_in_comments(species_text) if species_text else {}
    out = {}
    for path, value in flatten(raw).items():
        if path.startswith("species.") or is_setting(path, value):
            continue
        if path in tuned:
            out[path] = Label("TUNED", tuned[path])
            continue
        e = labels.get(path)
        if not e:
            out[path] = Label("VERIFY", "no label")
        elif "value" in e and e["value"] != value:
            out[path] = Label("VERIFY", f"labelled {e.get('status')} at {e['value']!r}; now {value!r}", changed=True)
        else:
            note = e.get("source") or e.get("against") or e.get("note") or ""
            out[path] = Label(e.get("status", "VERIFY"), note, e.get("checked", ""))
    return out


def check_labels(raw: dict, labels: dict) -> list:
    """What's wrong with a labels file itself: a value with no such key, an unknown status, a
    TUNED value not saying what it was tuned against, a sourced value naming no source."""
    flat = flatten(raw)
    problems = []
    for path, e in (labels or {}).items():
        if path not in flat:
            problems.append(f"{path}: no such value in the species file")
            continue
        status = (e or {}).get("status")
        if status not in STATUSES:
            problems.append(f"{path}: status must be one of {list(STATUSES)}, not {status!r}")
        elif status == "TUNED" and not e.get("against"):
            problems.append(f"{path}: TUNED must say what it was tuned against")
        elif status == "sourced" and not e.get("source"):
            problems.append(f"{path}: sourced must name the source")
    return problems


def load_labels(path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
