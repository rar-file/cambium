"""Old age, wind and snow: what can happen to a tree in a year.

Off by default (``damage.enabled`` and a switch for each part in the species
file).  The first half of this file is plain functions: they take a tree's state
and the year's weather and return what happens, and change nothing.  The second
half (``state_from_model``, ``apply_top_break``, ``tree_year``, ``plot_year``) is
the only part that touches a GrowthModel or a Plot, so growth.py and plot.py each
need one call.

What each part rests on (full sources and labels: reference/<species>/labels.yaml):

* Old age.  Elfving 2010 pp. 67-68: ln AMAX = b0 + b1 SIS + b2 ln n, and the share
  dead of ageing by age A is p = 1 / (1 + exp(a - b A / AMAX)).  A counts rings at
  breast height.
* Wind.  Whether a storm hits a tree: the logistic model of Kitenberga et al. 2021
  Tables 1-2, 14,749 birches in the Latvian forest inventory, per 5-year period.
  Its coefficients are per standard deviation about the mean: at the mean age its
  Fig. 2 reads 0.65 %, which is the inverse logit of the intercept -5.03.
* How a hit tree fails.  Whichever gives first, the stem (MOR x pi D^3 / 32,
  Nykanen et al. 1997 p. 198) or the roots (the critical turning moment of
  roots.py, Krisans et al. 2022), with scatter, set to give Kitenberga's 31-35 %
  uprooted on her mean tree.  So slender trees snap and stout ones uproot, as
  Zubizarreta-Gerendiain et al. 2012 Table 3 found in Scots pine (too few birches).
* Where it snaps.  Kitenberga Table 3 for the mean, her Fig. 4 for the spread.  A
  stem broken below the living crown dies; broken within it, it lives on with a
  new leader (Nykanen p. 195).
* Snow.  The load sits on the crown's projected area, at most the tree's share of the
  ground; the real stem's Rayleigh buckling factor (as tools/snow_buckling.py) amplifies
  the off-centre moment, compared with the stem's strength.  Slender stems and off-centre
  crowns go first (Nykanen pp. 201-202).  An overloaded stem mostly bends: 93.7 % of
  damaged birches did in Donis et al. 2024.
* Pit and mound.  The plate from RootSystem.anchorage tips over about its leeward
  edge.  The mound holds the soil the pit lost.

The storm and snow years come from this file's own stream of random numbers, so
turning damage on doesn't change any other draw in the model.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np

G = 9.81
# one stream per tree or plot, apart from the model's others
RNG_TAG = 86011
WEATHER_TAG = 86012


# -- the year's weather --------------------------------------------------------
@dataclass(frozen=True)
class Weather:
    storm: bool = False
    wind_from_deg: float = 0.0        # the direction the wind comes from; the tree falls the opposite way
    snow_load_kg_m2: float = 0.0      # on the crown's projected area; 0 = no damaging snowfall


def draw_weather(rng, dp) -> Weather:
    """One year's storm and damaging snowfall.  Every part draws whether it's on or
    not, so switching one part leaves the other's years as they were."""
    u_storm, az, u_snow, u_load = rng.random(), rng.normal(), rng.random(), rng.random()
    w, s = dp.wind, dp.snow
    storm = bool(w.enabled) and u_storm < 1.0 / float(w.storm_return_years)
    wind_from = (float(w.wind_from_deg) + az * float(w.wind_from_sd_deg)) % 360.0
    load = 0.0
    if bool(s.enabled) and u_snow < 1.0 / float(s.return_years):
        lo, hi = (float(v) for v in s.load_range_kg_m2)
        load = lo + u_load * (hi - lo)
    return Weather(storm, wind_from, load)


# -- a tree's state ------------------------------------------------------------
@dataclass
class TreeState:
    age: int
    height_m: float
    dbh_cm: float | None                # wood only, as GrowthModel.dbh_m gives it
    crown_base_m: float | None = None
    crown_width_m: float = 0.0
    stems_per_ha: float = 0.0
    basal_area_m2_ha: float = 0.0
    prior_damage: bool = False
    crown_offset_m: float = 0.0         # crown's centre of leaves from the stem base, sideways
    crown_wood_kg: float = 0.0          # fresh wood of the crown, without the stem
    anchorage: dict | None = None       # RootSystem.anchorage's numbers, when known
    x_m: float = 0.0                    # stem base, in plot coordinates
    y_m: float = 0.0
    storm_exposure: float = 1.0         # this tree's share of a storm's damage, against the stand's mean of 1
    stem_z: np.ndarray | None = None    # the real stem, when known: heights
    stem_r: np.ndarray | None = None    # and radii


@dataclass
class Event:
    cause: str                          # old age | wind snap | wind uproot | snow snap | snow uproot | snow bend
    fatal: bool
    snap_height_m: float | None = None
    fall_azimuth_deg: float | None = None
    plate: dict | None = None           # root plate, pit and mound (uprooting only)
    root_moment_knm: float | None = None    # for a tree that failed: what held it at the roots
    stem_moment_knm: float | None = None    # and at the stem

    def as_dict(self) -> dict:
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in asdict(self).items() if v is not None}


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x)) if x > -700.0 else 0.0


def _over_bark_cm(state: TreeState, dp) -> float:
    return float(state.dbh_cm) * float(dp.dbh_over_bark_factor)


# -- old age -------------------------------------------------------------------
def max_age_years(oa) -> float:
    """Elfving 2010 Eq. F1, at the number of sample trees the report uses for its figure."""
    return math.exp(float(oa.amax_b0) + float(oa.amax_b1) * float(oa.site_index_sis_m) + float(oa.amax_b2) * math.log(float(oa.amax_n)))


def share_dead_of_age(age_bh: float, oa) -> float:
    """Share of trees dead of ageing by breast-height age age_bh."""
    return 1.0 / (1.0 + math.exp(float(oa.ageing_a) - float(oa.ageing_b) * max(age_bh, 0.0) / max_age_years(oa)))


def old_age_hazard(age: float, oa) -> float:
    """Chance that a tree alive at this total age dies of ageing within the year."""
    a = float(age) - float(oa.years_to_breast_height)
    p0, p1 = share_dead_of_age(a, oa), share_dead_of_age(a + 1.0, oa)
    return (p1 - p0) / max(1.0 - p0, 1e-12)


# -- wind ----------------------------------------------------------------------
def _per_sd(value: float, c) -> float:
    """A coefficient of Kitenberga's Table 1, on a value kept inside her Table 2's range."""
    lo, hi = (float(v) for v in c.range)
    return float(c.per_sd) * (min(max(value, lo), hi) - float(c.mean)) / float(c.sd)


def wind_damage_probability(state: TreeState, dp) -> float:
    """Chance that wind snaps or uproots this tree within Kitenberga's 5-year period.
    Trees below w.min_dbh_cm are outside her data and get none."""
    w = dp.wind
    if not state.dbh_cm or _over_bark_cm(state, dp) < float(w.min_dbh_cm):
        return 0.0
    x = float(w.intercept) + float(w.population_offset) + float(w.site_effect)
    x += _per_sd(float(state.age), w.age)
    x += _per_sd(float(state.stems_per_ha), w.stems_per_ha)
    x += _per_sd(float(state.basal_area_m2_ha), w.basal_area_m2_ha)
    x += _per_sd(float(state.height_m) / _over_bark_cm(state, dp), w.slenderness)
    if state.prior_damage:
        x += float(w.prior_damage)
    return _logistic(x)


def storm_hit_probability(state: TreeState, dp) -> float:
    """Chance that a storm year's storm hits this tree: the same damage per year, all
    of it falling in the storm years."""
    w = dp.wind
    per_year = 1.0 - (1.0 - wind_damage_probability(state, dp)) ** (1.0 / float(w.period_years))
    return min(1.0, per_year * float(w.storm_return_years) * float(state.storm_exposure))


def stem_breaking_moment_knm(dbh_cm: float, mor_mpa: float) -> float:
    """Bending moment that breaks a round stem of this diameter at breast height."""
    d = float(dbh_cm) / 100.0
    return math.pi / 32.0 * d ** 3 * float(mor_mpa) * 1e6 / 1e3


def uprooting_moment_knm(state: TreeState, wind_from_deg: float, sp) -> float:
    """The critical turning moment for this wind direction, from the tree's roots when
    known; without them Krisans' regression on stem volume alone."""
    a = state.anchorage or {}
    ctm = a.get("critical_turning_moment") or {}
    # unrounded when the roots give them (anchorage.moments_unrounded), else as printed
    by_dir = ctm.get("by_wind_dir_knm_unrounded") or ctm.get("by_wind_dir_knm")
    if by_dir:
        key = min(by_dir, key=lambda d: abs((float(d) - wind_from_deg + 180.0) % 360.0 - 180.0))
        return float(by_dir[key])
    d = float(state.dbh_cm) / 100.0
    volume = float(sp.damage.stem_form_factor) * math.pi / 4.0 * d * d * float(state.height_m)
    return float(sp.anchorage.critical_moment_per_stem_volume_knm_per_m3) * volume


def uproot_probability(state: TreeState, wind_from_deg: float, sp) -> float:
    """Chance that a failing tree goes at the roots rather than the stem."""
    f = sp.damage.failure
    ratio = uprooting_moment_knm(state, wind_from_deg, sp) / stem_breaking_moment_knm(state.dbh_cm, f.mor_green_mpa)
    return _logistic(-(math.log(max(ratio, 1e-9)) - float(f.even_odds_log_ratio)) / float(f.spread))


def snap_height_m(state: TreeState, dp, rng) -> float:
    """Where the stem breaks: Kitenberga's mean, the spread of her Fig. 4."""
    s = dp.snap
    hd = float(state.height_m) / _over_bark_cm(state, dp)
    mean = float(s.intercept) + float(s.slenderness) * hd + (float(s.prior_damage) if state.prior_damage else 0.0)
    mean = min(max(mean, 0.02), 0.98)
    c = float(s.beta_concentration)
    return float(state.height_m) * float(rng.beta(mean * c, (1.0 - mean) * c))


# -- snow ----------------------------------------------------------------------
def rayleigh_terms(z: np.ndarray, r: np.ndarray, height: float, crown_base, mp) -> tuple[float, float, float]:
    """The buckling factor's sum for a stem of radius r at heights z, as tools/snow_buckling.py: the factor is
    stiffness / (stem's weight term + crown load in kg x load's term per kg).  The load is spread evenly over the crown."""
    H = float(height)
    cb = min(float(crown_base if crown_base is not None else 0.5 * H), 0.95 * H)
    dz = z[1] - z[0]
    stem = float(mp.wood_density) * np.pi * r * r * dz
    above = np.cumsum(stem[::-1])[::-1]
    share = np.clip((H - np.maximum(z, cb)) / max(H - cb, 1e-6), 0.0, 1.0)
    w1 = math.pi / (2.0 * H) * np.sin(math.pi * z / (2.0 * H))
    w2 = (math.pi / (2.0 * H)) ** 2 * np.cos(math.pi * z / (2.0 * H))
    ei = float(mp.youngs_modulus_wood) * np.pi * r ** 4 / 4.0
    return float(np.trapezoid(ei * w2 * w2, z)), float(np.trapezoid(G * above * w1 * w1, z)), float(np.trapezoid(G * share * w1 * w1, z))


def snow_loading(state: TreeState, load_kg_m2: float, sp) -> tuple[float, float]:
    """(moment over the stem's strength at breast height, Rayleigh buckling factor) under this
    snow load, on the tree's real stem.  Without one its radius falls as (H - z)^p from its DBH
    to nothing at its top, with p from the stem form factor f (volume = f pi/4 DBH^2 H gives
    p = (1/f - 1)/2); under its own weight that's 1.3 to 2.2 times weaker than the grown stems of
    logged plots.  Below a buckling factor of 1 the stem can't stand the load at all."""
    dp = sp.damage
    H = float(state.height_m)
    area = math.pi / 4.0 * float(state.crown_width_m) ** 2
    if state.stems_per_ha > 0.0:
        area = min(area, 1e4 / float(state.stems_per_ha))      # no tree holds more snow than falls on its share of the ground
    m_load = load_kg_m2 * float(dp.snow.crown_catch_fraction) * area + float(state.crown_wood_kg)
    z = np.linspace(0.0, H, 121)
    if state.stem_z is not None:
        r = np.interp(z, state.stem_z, state.stem_r, right=0.0)
    else:
        p = (1.0 / float(dp.stem_form_factor) - 1.0) / 2.0
        r = 0.5 * float(state.dbh_cm) / 100.0 * (np.maximum(H - z, 0.0) / max(H - 1.3, 0.1)) ** p
    stiff, stem_weight, load_weight = rayleigh_terms(z, r, H, state.crown_base_m, sp.mechanics)
    buckling = float(stiff / max(stem_weight + m_load * load_weight, 1e-30))
    if buckling <= 1.0:
        return math.inf, buckling
    lever = float(state.crown_offset_m) + float(dp.snow.lever_fraction) * H
    moment_knm = G * m_load * lever / (1.0 - 1.0 / buckling) / 1e3
    return moment_knm / stem_breaking_moment_knm(state.dbh_cm, dp.failure.mor_green_mpa), buckling


def snow_overload_probability(state: TreeState, load_kg_m2: float, sp) -> float:
    """Chance that this load overloads this stem: its moment reaches the stem's strength, or the stem buckles.
    Overloaded isn't broken: see assess_year."""
    ratio = snow_loading(state, load_kg_m2, sp)[0]
    return 1.0 if ratio == math.inf else _logistic(math.log(max(ratio, 1e-12)) / float(sp.damage.snow.spread))


# -- pit and mound -------------------------------------------------------------
def root_plate(state: TreeState, fall_azimuth_deg: float, sp) -> dict:
    """The plate and what's left in the ground when this tree uproots.  The plate is a
    disc that tips about its leeward edge (the hinge).  The pit is a paraboloid in the
    plate's place, so with RootSystem.anchorage's plate of half a cylinder's volume its
    depth is the plate's.  The mound, the same volume of soil, lies past the hinge."""
    dp = sp.damage.uproot
    a = state.anchorage or {}
    radius = float(a.get("plate_radius_m") or 0.0)
    depth = float(a.get("plate_depth_m") or 0.0)
    if radius <= 0.0 or depth <= 0.0:
        # no root numbers: the taper zone's radius and the pulled trees' plate depth
        radius = float(sp.roots.zrt_radius_per_dbh) * float(state.dbh_cm or 0.0) / 100.0
        depth = float(sp.anchorage.reference_rooting_depth_m)
    az = math.radians(fall_azimuth_deg)
    ux, uy = math.cos(az), math.sin(az)
    volume = math.pi * radius * radius * depth / 2.0
    mound_radius = radius * float(dp.mound_radius_factor)
    mound_at = radius * (1.0 + float(dp.mound_distance_factor))
    return {
        "x_m": round(state.x_m, 3), "y_m": round(state.y_m, 3), "fall_azimuth_deg": round(fall_azimuth_deg, 1),
        "plate_radius_m": round(radius, 3), "plate_depth_m": round(depth, 3),
        "plate_soil_mass_kg": round(float(a.get("plate_soil_mass_kg") or 0.0), 1),
        "hinge_x_m": round(state.x_m + radius * ux, 3), "hinge_y_m": round(state.y_m + radius * uy, 3),
        "pit_depth_m": round(depth, 3), "pit_volume_m3": round(volume, 4),
        "mound_x_m": round(state.x_m + mound_at * ux, 3), "mound_y_m": round(state.y_m + mound_at * uy, 3),
        "mound_radius_m": round(mound_radius, 3),
        "mound_height_m": round(2.0 * volume / (math.pi * mound_radius * mound_radius), 3),
    }


def ground_relief(xy: np.ndarray, plates: list, ages: list, half_life_years: float) -> np.ndarray:
    """Height (m, down in pits) the given plates add to the ground at points xy, each plate
    ages[i] years old, the relief fading with half_life_years.  For the ground mesh."""
    xy = np.asarray(xy, float)
    out = np.zeros(len(xy))
    for p, age in zip(plates, ages):
        fade = 0.5 ** (float(age) / float(half_life_years))
        pit = np.hypot(xy[:, 0] - p["x_m"], xy[:, 1] - p["y_m"]) / p["plate_radius_m"]
        mound = np.hypot(xy[:, 0] - p["mound_x_m"], xy[:, 1] - p["mound_y_m"]) / p["mound_radius_m"]
        out += fade * (p["mound_height_m"] * np.maximum(1.0 - mound * mound, 0.0) - p["pit_depth_m"] * np.maximum(1.0 - pit * pit, 0.0))
    return out


def expose_mineral_soil(regen, plate: dict) -> None:
    """Bare the seedbed of a plot's regeneration grid on the pit and the mound."""
    if regen is None:
        return
    for cx, cy, r in ((plate["x_m"], plate["y_m"], plate["plate_radius_m"]),
                      (plate["mound_x_m"], plate["mound_y_m"], plate["mound_radius_m"])):
        d = np.hypot(((regen.cx - cx + 0.5 * regen.L) % regen.L) - 0.5 * regen.L,
                     ((regen.cy - cy + 0.5 * regen.L) % regen.L) - 0.5 * regen.L)
        regen.mineral[d <= r + 0.5 * regen.cs] = 1.0


# -- the year's verdict --------------------------------------------------------
def leaf_share_above(state: TreeState, z: float) -> float:
    """Without the tree itself: its leaves spread evenly over its crown."""
    H = float(state.height_m)
    cb = float(state.crown_base_m if state.crown_base_m is not None else 0.5 * H)
    return min(max((H - z) / max(H - cb, 1e-6), 0.0), 1.0)


def _failure(state: TreeState, weather: Weather, sp, rng, kind: str, share_above=None) -> Event:
    dp = sp.damage
    fall = (weather.wind_from_deg + 180.0) % 360.0
    roots = uprooting_moment_knm(state, weather.wind_from_deg, sp)
    stem = stem_breaking_moment_knm(state.dbh_cm, dp.failure.mor_green_mpa)
    if rng.random() < uproot_probability(state, weather.wind_from_deg, sp):
        return Event(f"{kind} uproot", True, None, fall, root_plate(state, fall, sp), roots, stem)
    z = snap_height_m(state, dp, rng)
    taken = share_above(z) if share_above is not None else leaf_share_above(state, z)
    below_crown = state.crown_base_m is None or z < float(state.crown_base_m)
    return Event(f"{kind} snap", below_crown or 1.0 - taken < float(dp.snap.min_leaves_left), z, fall, None, roots, stem)


def assess_year(state: TreeState, weather: Weather, sp, rng, load_anchorage=None, share_above=None) -> Event | None:
    """What happens to this tree this year, or None.  Winter's snow first, then the storm,
    then age; a tree takes at most one blow a year.  load_anchorage: called for the root
    numbers only when a tree fails, because working them out takes time.  share_above: the
    share of the tree's leaves a break at a height would take, when the tree itself is at hand."""
    dp = sp.damage
    if not bool(dp.enabled):
        return None

    def fail(kind):
        if state.anchorage is None and load_anchorage is not None:
            state.anchorage = load_anchorage()
        return _failure(state, weather, sp, rng, kind, share_above)

    if state.dbh_cm and weather.snow_load_kg_m2 > 0.0 and rng.random() < snow_overload_probability(state, weather.snow_load_kg_m2, sp):
        # an overloaded stem bends and few break: 93.7 % of damaged birches bent in Donis 2024
        if rng.random() >= float(dp.snow.break_share):
            return Event("snow bend", False)
        return fail("snow")
    if weather.storm and state.dbh_cm and rng.random() < storm_hit_probability(state, dp):
        return fail("wind")
    if bool(dp.old_age.enabled) and rng.random() < old_age_hazard(state.age, dp.old_age):
        return Event("old age", True)
    return None


# -- connecting to the model ---------------------------------------------------
def anchorage_of(model) -> dict | None:
    """RootSystem.anchorage for this tree.  The stem volume is the larger of the trunk
    chain's and the form factor's: on 3 of the 20 saved stand trees at 60 (seeds 8, 9,
    20) the chain's is a third or less of the others' at the same size."""
    if model.roots is None:
        return None
    sp, s, T = model.sp, model.stats[-1], model.tree
    trunk = T.trunk_chain(model.leader_axes)
    chain = float((np.pi * T.radius[trunk[1:]] ** 2 * T.length[trunk[1:]]).sum())
    d = float(s["dbh_cm"] or 0.0) / 100.0
    volume = max(chain, float(sp.damage.stem_form_factor) * math.pi / 4.0 * d * d * float(s["height_m"]))
    return model.roots.anchorage(sp.anchorage, s["height_m"], s["dbh_cm"], volume * float(sp.mechanics.wood_density), volume)


def state_from_model(model, stems_per_ha: float | None = None, basal_area_m2_ha: float | None = None,
                     prior_damage: bool = False, xy=(0.0, 0.0)) -> TreeState:
    """A tree's state after its last season.  Alone in a stand or in the open, the stem
    count and basal area come from the tree itself."""
    s, T = model.stats[-1], model.tree
    n = T.n
    alive = T.death[:n] < 0
    trunk = T.trunk_chain(model.leader_axes)
    on_trunk = np.zeros(n, bool)
    on_trunk[trunk] = True
    side = alive & ~on_trunk
    wood = float((np.pi * T.radius[:n][side] ** 2 * T.length[:n][side]).sum()) * float(model.sp.mechanics.wood_density)
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    total = float(leaves.sum())
    offset = 0.0
    if total > 0.0:
        c = (T.pos[:n, :2] * leaves[:, None]).sum(0) / total
        offset = float(np.hypot(c[0] - T.pos[0, 0], c[1] - T.pos[0, 1]))
    h, dbh = float(s["height_m"]), s["dbh_cm"]
    if stems_per_ha is None:
        # (the stand's schedule, read as every other place reads it: GrowthModel._schedule_height)
        stems_per_ha = float(model.stems_per_ha(model._schedule_height(h, measured=True))) if model.stand else 0.0
    if basal_area_m2_ha is None:
        over_bark = float(dbh or 0.0) * float(model.sp.damage.dbh_over_bark_factor)
        basal_area_m2_ha = stems_per_ha * math.pi / 4.0 * (over_bark / 100.0) ** 2
    z, r = T.pos[trunk, 2].astype(float), T.radius[trunk].astype(float)
    o = np.argsort(z, kind="stable")
    return TreeState(int(model.year), h, dbh, s.get("crown_base_height_m"), float(s.get("crown_width_m") or 0.0),
                     float(stems_per_ha), float(basal_area_m2_ha), bool(prior_damage), offset, wood,
                     x_m=float(xy[0]), y_m=float(xy[1]), stem_z=z[o], stem_r=r[o])


def _top_above(model, z_break: float):
    """(first node off, the node below it, everything that goes), or None if the break misses the living stem."""
    T = model.tree
    n = T.n
    trunk = T.trunk_chain(model.leader_axes)
    above = np.nonzero(T.pos[trunk, 2] >= z_break)[0]
    if not above.size or above[0] < 2:
        return None
    k, base = int(trunk[above[0]]), int(trunk[above[0] - 1])
    kill = np.zeros(n, bool)
    kill[k] = True
    for seg, _, _ in T.levels(T.death[:n] < 0)[1:]:
        kill[seg] |= kill[T.parent[seg]]
    return k, base, kill


def top_break_share(model, z_break: float) -> float:
    """The share of this tree's leaves a break at this height would take."""
    cut = _top_above(model, z_break)
    if cut is None:
        return 1.0 if z_break < float(model.stats[-1]["height_m"]) else 0.0
    T = model.tree
    leaves = np.where(T.death[:T.n] < 0, T.leaves[:T.n], 0.0).astype(float)
    return float(leaves[cut[2]].sum() / max(leaves.sum(), 1e-9))


def apply_top_break(model, z_break: float, t: int):
    """Take the stem off above z_break: everything above is dead from season t, and the
    uppermost living lateral buds or limbs below the wound become leaders, as after
    browsing (GrowthModel._leader_damage).  False if the break misses the living stem;
    otherwise what it took: the share of the tree's leaves, and the height left."""
    from .growth import LAT_DEAD, LAT_DORMANT, LAT_SPUR

    T = model.tree
    n = T.n
    alive = T.death[:n] < 0
    cut = _top_above(model, z_break)
    if cut is None:
        return False
    k, base, kill = cut
    dead = np.nonzero(kill)[0]
    leaves = np.where(alive, T.leaves[:n], 0.0).astype(float)
    took = {"leaf_share": round(float(leaves[kill].sum() / max(leaves.sum(), 1e-9)), 4),
            "height_left_m": round(float(T.pos[:n][alive & ~kill, 2].max()), 3)}
    T.death[dead] = t
    T.term[dead] = 0
    for nd in dead[T.lat[dead] == LAT_SPUR].tolist():
        model._end_spur(nd, t)
    if T.main_child[base] == k:
        T.main_child[base] = -1
    if T.lat_child[base] == k:
        T.lat_child[base] = -1
        T.lat[base] = LAT_DEAD
    T.relay.pop(base, None)
    T.term[base] = 0
    # the leaders: as many as after browsing, from the uppermost living side shoots
    want = int(getattr(getattr(model.sp, "leader_damage", None), "replacement_leaders", 1))
    j, cand = base, []
    while j > 0 and len(cand) < want:
        if (T.lat[j] in (LAT_DORMANT, LAT_SPUR) and not T.no_axil[j]) or (T.lat_child[j] >= 0 and T.death[T.lat_child[j]] < 0):
            cand.append(j)
        j = int(T.parent[j])
    for c in cand:
        lc = int(T.lat_child[c])
        if lc >= 0 and T.death[lc] < 0:
            model.leader_axes.add(int(T.axis[lc]))
            T.relay.setdefault(base, lc)
        else:
            if T.lat[c] == LAT_SPUR:
                model._end_spur(c, t)
            T.lat[c] = LAT_DORMANT
            T.lat_age[c] = 0
            model._relay_buds[c] = base
    return took


def _rng(holder, seed: int):
    if getattr(holder, "_damage_rng", None) is None:
        holder._damage_rng = np.random.default_rng([int(seed), RNG_TAG])
    return holder._damage_rng


def _weather_rng(holder, seed: int):
    """The years' weather has its own stream, so a seed has the same storms and snowfalls however
    many trees stand or fall: two runs on one seed can be compared, storm for storm."""
    if getattr(holder, "_weather_rng_state", None) is None:
        holder._weather_rng_state = np.random.default_rng([int(seed), WEATHER_TAG])
    return holder._weather_rng_state


def _is_on(sp) -> bool:
    dp = getattr(sp, "damage", None)
    return dp is not None and bool(dp.enabled)


def _number(x, digits: int = 4):
    return None if x is None else float(f"{float(x):.{digits}g}")


def _record(year: int, k, event: Event, state: TreeState, factor: float) -> dict:
    """One line of the log: what happened, to what size of tree."""
    d = float(state.dbh_cm or 0.0)
    row = {"year": year, "cause": event.cause, "fatal": event.fatal, "uprooted": event.plate is not None,
           "age": state.age, "height_m": _number(state.height_m), "dbh_cm": _number(d),
           "hd_over_bark": _number(state.height_m / (d * factor)) if d > 0.0 else None,
           "crown_base_m": _number(state.crown_base_m), "stems_per_ha": _number(state.stems_per_ha),
           "basal_area_m2_ha": _number(state.basal_area_m2_ha), "prior_damage": state.prior_damage,
           "snap_height_m": _number(event.snap_height_m), "fall_azimuth_deg": _number(event.fall_azimuth_deg),
           "root_moment_knm": _number(event.root_moment_knm), "stem_moment_knm": _number(event.stem_moment_knm)}
    if k is not None:
        row["tree"] = k
    if event.plate is not None:
        row["plate"] = event.plate
    return row


def _snow_tree_row(k, state: TreeState, event, sp) -> list:
    """For retuning the snow without a new run: the size of this tree in a snow year, and the parts of its buckling sum."""
    H = float(state.height_m)
    grid = np.linspace(0.0, H, 121)
    real = np.interp(grid, state.stem_z, state.stem_r, right=0.0)
    return [k, state.age, _number(H), _number(state.dbh_cm), _number(state.crown_base_m), _number(state.crown_width_m),
            _number(state.crown_offset_m), _number(state.crown_wood_kg),
            *[_number(x) for x in rayleigh_terms(grid, real, H, state.crown_base_m, sp.mechanics)],
            event.cause if event is not None else None]


def tree_year(model, t: int) -> Event | None:
    """One winter for a tree grown on its own (cli.py).  A top that breaks is taken off; a
    fatal blow is logged but the tree carries on, because a single run has no stand to
    take it out of: a plot is where trees die (plot_year).  In a plot this does nothing."""
    if not _is_on(model.sp) or hasattr(model, "_plot_spacing") or not model.stats:
        return None
    rng = _rng(model, model.seed)
    weather = draw_weather(_weather_rng(model, model.seed), model.sp.damage)
    log = model.__dict__.setdefault("damage_log", [])
    any_blow = weather.storm or weather.snow_load_kg_m2 > 0.0
    if any_blow:
        state = state_from_model(model, prior_damage=any(e.get("took") for e in log))
    else:
        state = TreeState(int(model.year), float(model.stats[-1]["height_m"]), model.stats[-1]["dbh_cm"])   # only age can act
    event = assess_year(state, weather, model.sp, rng, load_anchorage=lambda: anchorage_of(model),
                        share_above=lambda z: top_break_share(model, z))
    if event is not None:
        row = _record(t, None, event, state, float(model.sp.damage.dbh_over_bark_factor))
        if event.snap_height_m is not None and not event.fatal:
            row["took"] = apply_top_break(model, event.snap_height_m, t)
        log.append(row)
    return event


def storm_exposure(plot, trees: list, rng, dp, factor: float) -> dict:
    """Where a storm falls in a plot: most of its damage in a few round patches, so it opens gaps instead of
    picking single trees all over.  Tree -> how much more or less than the stand's mean it's exposed.  The stand's
    expected damage is unchanged: exposure averages 1 over the trees wind can take."""
    w = dp.wind
    radius, area_share, damage_share = float(w.gap_radius_m), float(w.gap_area_share), float(w.gap_damage_share)
    lx, ly = plot._sides() if hasattr(plot, "_sides") else (math.sqrt(plot.area), math.sqrt(plot.area))
    n = max(1, int(round(area_share * lx * ly / (math.pi * radius * radius))))
    cx = rng.uniform(-0.5 * lx, 0.5 * lx, n)
    cy = rng.uniform(-0.5 * ly, 0.5 * ly, n)
    at_risk = [k for k in trees if float(plot.trees[k].stats[-1]["dbh_cm"] or 0.0) * factor >= float(w.min_dbh_cm)]
    inside = set()
    for k in at_risk:
        dx, dy = np.abs(plot.info[k]["x"] - cx), np.abs(plot.info[k]["y"] - cy)
        if (np.hypot(np.minimum(dx, lx - dx), np.minimum(dy, ly - dy)) <= radius).any():
            inside.add(k)
    out = {"centres": [[round(float(x), 2), round(float(y), 2)] for x, y in zip(cx, cy)]}
    if not at_risk or not inside or len(inside) == len(at_risk):
        return out
    share = len(inside) / len(at_risk)
    for k in at_risk:
        out[k] = damage_share / share if k in inside else (1.0 - damage_share) / (1.0 - share)
    return out


def plot_year(plot, active: list) -> list:
    """One year of damage in a plot, after the trees have grown.  Stems killed go through
    Plot._finish with the cause; a broken top is taken off the tree; a root plate bares the
    seedbed.  plot.damage_log, which plot.json saves, holds every year's weather and every
    event; a tree's own part also goes in plot.info[k]["damage"]."""
    if not _is_on(plot.species):
        return []
    dp = plot.species.damage
    rng = _rng(plot, plot.seed)
    weather = draw_weather(_weather_rng(plot, plot.seed), dp)
    factor = float(dp.dbh_over_bark_factor)
    ha = plot.area / 1e4
    log = plot.__dict__.setdefault("damage_log", {"years": [], "events": [], "snow_trees": {}})
    # the canopy layer, as her 'overstory': her densities run up to 11,520 stems/ha, so small trees count,
    # but seedlings under the canopy don't shelter it
    rows = [plot.trees[k].stats[-1] for k in plot.alive]
    tall = max((float(r["height_m"]) for r in rows), default=0.0)
    d_ob = np.array([float(r["dbh_cm"] or 0.0) * factor for r in rows if float(r["height_m"]) >= float(dp.wind.canopy_height_share) * tall]) / 100.0
    stems, basal = len(d_ob) / ha, float((np.pi / 4.0 * d_ob * d_ob).sum()) / ha
    events = []
    trees = [k for k in active if k in plot.alive]
    year = {"year": plot.year, "storm": weather.storm, "wind_from_deg": _number(weather.wind_from_deg), "snow_load_kg_m2": _number(weather.snow_load_kg_m2),
            "trees": len(trees), "stems_per_ha": _number(stems), "basal_area_m2_ha": _number(basal), "wind_at_risk": 0, "wind_expected": 0.0,
            "stems_over_min": sum(float(plot.trees[k].stats[-1]["dbh_cm"] or 0.0) * factor >= float(dp.wind.min_dbh_cm) for k in trees),
            "snow_at_risk": 0, "snow_expected": 0.0, "events": 0, "fatal": 0}
    detail = bool(getattr(dp, "log_snow_trees", False)) and weather.snow_load_kg_m2 > 0.0
    any_blow = weather.storm or weather.snow_load_kg_m2 > 0.0
    exposure = storm_exposure(plot, trees, rng, dp, factor) if weather.storm else {}
    if exposure:
        year["gap_centres"] = exposure.pop("centres")
    for k in trees:
        m = plot.trees[k]
        xy = (plot.info[k]["x"], plot.info[k]["y"])
        if any_blow:
            state = state_from_model(m, stems, basal, bool(plot.info[k].get("prior_damage")), xy)
            state.storm_exposure = exposure.get(k, 1.0)
        else:
            state = TreeState(int(m.year), float(m.stats[-1]["height_m"]), m.stats[-1]["dbh_cm"])    # only age can act
        if weather.storm and state.dbh_cm:
            p = storm_hit_probability(state, dp)
            year["wind_at_risk"] += p > 0.0
            year["wind_expected"] += p
        if weather.snow_load_kg_m2 > 0.0 and state.dbh_cm:
            year["snow_at_risk"] += 1
            year["snow_expected"] += snow_overload_probability(state, weather.snow_load_kg_m2, m.sp)
        event = assess_year(state, weather, m.sp, rng, load_anchorage=lambda: anchorage_of(m),
                            share_above=lambda z: top_break_share(m, z))
        if detail and state.dbh_cm:
            log["snow_trees"].setdefault(str(plot.year), []).append(_snow_tree_row(k, state, event, m.sp))
        if event is None:
            continue
        record = _record(plot.year, k, event, state, factor)
        year["events"] += 1
        year["fatal"] += bool(event.fatal)
        if event.plate is not None:
            expose_mineral_soil(getattr(plot, "regen", None), event.plate)
        if event.fatal:
            record["took"] = {"leaf_share": 1.0, "leaf_area_m2": m.stats[-1].get("leaf_area_m2")}
            plot._finish(k, event.cause)
        elif event.snap_height_m is not None:
            # a broken stem is what her 'prior damage' means; a bent one that recovers isn't
            plot.info[k]["prior_damage"] = True
            record["took"] = apply_top_break(m, event.snap_height_m, plot.year + 1)
        plot.info[k].setdefault("damage", []).append(record)
        log["events"].append(record)
        events.append((k, record))
    year["wind_expected"], year["snow_expected"] = _number(year["wind_expected"]), _number(year["snow_expected"])
    year["wind_at_risk"] = int(year["wind_at_risk"])
    log["years"].append(year)
    return events
