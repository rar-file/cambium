# Milestone M2: Carbon production

Protocol hash at the start of the campaign: `0e58497`; now `85f32d1`. Date: 2026-11-06. Machine for every verdict: the node. PC runs are exploring only, each against the PC's own baseline, and they're marked. Code: the baseline at `68782d9`; the default's alpha sweep, the diagnosis runs, apical steps and the 0.15 test at `f45928e`; both proposed corrections, the grid and fresh seeds at `3f3d687`. No file in `treegen/` or `cli.py` has changed since `3f3d687`, and `species/` only in comments. Outputs: `out/bench/ensemble/` unless a path says otherwise. **Nothing in M2 was adopted, so the model's defaults are as they were at M1's close.**

## 1. Summary

- Alpha, the carbon a lit leaf fixes in a year, stays 4.8 with VERIFY. No direct source in what I could read, and no value run fits height and leaf area (LAI) together on stand trees, with or without the two proposed corrections, wood shade off and the leaf charge.
- Plots at alpha 3.0 with both pass height and LAI, depending on the draw, at twice or more the source's stems/ha, and fail light. Trees and plots disagree, so by my rule I picked nothing. As you asked, I report that as how carbon is shared out, M3's work; the cause isn't settled.
- Wood shade off and the leaf charge wait on you (Q21, Q23), and so do apical values (Q22; I recommend not picking). Fertility and season aren't built, because nothing tried keeps the curve's shape (Q25).
- M1's baseline was a low draw for LAI: 3.09, 3.27 at 50, 60 on its 20 seeds, 3.23, 3.37 on 40. Its verdicts stand, and the corrections' gains are smaller than I first read.
- Light fails at default and with both; only a test value passes it. Plots barely thin: about 1,660 stems/ha and 63-67 m2/ha over bark at 60 with both, against Repola's top of 32.3.

## 2. Scorecard

From `tools/scorecard.py --ensemble`, unchanged, at `targets-approved` as moved in this milestone (`bb3048c`). No row differs from the previous tag. Ages 20-60. **The first two are the model as it stands,** the same runs and verdicts as M1. The second two show both proposed corrections, not adopted: `--set` on the same seeds, at alpha 4.8. Seeds 21-40 are in section 3.

**Stand trees, 20 seeds, default:**

Targets: reference/targets.yaml at targets-approved (commit bb3048c). Ensemble: out/bench/ensemble/base_trees, 20 runs.

| Target | Ensemble mean | SD | Seeds | Target Range / Value | Status | Share of seeds inside | Source | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 50)` | 3.094 | 0.407 | 20 | [3.60, 5.40] | **FAIL** | 10 % | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 3.274 | 0.370 | 20 | [3.60, 5.40] | **FAIL** | 20 % | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | 30.140 | 4.221 | 20 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +15.3 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | 27.505 | 2.727 | 20 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +12.7 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | 0.575 | 0.134 | 20 | >= 0.5 | **INFO** | 75 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | 0.673 | 0.103 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | 0.706 | 0.099 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.726 | 0.097 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.699 | 0.133 | 20 | >= 0.5 | **INFO** | 95 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | 0.575 | 0.134 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | 0.673 | 0.103 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | 0.706 | 0.099 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.726 | 0.097 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.699 | 0.133 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | N/A | 0 | 880 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | N/A | 0 | 420 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 20)` | 14.888 | 0.483 | 20 | 8.05-13.61 m (SI20-SI26, bh age 14.0-15.0) | **FAIL** | 5 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 30)` | 19.728 | 0.708 | 20 | 12.66-19.24 m (SI20-SI26, bh age 24.0-25.0) | **FAIL** | 20 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 40)` | 23.068 | 0.748 | 20 | 16.16-22.79 m (SI20-SI26, bh age 34.0-35.0) | **FAIL** | 35 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 50)` | 25.286 | 0.621 | 20 | 18.76-25.12 m (SI20-SI26, bh age 44.0-45.0) | **FAIL** | 30 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 27.069 | 0.741 | 20 | 20.72-26.73 m (SI20-SI26, bh age 54.0-55.0) | **FAIL** | 30 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Repola (2008) | scorecard.py computes no model value for this target |
| `tree_allometry.wood_basic_density` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | N/A | 0 | [0.15, 0.35] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | N/A | 0 | [1.20, 1.80] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.field_layer` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | needs a single-seedling or plot run |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

The verdict is the ensemble mean against the band. The band shown is the first seed's where it depends on the seed.
INFO: information only (scoring: info in targets.yaml), never PASS/FAIL.

**Plots, 5 seeds, default:**

Targets: reference/targets.yaml at targets-approved (commit bb3048c). Ensemble: out/bench/ensemble/base_plots, 5 runs.

| Target | Ensemble mean | SD | Seeds | Target Range / Value | Status | Share of seeds inside | Source | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | 2.972 | 0.390 | 5 | [2.50, 4.50] | **PASS** | 80 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1746 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | 3.768 | 0.152 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1728 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | 3.807 | 0.045 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1566 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | 3.769 | 0.031 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1476 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | 3.761 | 0.016 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1440 stems/ha |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 50)` | 3.769 | 0.031 | 5 | [3.60, 5.40] | **PASS** | 100 % | Hagemeier & Leuschner (2019) | stand LAI at 1476 stems/ha |
| `stand_canopy.lai_hagemeier (age 60)` | 3.761 | 0.016 | 5 | [3.60, 5.40] | **PASS** | 100 % | Hagemeier & Leuschner (2019) | stand LAI at 1440 stems/ha |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | 22.316 | 0.103 | 5 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +7.5 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | 22.286 | 0.103 | 5 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +7.5 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | 0.724 | 0.028 | 5 | [0.30, 0.45] | **FAIL** | 0 % | Niemistö (1995, Paper 1); Repola (2008) | mean crown ratio of 96 live trees |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 30 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 40 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 50 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 60 outside age_years [11, 22] |
| `stand_canopy.stand_density (age 45)` | 1566.000 | 52.479 | 5 | 880 stems/ha | **INFO** | 0 % | Hagemeier & Leuschner (2019, Forests 10(3):265) |  |
| `stand_canopy.stand_density (age 67)` | N/A | N/A | 0 | 420 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | age 67 not in plot output |
| `stand_canopy.dominant_height_invariance` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs runs at several densities |
| `tree_allometry.site_index_curves (age 20)` | 15.429 | 0.324 | 5 | 8.05-13.61 m (SI20-SI26, bh age 14.0-15.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 15.10 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 30)` | 21.776 | 0.253 | 5 | 12.66-19.24 m (SI20-SI26, bh age 24.0-25.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 21.53 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 40)` | 26.165 | 0.356 | 5 | 16.16-22.79 m (SI20-SI26, bh age 34.0-35.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 25.73 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 50)` | 28.878 | 0.387 | 5 | 18.76-25.12 m (SI20-SI26, bh age 44.0-45.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 28.16 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 60)` | 30.587 | 0.296 | 5 | 20.72-26.73 m (SI20-SI26, bh age 54.0-55.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 29.56 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.bark_thickness` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `tree_allometry.wood_basic_density` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | N/A | 0 | [0.15, 0.35] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | N/A | 0 | [1.20, 1.80] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.field_layer` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

The verdict is the ensemble mean against the band. The band shown is the first seed's where it depends on the seed.
INFO: information only (scoring: info in targets.yaml), never PASS/FAIL.

**Stand trees, 20 seeds, wood shade off and leaf charge on, not adopted:**

Targets: reference/targets.yaml at targets-approved (commit bb3048c). Ensemble: out/bench/ensemble/m2_cc, 20 runs.

| Target | Ensemble mean | SD | Seeds | Target Range / Value | Status | Share of seeds inside | Source | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | N/A | 0 | [2.50, 4.50] | **NOT APPLICABLE** | N/A | Uri et al. (2012); Varik et al. (2015) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 50)` | 3.681 | 0.314 | 20 | [3.60, 5.40] | **PASS** | 60 % | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 3.852 | 0.313 | 20 | [3.60, 5.40] | **PASS** | 80 % | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | 27.855 | 2.227 | 20 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +13.1 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | 26.352 | 2.546 | 20 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +11.6 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | 0.645 | 0.134 | 20 | >= 0.5 | **INFO** | 90 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | 0.730 | 0.102 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | 0.770 | 0.089 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.778 | 0.094 | 20 | >= 0.5 | **INFO** | 100 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.752 | 0.114 | 20 | >= 0.5 | **INFO** | 95 % | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | 0.645 | 0.134 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | 0.730 | 0.102 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | 0.770 | 0.089 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.778 | 0.094 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.752 | 0.114 | 20 | [0.29, 0.96] (mean 0.58) | **INFO** | 100 % | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | N/A | 0 | 880 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | N/A | 0 | 420 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 20)` | 14.479 | 0.605 | 20 | 8.05-13.61 m (SI20-SI26, bh age 14.0-15.0) | **FAIL** | 10 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 30)` | 19.246 | 1.082 | 20 | 12.66-19.24 m (SI20-SI26, bh age 24.0-25.0) | **FAIL** | 40 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 40)` | 22.706 | 0.916 | 20 | 16.16-22.79 m (SI20-SI26, bh age 34.0-35.0) | **PASS** | 40 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 50)` | 25.071 | 0.657 | 20 | 18.76-25.12 m (SI20-SI26, bh age 44.0-45.0) | **PASS** | 55 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 27.024 | 0.769 | 20 | 20.72-26.73 m (SI20-SI26, bh age 54.0-55.0) | **FAIL** | 35 % | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Repola (2008) | scorecard.py computes no model value for this target |
| `tree_allometry.wood_basic_density` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | N/A | 0 | [0.15, 0.35] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | N/A | 0 | [1.20, 1.80] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.field_layer` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | needs a single-seedling or plot run |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

The verdict is the ensemble mean against the band. The band shown is the first seed's where it depends on the seed.
INFO: information only (scoring: info in targets.yaml), never PASS/FAIL.

**Plots, 5 seeds, wood shade off and leaf charge on, not adopted:**

Targets: reference/targets.yaml at targets-approved (commit bb3048c). Ensemble: out/bench/ensemble/m2_plots_cc, 5 runs.

| Target | Ensemble mean | SD | Seeds | Target Range / Value | Status | Share of seeds inside | Source | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | 3.440 | 0.106 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1746 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | 3.672 | 0.360 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1728 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | 4.171 | 0.030 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1674 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | 4.098 | 0.026 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1674 stems/ha |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | 4.060 | 0.040 | 5 | [2.50, 4.50] | **PASS** | 100 % | Uri et al. (2012); Varik et al. (2015) | stand LAI at 1674 stems/ha |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | N/A | 0 | [3.60, 5.40] | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 67] |
| `stand_canopy.lai_hagemeier (age 50)` | 4.098 | 0.026 | 5 | [3.60, 5.40] | **PASS** | 100 % | Hagemeier & Leuschner (2019) | stand LAI at 1674 stems/ha |
| `stand_canopy.lai_hagemeier (age 60)` | 4.060 | 0.040 | 5 | [3.60, 5.40] | **PASS** | 100 % | Hagemeier & Leuschner (2019) | stand LAI at 1674 stems/ha |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | N/A | 0 | [6.40, 19.80] % | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 67] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | 24.308 | 0.725 | 5 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +9.5 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | 24.790 | 0.594 | 5 | [6.40, 19.80] % | **FAIL** | 0 % | Hagemeier & Leuschner (2019b) | +10.0 points from the paper's median of 14.8 %; diffuse light at 1.0-2.0 m, this year |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | N/A | N/A | 0 | >= 0.5 | **NOT APPLICABLE** | N/A | Hynynen et al. (2010) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | N/A | N/A | 0 | [0.29, 0.96] (mean 0.58) | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | 0.738 | 0.031 | 5 | [0.30, 0.45] | **FAIL** | 0 % | Niemistö (1995, Paper 1); Repola (2008) | mean crown ratio of 96 live trees |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 30 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 40 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 50 outside age_years [11, 22] |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | N/A | 0 | [0.30, 0.45] | **NOT APPLICABLE** | N/A | Niemistö (1995, Paper 1); Repola (2008) | age 60 outside age_years [11, 22] |
| `stand_canopy.stand_density (age 45)` | 1659.600 | 34.624 | 5 | 880 stems/ha | **INFO** | 0 % | Hagemeier & Leuschner (2019, Forests 10(3):265) |  |
| `stand_canopy.stand_density (age 67)` | N/A | N/A | 0 | 420 stems/ha | **NOT APPLICABLE** | N/A | Hagemeier & Leuschner (2019, Forests 10(3):265) | age 67 not in plot output |
| `stand_canopy.dominant_height_invariance` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs runs at several densities |
| `tree_allometry.site_index_curves (age 20)` | 15.353 | 0.152 | 5 | 8.05-13.61 m (SI20-SI26, bh age 14.0-15.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 15.09 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 30)` | 21.531 | 0.130 | 5 | 12.66-19.24 m (SI20-SI26, bh age 24.0-25.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 21.14 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 40)` | 26.135 | 0.201 | 5 | 16.16-22.79 m (SI20-SI26, bh age 34.0-35.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 25.52 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 50)` | 28.727 | 0.237 | 5 | 18.76-25.12 m (SI20-SI26, bh age 44.0-45.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 27.72 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.site_index_curves (age 60)` | 30.324 | 0.218 | 5 | 20.72-26.73 m (SI20-SI26, bh age 54.0-55.0) | **FAIL** | 0 % | Eriksson, Johansson & Kiviste (1997) | top height on a Naslund curve at the mean diameter of 5.56 of 5.56 trees on the plot; those trees' mean height 28.51 m; fewer than 10 such trees, so this is noisy |
| `tree_allometry.bark_thickness` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | N/A | 0 | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | N/A | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Repola (2008) | mode natural not in ['managed'] |
| `tree_allometry.wood_basic_density` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | N/A | 0 | See yaml | **NOT SCORED** | N/A | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | N/A | 0 | [0.15, 0.35] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | N/A | 0 | [1.20, 1.80] m | **NOT APPLICABLE** | N/A | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.field_layer` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | field_layer_competition.enabled was False, needs True |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | N/A | 0 | See yaml | **NOT APPLICABLE** | N/A | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

The verdict is the ensemble mean against the band. The band shown is the first seed's where it depends on the seed.
INFO: information only (scoring: info in targets.yaml), never PASS/FAIL.

## 3. Task items

### M2a. Replace or justify alpha

**Not done:** it stays 4.8, VERIFY, not labelled calibrated, because nothing fits. It comes back after M3 changes how carbon is shared, and after M4 for the Liziniewicz ladder. Alpha is what each leaf fixes (`treegen/growth.py:853`). No direct source in what I could read, though Uddling 2005 and Riikonen 2005 are unread (`reports/research_notes.md`; Q27). So it goes by the calibration route:

| What the calibration rule asks | Where it stands |
|---|---|
| Only for a parameter with no direct source | As far as I could read |
| Bounds from published ranges | Not met. About 2.7-6.8, a subagent's arithmetic from leaf and stand routes, not a published range |
| Several independent patterns at once | Not met. Height and LAI are linked, and the brief's three fit patterns are below |
| Validate on data not used | A look only, below |
| Label it calibrated | Not done, because nothing fits |

**Stand trees, 20 seeds, node. F: height outside its band. \*: depends on the draw (height within 0.2 m of an edge, LAI within 0.12 of 3.60). The lines: height inside its band at 20-60, LAI at least 3.60 at 50 and 60. Default's LAI is under 3.60 on all these rows (`m2_alpha_report.txt`, `m2_cc_alpha_trees.txt`):**

| Alpha | Default: height at 50, 60 (m) | Default: LAI at 50, 60 | Default: light at 50, 60 (%) | Both proposed corrections: height at 20, 30, 40, 50, 60 (m) | Height SD at 60 | LAI at 50, 60 | LAI SD at 50 | Light at 50, 60 (%) | Seeds meeting every line |
|---|---|---|---|---|---|---|---|---|---|
| 3.0 | | | | 10.99, 14.04, 15.80 F, 17.14 F, 18.26 F | 1.43 | 1.52, 1.53 | 0.66 | 59.5, 61.1 | 0 % |
| 3.25 | | | | 11.38, 14.28, 16.36\*, 17.94 F, 19.30 F | 1.56 | 1.84, 1.97 | 0.53 | 53.6, 51.6 | 0 % |
| 3.5 | 19.85, 21.56 | 2.21, 2.42 | 43.1, 39.5 | 11.94, 15.13, 18.05, 20.22, 22.01 | 1.45 | 2.48, 2.95 | 0.40 | 42.6, 35.9 | 0 % |
| 4.0 | 21.91, 23.42 | 2.81, 3.02 | 33.9, 31.1 | 13.12, 16.76, 20.02, 22.21, 23.84 | 1.21 | 3.02, 3.47 | 0.47 | 35.1, 30.0 | 5 % |
| 4.4 | 23.45, 25.16 | 3.09, 3.31 | 30.7, 27.9 | 13.95 F, 18.14, 21.36, 23.68, 25.41 | 1.14 | 3.37, 3.69\* | 0.49 | 31.3, 27.6 | 0 % |
| 4.6 | 24.29, 25.94 | 3.13, 3.32 | 29.6, 27.6 | 14.41 F, 18.88, 22.20, 24.54, 26.35 | 0.69 | 3.58\*, 3.75 | 0.31 | 28.6, 27.2 | 0 % |
| 4.8, now | 25.29\* F, 27.07 F | 3.09, 3.27 | 30.1, 27.5 | 14.48 F, 19.25\* F, 22.71\*, 25.07\*, 27.02 F | 0.77 | 3.68\*, 3.85 | 0.31 | 27.9, 26.4 | 0 % |
| 5.0 | 25.50 F, 27.38 F | 3.33, 3.42 | 27.7, 26.6 | 14.52 F, 19.57 F, 23.22 F, 25.60 F, 27.48 F | 0.94 | 3.70\*, 3.79 | 0.31 | 27.8, 26.9 | 0 % |
| 5.8 | 27.62 F, 29.61 F | 3.46, 3.53\* | 27.3, 25.7 | | | | | | |
| 6.8 | 29.12 F, 31.33 F | 3.42, 3.52\* | 26.7, 25.9 | | | | | | |

**Plots, 5 seeds, node, by row 52: top height inside its band and LAI 3.6-4.5, at both 50 and 60. Means; SD between plots is in the files (`m2_plots_table.txt`, `m2_cc_alpha_plots.txt`). The source's stands hold 880 and 420 stems/ha, so these aren't like for like (Q13):**

| Alpha | Setting | Top height at 50, 60 (m) | LAI at 50, 60 | Light at 50, 60 (%) | Basal area over bark at 50, 60 (m2/ha) | Stems/ha at 45 | Plots meeting every line | Fits? |
|---|---|---|---|---|---|---|---|---|
| 3.0 | Default | 23.19 +- 0.66, 24.81 +- 0.80 | 3.25 +- 0.04 F, 3.32 +- 0.05 F | 27.7 +- 0.4, 26.8 +- 0.5 | | 1,782 | 0 % | no |
| | Both | 23.17 +- 0.83, 24.76 +- 1.04 | 3.61 +- 0.04, 3.69 +- 0.05 | 27.9 +- 0.3, 27.2 +- 0.6 | 30.4-32.5, 35.0-37.5 | 1,782 | 60 % | yes, depending on the draw |
| 3.5 | Default | 26.07 +- 0.66 F, 27.61 +- 0.71 F | 3.52 +- 0.03 F, 3.55 +- 0.05 F | 25.2 +- 0.3, 24.8 +- 0.4 | | 1,768 | 0 % | no |
| | Both | 25.27 +- 0.47 F, 26.79 +- 0.51 F | 3.89 +- 0.04, 3.88 +- 0.04 | 25.5 +- 0.3, 25.4 +- 0.5 | 39.5-42.3, 45-48 | 1,768 | 40 % | no, depending on the draw: 0.14, 0.05 m over |
| 4.0 | Default | 27.27 +- 0.49 F, 28.81 +- 0.39 F | 3.69 +- 0.04, 3.66 +- 0.04 | 23.6 +- 0.5, 23.5 +- 0.4 | | 1,714 | 0 % | no |
| 4.4 | Default | 28.29 +- 0.40 F, 29.94 +- 0.40 F | 3.72 +- 0.05, 3.69 +- 0.06 | 22.9 +- 0.5, 22.9 +- 0.2 | | 1,645 | 0 % | no |
| 4.8, now | Default | 28.88 +- 0.39 F, 30.59 +- 0.30 F | 3.77 +- 0.03, 3.76 +- 0.02 | 22.3 +- 0.1, 22.3 +- 0.1 | 51-55, 58-62 | 1,566 | 0 % | no |
| | Both | 28.73 +- 0.24 F, 30.32 +- 0.22 F | 4.10 +- 0.03, 4.06 +- 0.04 | 24.3 +- 0.7, 24.8 +- 0.6 | 54.7-58.7, 62.6-67.3 | 1,660 | 0 % | no |

- **Trees and plots disagree, so I picked nothing** (row 66(b), written before the runs, and row 76). LAI needs about 4.8 on trees and passes at 3.0 on plots, a gap of 1.8; height at 60 allows up to 4.6 on trees, 1.6; height at 20 up to 4.0, 1.0. Plots' own edge isn't located, because 3.25 wasn't run there. Plots at 3.0 with both are the first plot set to pass height and LAI together, depending on the draw, and stems barely thin, so it may be the right numbers for the wrong reason.
- **Why they disagree isn't established.** Here are the heights (`m2_linked.txt`):

| Alpha, both | Age | Plots: top height on the curve (m) | Plots: thickest 6 of each plot, about 100/ha, mean (m) | Plots: all trees, mean (m) | Stand tree (m) |
|---|---|---|---|---|---|
| 3.0 | 50 | 23.17 | 23.61 | 18.33 | 17.14 |
| | 60 | 24.76 | 25.07 | 19.22 | 18.26 |
| 3.5 | 50 | 25.27 | 25.04 | 19.00 | 20.22 |
| | 60 | 26.79 | 26.38 | 19.86 | 22.01 |
| 4.8 | 50 | 28.73 | 27.69 | 21.64 | 25.07 |
| | 60 | 30.32 | 29.05 | 22.48 | 27.02 |

The thickest trees run 2.0-6.8 m over a stand tree. The average plot tree is about 1 m over at 3.0, and under at 3.5 and 4.8. So part of it may be selection, the thickest 5-6 of about 95 trees against one typical tree, and part crowding. Not separated. The target file's own rule, from an unopened paper, says dominant height doesn't change across 1,000-2,500 stems/ha (`dominant_height_invariance`); stand trees at 450 are outside that. M4.

**The brief's fit patterns:**

| Pattern | Result |
|---|---|
| Eriksson curve shape across site indices | **Alpha spreads the wrong way.** The curves' ratio, SI 32 to SI 22, falls with age: 2.11 at 20, 1.78 at 30, 1.50 at 50, 1.44 at 60. SI 32 and ages under 20 are outside the target's band, so this is for shape only. Alpha 6.8 to 3.5 rises: 1.28, 1.43, 1.47, 1.45 (`m2_shape.txt`). So alpha can't stand in for site quality |
| Liziniewicz 2022 MAI ladder | **Not run.** It's the output of their simulation, planted and thinned on their schedule, and it needs stand volume with thinnings counted. It moves to M4, on plots (row 81) |
| Repola stem wood at the model's own size | Below |

**Wood against Repola's equations at the same size, PC, 20 seeds (`out/bench/wood/wood_table_alpha.txt`). Taking Repola's d as over bark is a reading; the bark here is `tools/bark.py`'s. With Repola's own sample's bark, about 0.9 cm at 16.5 cm, Repola's stem wood at 60 is 390 and 407 kg, not 413 and 430. Model wood has no bark, and Repola's branches include it. For a look, not a verdict. Ilomaki's 80-96 % stem share is from 30-year-old stands, from the abstract, and varies with slenderness:**

| Setting | Age | Stem wood, model / Repola (kg) | Branch wood, model / Repola (kg) | Stem share (%) |
|---|---|---|---|---|
| Default, 4.8 | 30 | 136 / 150 | 20 / 27 | 85.8 |
| | 50 | 326 / 339 | 55 / 61 | 85.7 |
| | 60 | 421 / 413 | 74 / 73 | 85.4 |
| Both, 4.8 | 30 | 132 / 149 | 20 / 29 | 85.7 |
| | 50 | 348 / 351 | 62 / 67 | 85.2 |
| | 60 | 456 / 430 | 85 / 80 | 84.5 |
| Both, 4.0 | 30 | 85 / 104 | 14 / 21 | 85.5 |
| | 50 | 234 / 262 | 43 / 54 | 84.8 |
| | 60 | 314 / 327 | 63 / 67 | 84.0 |
| Both, 3.0 | 30 | 33 / 46 | 12 / 10 | 71.2 |
| | 50 | 86 / 112 | 36 / 25 | 67.6 |
| | 60 | 119 / 149 | 55 / 34 | 66.5 |

At alpha 4.8, stem wood at 60 is 2-8 % over at default and 6-12 % with both, by which bark, branches 1-13 % and 7-19 %, and both are under at 30. So on this check the default isn't far off. It goes to M3b with the crown work.

**Validation, kept out of every fit (`tools/m2_validation.py`, `m2_validation.txt`):**

| Set | Age | Leaves, of NPP (%) | Above-ground wood (%) | Below ground (%) | Basal area over bark (m2/ha) | Stems/ha |
|---|---|---|---|---|---|---|
| Aosaar 2016, one stand: shares by my arithmetic from Table 4, G and N from Table 3 | 10 | 21.6 | 60.6 | 17.8 | 15.2 | 10,200 |
| Stand trees, both | 8-12, mean; basal area at 10 | 13.3 | 58.5 | 28.2 | 16.2 +- 1.6 | 1,800 |
| | 50 | 17.2 | 52.9 | 29.9 | 32.1-34.5 | 450 |
| | 60 | 17.9 | 51.9 | 30.2 | 37.8-40.6 | 450 |
| Plots, both, 4.8 | 8-12, mean | 14.4 | 57.4 | 28.2 | | |
| | 50 | 16.0 | 54.0 | 29.9 | 54.7-58.7 | 1,656 |
| | 60 | 15.8 | 53.6 | 30.6 | 62.6-67.3 | 1,656 |
| Plots, both, 3.0 | 50 | 27.8 | 42.3 | 29.9 | 30.4-32.5 | 1,782 |
| | 60 | 29.1 | 40.2 | 30.7 | 35.0-37.5 | 1,778 |

- **Carbon split, at about age 10:** below ground reads about 10 points over Aosaar's, and leaves about 8 under. I use ages 8-12 because trees flip year to year (age 10 alone reads 11.4 %). The below-ground share comes from `resource.root_share_min`, 0.25 (`treegen/growth.py:867`). Aosaar's is one stand at 10,200 stems/ha, 4.4 cm at 8.5 m, against a model tree at 1,800, 10.7 cm over bark at 9.1 m (node), with roots partly assumed; it has no data at 50, 60; and the model's split is my own accounting. A lead for M3b, not a verdict.
- **Basal area:** Repola's Table 1, p. 607: 2.7-32.3 m2/ha, mean 19.2, 24 stands aged 11-97 at stump height, birch 28-100 % of basal area, four thinning experiments, three on peat. A range check, not a target. Over bark, by which bark figure, stand trees reach 37.8-40.6 at 60, and plots 62.6-67.3. Plots at alpha 3.0 reach 35.0-37.5, so they're over it too. How much of plots' excess is too little thinning, and how much thick stems, isn't worked out. M4.

### Light and leaf area are linked (your review, item b)

**Answer: linked, not one failure.** k is how fast light fades through leaves, k = -ln(light) / LAI (`tools/m2_linked.py`, `m2_linked.txt`). At 50 and 60 it's steady within each wood setting, on trees and plots: 0.388-0.399 with wood on, 0.345-0.347 with wood off. On trees, a seed's light follows its LAI, though at r +0.71 LAI explains only about half the spread. With both proposed corrections on, trees pass LAI and still fail light, because at that k light needs LAI of about 4.67.

| Set, ages 50, 60; node | LAI | Light (%) | Implied k | Each seed's k, SD | r between LAI and -ln(light), across seeds | Light minus exp(-0.37 LAI) (points) | LAI that 19.8 % needs at this k |
|---|---|---|---|---|---|---|---|
| Trees, wood on | 3.09, 3.27 | 30.1, 27.5 | 0.388, 0.394 | 0.046, 0.029 | +0.71, +0.80 | -1.69, -2.27 | 4.18, 4.11 |
| Trees, wood off | 3.62, 3.82 | 28.6, 26.6 | 0.346, 0.347 | 0.014, 0.017 | +0.93, +0.87 | +2.37, +2.23 | 4.68, 4.67 |
| Trees, both | 3.68, 3.85 | 27.9, 26.4 | 0.347, 0.346 | 0.016, 0.015 | +0.85, +0.84 | +2.24, +2.30 | 4.66, 4.68 |
| Plots, wood on | 3.77, 3.76 | 22.3, 22.3 | 0.398, 0.399 | 0.004, 0.002 | too few plots | -2.48, -2.59 | 4.07, 4.06 |
| Plots, wood off | 4.11, 4.08 | 24.1, 24.5 | 0.346, 0.345 | 0.006, 0.004 | too few plots | +2.30, +2.42 | 4.69, 4.70 |
| Plots, wood on, death lines 0.15 (test value) | 4.35, 4.35 | 18.5, 18.3 | 0.388, 0.391 | | too few plots | -1.51, -1.73 | 4.17, 4.14 |

Neither wood setting sits on the paper's 0.37, as your check assumes. k isn't steady with age: on the node, wood off reads 0.321 and 0.331 at 20 and 30. The 0.15 set is the only one to pass light on any scorecard, and it's a test value with no source.

### What holds leaf area down, and is it the wrong knob? (your review, item c)

**Answer: not settled. Lowering alpha for height does cost leaves, as you expected. Wood shade moves leaves with little effect on height. The death lines move leaves and take about 1.3 m off. Steps in sharing move height with leaves about level at 50 and 60 at default, but not at 30, and not with both proposed corrections on.** So "leaves to light, height to sharing" is too simple. How each acts, as my reading of the code:

- **Wood shade** darkens the light grid (`treegen/growth.py:707-724`), so more shoots fall under the death lines.
- **Death lines** kill spurs and limbs under 21 % light (`:781`, `:1132-1162`).
- **Sharing** sets the leader's split at each fork (`:952`), so more carbon up means more height and less crown.
- **The cap** limits one year's shoot (`:1589`).

**Stand trees, node, alpha 4.8, each paired with the default on the same seeds; bold is over 2 SE. All exploring. Corrections on 40 seeds; the rest on seeds 1-20, a low draw for the default's LAI (`m2_linked.txt`, `m2_diagnosis.txt`, `m2_apical_steps.txt`):**

| Change | Seeds | Height at 50, 60 (m) | LAI at 50, 60 | Light at 50, 60 (points) |
|---|---|---|---|---|
| Wood shade off | 40 | +0.09, +0.17 | **+0.40, +0.42** | -0.40, +0.33 |
| Leaf charge | 40 | **-0.48, -0.50** | **+0.11**, +0.09 | **-0.96, -0.86** |
| Both | 40 | -0.10, +0.06 | **+0.48, +0.47** | **-1.42**, -0.31 |
| Both 0.21 death lines at 0.15 (test value) | 20 | **-1.27, -1.33** | **+0.32, +0.36** | **-2.99, -2.66** |
| Spurs may start at 0.21, not 0.30 (test value) | 20 | -0.20, -0.22 | +0.06, +0.08 | +0.34, +0.42 |
| Shoot cap 0.9 m, not 1.2 (test value) | 20 | -0.27, -0.16 | +0.06, +0.02 | -0.38, +0.50 |
| Both apical controls x 0.95 | 20 | **-1.68, -2.07** | +0.17, +0.12 | -2.10, -0.62 |
| x 0.9 | 20 | **-3.58, -4.26** | +0.07, -0.01 | -0.97, +0.48 |
| x 0.85 | 20 | **-6.27, -7.01** | -0.04, -0.13 | -0.11, +1.12 |

The apical steps stay at 450 stems/ha at 50 and 60, so they aren't confounded by density there. At 30, x 0.9 costs 6.19 m2 and x 0.85 costs 18.29 m2 of a tree's leaf area, and on x 0.85, 4 of 20 seeds aren't yet at 450. With both proposed corrections on, all nine grid settings lower LAI at 60 by over 2 SE. That's how far FIX 3 of the M1 review goes: light and sharing are separated at these like-for-like steps, and neither is shown to be the cause.

**The first draw was low.** The default on seeds 21-40 reads 25.07, 26.75 m, LAI 3.36, 3.46, light 27.7, 26.4 %. On all 40: 25.18, 26.91 m, LAI 3.23, 3.37, light 28.9, 26.9 %. Height at 50 passes on the second draw and fails on the first, so it depends on the draw. M1's verdicts stand; I don't rescore them on a draw chosen later (row 77).

### The two proposed corrections

**Answer: neither is adopted. The gate's numbers are in, item 1, a published formulation that names it, isn't met for either, and each waits on you.**

| | Wood shade off | Leaf charge |
|---|---|---|
| What's wrong | Wood's shade is added on top of K_PAR, which was measured through the whole canopy against leaf-only LAI (my inference from Hagemeier & Leuschner 2019b's Methods 2.2, 2.3; no page) | Next spring's clusters on fresh side buds aren't charged, though the code's comment says they were (`treegen/growth.py:1325`, `:1606-1608`, `:240-243`) |
| Gate, trees, seeds 1-20 | No PASS to FAIL. LAI FAIL to PASS at 50, 60, narrowly at 50 (3.62, 55 % of seeds). Nothing worse | No PASS to FAIL. Height PASS at 30-60. Nothing worse |
| Trees, seeds 21-40 | LAI FAIL to PASS. Height at 50 PASS to FAIL, 25.07 to 25.30, within the noise | No PASS to FAIL. Height PASS at 30, 40, 60 |
| Gate, plots | No PASS to FAIL. **Light further by 1.81, 2.25 points;** crown ratio at 20 by 0.03; top height at 50 by 0.23 +- 0.11 | No PASS to FAIL. Light at 50 +0.29 +- 0.14, one row of 15, on two of the five plots |
| Basis | Removes a value with no page. The method argues for it; the outputs don't settle it: implied k 0.345 against the paper's 0.37 | Perttunen 2008, Eq. 21-22, p. 26, text layer: my reading, and it doesn't name leaves on side buds. Adds no number |
| With k near the paper's (PC, stand trees, leaf charge on, input k 0.40, a test value) | LAI 3.32, 3.58\*, fails | Not tried |
| Your question | Q21: I recommend holding it | Q23: I recommend adopting it |

Both together, seeds 1-20 and 21-40: no PASS to FAIL, nothing worse (`gate_both_trees.txt`, `gate_both_trees_fresh.txt`). Plots: light further by 1.99, 2.50 points (`gate_both_plots.txt`). One plot at `3f3d687` equals `base_plots` plot 1 on all 101 files (`m2_plots_control_3f3d687.txt`).

### M2b. Fertility and season length

**Not done:** neither is built, and Q25 asks you whether to. Nothing I can read gives values, and nothing I tried keeps the curve's shape. The model stays one site, near SI 26, over its band today.

**PC, 20 seeds, both proposed corrections on, test values with no source (`pc_q25.txt`, `m2_ladder.txt`). Season stand-in: alpha, leaf upkeep and fine-root upkeep all x 0.9:**

| Test | Height at 10, 20, 30, 50, 60 (m) | LAI at 50, 60 | Site index it reads as at 20, 30, 50, 60 |
|---|---|---|---|
| As now | 9.07, 14.35, 19.22, 25.02, 26.86 | 3.71, 3.87 | 26.7, 26.0, 25.9, 26.1 |
| Carbon below ground 0.15, from 0.25 | 9.01, 14.75, 20.20, 26.24, 28.17 | 3.81, 4.01 | 27.1, 26.8, 27.1, 27.5 |
| Carbon below ground 0.40 | 7.94, 12.89, 16.40, 21.79, 23.65 | 2.92, 3.25 | 25.3, 23.5, 22.9, 22.9 |
| Season stand-in | 8.93, 14.38, 18.74, 24.24, 25.88 | 3.44, 3.62 | 26.7, 25.6, 25.2, 25.1 |

| Gap between a better and a poorer setting, in site index, as each reads at that age. Level would keep the curves' shape | 15 | 20 | 30 | 40 | 50 | 60 |
|---|---|---|---|---|---|---|
| Carbon below ground 0.15 against 0.40 | 1.5 | 1.7 | 3.3 | 3.9 | 4.2 | 4.6 |
| Alpha 5.0 against 3.5 | 1.8 | 2.5 | 4.0 | 4.7 | 5.2 | 5.8 |

- **Fertility:** both spreads widen about threefold from 15 to 60, and 2.7 and 2.3 times from 20, age 15 being outside the target's band, so below-ground share (`treegen/growth.py:867`) is no better than alpha at keeping the shape. Too little spread when young: my guess is that young shoots hit the same length cap at every setting. Its direction rests on one quote I can't check (Makela et al. 2008, Q27); Minunno et al. 2019 gives the route, not the direction, and prints "-" for this ratio for every species. Fine-root mass per leaf mass makes no ladder (`pc_fineroot_shape.txt`): it only moves fine-root upkeep and water uptake (`treegen/growth.py:1252`, `:1333`, `:1656`).
- **Season:** a shorter season takes the most when old, the wrong way for the shape. PRELES's term needs daily temperatures the model doesn't have, with Scots pine values. The model's season only sets the sun's path (`treegen/environment.py:106`). How a shorter season acts by age, as my reading: carbon falls in proportion, while wood's upkeep, which grows with the tree, doesn't, so old trees lose more.
- **The late leaves' share of the season,** at 0.25 and 0.75, isn't the lever (`pc_late*`).

### The apical grid (my own addition, not in the brief)

**Answer: none of the nine settings run meets the lines on seeds 1-20, nothing is picked, and whether M2 should pick at all is Q22.** I set this up on my own (row 62), and a reviewer pointed out that it's close to what you ruled out. Rule first, results after: `m2_cc` and young 0.54 and 0.50 were already in; the other eight weren't. The 0.46-0.54 bound is five values illustrated on synthetic trees, not a published range, and dominance 0.62 sits outside it. Full table: `m2_grid_table.txt`, and the daily report.

| Both proposed corrections, alpha 4.8; today young 0.60, old 0.50 | Height at 20, 30, 40, 50, 60 (m) | Height SD at 60 | LAI at 50, 60 | LAI SD at 50 | Light at 50, 60 (%) | Seeds meeting every line | Under 2 cm at 5-19 |
|---|---|---|---|---|---|---|---|
| Young 0.50, seeds 1-20 | 13.52\*, 18.29, 21.84, 24.33, 26.29 | 0.71 | 3.584\*, 3.693\* | 0.41 | 29.0, 27.8 | 10 % | 4 % |
| Young 0.50, seeds 21-40 | 13.68\* F, 18.29, 21.77, 24.22, 26.06 | 0.61 | 3.619\*, 3.695\* | 0.30 | 28.3, 28.1 | 10 % | 1 % |
| Young 0.50, all 40 | 13.60\*, 18.29, 21.81, 24.27, 26.17 | | 3.602\*, 3.694\* | | 28.6, 28.0 | | |
| Young 0.50, rings ahead, seeds 1-20 (outside the rule) | 12.67, 17.14, 20.58, 22.77, 24.57 | 2.40 | 3.904, 3.865 | 0.40 | 25.7, 26.4 | 45 % | 0 % |
| Young 0.50, rings ahead, seeds 21-40 (outside the rule) | 12.63, 17.05, 20.52, 22.87, 24.75 | 1.25 | 3.950, 4.085 | 0.43 | 25.3, 24.3 | 75 % | 1 % |

On all 40, young 0.50's means land on the lines, by 0.01 m and 0.002: too close to call (row 68). On plots it's 2.49 and 3.00 m over. It takes about the same height off at every age, where alpha takes more and more with age. Against that, its branch wood is 33 kg against 69 from Repola at 60 (PC). M3a inherits it.

**Rings ahead with young 0.50** meets the numbers on trees on both draws, and fails hard on plots: 1.94, 2.51 m over, basal area over bark about 70-75 and 77-83 m2/ha. Its rule has no published form. So it isn't the fix as it stands (Q18).

### Noise

**Answer: nothing was adopted, so the gate's noise test wasn't due.** A look, at alpha 4.79 and 4.81 against 4.80, cells over 2 SE: 3 of 42 at default, 7 of 42 with wood off, 2 of 42 with both (`m2_noise.txt`, `m2_noise_nowood.txt`, `m2_noise_cc.txt`). Each is against one baseline draw, so I don't read these as steadier or wilder. Two wood-off runs at different commits, same seeds, differ on all 20 seeds, with 4 of 6 rows over 2 SE (`m2_twin_nowood.txt`, `m2_linked.txt`): how far a same-setting pair can drift. So I treat a lone 2 SE on seeds 1-20 as a reason to look, as the second draw showed.

### Your review's other items

**Answer:** (d) the idle PC's golden runs, diagnosis and merges are in `reports/P0_performance.md`. (e) Renders are below. (f) 1,000 m2 plots are in M4's list.

### Renders

**Answer: the model hasn't changed, so the example tree is still seed 5, shown in M1. Here it is, with the proposed settings beside it.** Each set's seed is the one closest to its own median. Full meshes were made on the node, and every scored value equals that seed's run in the ensemble (`tools/example_tree.py`, `out/bench/ensemble/example_*`). They were drawn on this PC.

**Default, seed 5:**

![Seed 5 at 10, 30 and 60](renders/M1_example_seed5.png)

**Both proposed corrections, seed 14:**

![Both, seed 14](renders/M2_example_both_seed14.png)

**Both, young apical 0.50, seed 14:**

![Young 0.50, seed 14](renders/M2_example_y50_seed14.png)

**Both, young 0.50, rings ahead, seed 4:**

![Rings ahead with young 0.50, seed 4](renders/M2_example_y50_ahead_seed4.png)

None of these looks like a birch yet. They're still poles with sparse crowns. With rings ahead, the crown is more continuous, and lopsided near the top. That's M3's work. The plot view next to the photo starts at M4.

## 4. Changes made

**No option was adopted, and no default value changed.** The options below are off by default, and an off option leaves the golden hash alone. All 118 tests pass at this report's commit (`out/bench/m2/tests.txt`).

| Commit | What | Default | Before / after |
|---|---|---|---|
| `42e5a78`, `e53de8b`, `a907acf`; merged `3f3d687` | Exploring options: `pipe_model.sapwood_for_next_season`, `bud_fate.density_control`, `resource.leaf_costs.charge_fresh_laterals` | Off | Golden runs identical, 225 files |
| `0386ce7`, merged `2b18cf9` | Light can be read with wood shade off | Output only with wood on, where golden runs are identical. With wood off, it likely changes the path (`KNOWN_ISSUES.md`) | An empty reading now has a value |
| `ad59fc9` | Golden check: an option that's off leaves the hash alone, with a test | Tool | Rehashed, still identical |
| Various, to this report's commit | `tools/m2_*.py`, `tools/m3_*.py`, `tools/ensembles_identical.py`, `tools/plots_identical.py`, `tools/node_queue_lib.sh`, `tools/node/` | Tools | Read saved outputs, or queue runs |
| `bb3048c` | Target text, section 5; VERIFY in comments on the off options' test values | Target text, comments | No band, value or verdict changes |

Node side copy `~/origin/repo_3f3d687`: its golden run is identical to the rehashed `node_a`.

## 5. Proposed targets

Three text corrections under pre-approval (a), and one VERIFY comment, in checker A's words, with the tag moved to `bb3048c` (row 79). No band, value or verdict changes: the scorecard's rows are identical at both tags on all four sets.

| Target | Before | After | Source |
|---|---|---|---|
| `live_crown_ratio.dense_unmanaged_stand.citation` | "...taper of silver birch. Scand. J. For. Res." | "...taper of silver birch (Betula pendula). Scand. J. For. Res." | Crossref's record for the DOI |
| `site_index_curves.sis_reading` | "pp. 9-10 put birch on the H100 pine scale" | "p. 9 (Section 2.2, functions for mean height development in young stands) puts birch on the H100 pine scale..., and p. 10 (Section 2.3, functions for age determination of young trees) gives 'H100pine for pine and birch'" | Elfving 2010, pp. 9, 10 |
| `lai_baltic_chronosequence.page_table` | "Table 4 (p. 122)" | "Table 4 (p. 121)" | Uri 2012's running head, "117-126 121" |
| `lai_baltic_chronosequence`, a comment | No mark | "VERIFY: where 2.5-4.5 comes from isn't settled..." Neither paper prints an LAI | Checker A accepts it as a flag; checker C says (a) doesn't cover it; Q26 asks you |

A text fix waits for the next target change: `lai_hagemeier` says "monospecific", where the source says "monospecific or at least dominated by". New targets aren't proposed here: M3c's come from Evo and Lintunen.

## 6. Checker results

Three fresh checkers ran once on the first draft, then one re-check of the fixes. Full reports: `reports/reviews/2026-11-06_M2_checker_A.md`, `_B.md`, `_C.md`, `2026-11-06_M2_recheck.md`.

| Checker | What it caught | What I did | Unresolved |
|---|---|---|---|
| A, sources and targets | The Baltic LAI band's papers print no LAI. Wood-only diameters against over-bark sources. Three text faults in my target edits. Repola's and Ilomaki's conditions left out. Q21's "can't pass light" rested on that band's top. Q19 tied Figure 6 to the wrong thing. Three publishers blocked it | Applied its words and moved the tag. Mended the tools. Rewrote Q21 and Q19. Added the conditions | Q13, Q14, Q26, Q27 |
| B, numbers | All scorecards and 19 tool reruns reproduce. Bark again. "First set to pass", "one failure", "3.3-6.5 m taller", "about the right size from 30", "takes most when young", "leaves to light, height to sharing": none follows from the numbers. Spread, share and stars missing. Plots' carbon split was saved. Late leaves are in `leaf_dm_g`. PC and node mixed in three places | Reworded each, with the figures. Added the like-for-like ladder. Added spread, share and stars. Saved the figures with `tools/m2_linked.py`, `m2_validation.py`, `m2_fresh.py`, `m2_ladder.py`, and `m2_fresh_grid.txt` | Whether Q16's "not settled" is enough for you: I kept it in the summary |
| C, rules | No default changed. The only fixed file touched is `reference/targets.yaml`, text only; its VERIFY comment isn't covered by pre-approval (a), so Q26 asks you. M2a and M2b need "Not done:". Plain words. Ages 50, 60. Options in section 8. Calibration steps not said. Liziniewicz had no row. "Light fails on every run". VERIFY missing on test values. Lock gaps. Stale rows and lines. Way of working and node scripts not saved | Done, in this report, `DECISIONS.md`, `CAMPAIGN.md`, the way-of-working note, `tools/node/`. Left: `room_mb` is unused, and mesh exports have no memory floor; both before M4's plots | Q26's comment, Q28's tag |

**Also from the checkers, not in that table:** rows 61, 74-76 and commits `e3b1dee`, `cb20216` had no step review of their own, so the checkers stand in for it (row 81). The decision not to build M2b is Q25's to settle.

**The re-check** (`reports/reviews/2026-11-06_M2_recheck.md`): of 79 items, 53 were fixed, 24 partly, 1 not, and 1 deferred as checker A allowed. Scorecards, tools and the target text all held. It listed 14 changes before the tag, and they're in. No further round.

## 7. Corrections to earlier reports

- **M1's baseline was a low draw for LAI.** Its verdicts stand, but "too few leaves" reads smaller on 40 seeds (row 77).
- **Stem wood and basal area used wood-only diameters against over-bark sources (row 80).** "Stem wood 23 % over Repola at 60" was wrong: 6-12 % with both, 2-8 % at default, by which bark. "Inside Repola's range" at alpha 3.0 was wrong at 60 on either bark figure. Also corrected in Q18.
- **"Light fails on every run":** the 0.15 test passes it.
- **"Pass... basal area":** I wrote that verdict by hand, and it has no approved target.
- **"Crowded plot trees 3.3-6.5 m taller":** true only of the thickest 100 per hectare on the curve, and "crowded" assumed the cause.
- **"About 1.5 in alpha":** by line it's 1.0-1.8. **"The first set to pass":** trees with rings ahead got there first; it's the first plot set.
- **Leaves "about 10 under" Aosaar, and "late leaves aren't in `leaf_dm_g`":** that was one on-off year, and they are in it. About 8 under over ages 8-12. **Plots' carbon split "not saved":** it's in the tree files.
- **Q21's "can't pass light":** only against the Baltic band's top. **Q25's "birch's values blank", and Minunno credited with the direction:** Table 1 prints "-" for every species, and it gives the route. **The Baltic band's citation:** its papers print no LAI (Q26).
- **"Below-ground share makes a ladder of about the right size from about 30 on":** the curves' pair was picked from the model's own reading at 60, so they agreed there by construction. On one machine it widens as alpha does.
- **"One failure, not two":** linked is what the numbers show.
- **"Leaves respond to light and height to sharing" and "alpha isn't the knob":** too simple. See item c.
- **Young 0.50 "takes the most off when young":** within the noise.
- **"+0.23 LAI" for the leaf charge, and "+0.53, +0.54" for wood off:** the first draw's. On 40 seeds, +0.11, +0.09 and +0.40, +0.42.
- **Row 60, "none of the later queues can repeat it":** wrong. 15 at once for about 7.5 minutes at 14:42 (row 70).
- **`0386ce7`, "output only":** holds with wood on only (section 4).
- **A shorter season as "one multiplier":** my reasoning, and the run showed otherwise (M2b).
- **Plot light "follows the death line":** that made one link into a separate failure. The line moves LAI, and light follows.
- **Q19 tied Figure 6 to the shade leaves,** where the reading ties it to saplings.
- **"Under 3.6 at every alpha" (alpha 6.0 reaches 3.67), "points at carbon sharing", "about -0.7" in `a7e4c06` (-0.49 to -0.88, -0.73 at 4.8), `fccd283`'s "fix list closed", apical "LAI level", "all but removes", and "bud density doesn't move the pattern":** each went further than the runs, and each is corrected in the daily report or in `QUESTIONS.md`.
- **LAI "3.60", and "both come through at 50 and 60",** as I told you for rings ahead with wood off on the PC: actual 3.599, FAIL at 50.
- **"Corrections" in my tables and titles:** "proposed corrections" is right until you decide.

## 8. Decisions for the maintainer

Full text in `QUESTIONS.md`. Wood shade off waits on Q21, the leaf charge on Q23, and any apical pick on Q22; M2 closes without them. While they're open, M3 scores the default and shows both proposed corrections beside it. If you answer mid-way, I apply it at the next step's end, then record a new baseline of 20 trees and 5 plots, with golden runs and the noise test.

| # | Decision | Options | Recommendation |
|---|---|---|---|
| Q28 | Tag M2 as closed, with M2a and M2b parked? | (a) tag, saying so; (b) leave M2 open | (a) |
| Q27 | Three papers need your browser, two more would help | (a) save what you can; (b) leave them | (a), Hagemeier first |
| Q26 | The Baltic LAI band's papers print no LAI | (a) keep scoring, marked; (b) move to INFO; (c) replace under a proposal; or remove the mark | (a), and (c) in M4 if I find a source |
| Q25 | Fertility and season: nothing keeps the shape | (a) build neither now; (b) build below-ground share, off; (c) try Makela 2016 first | (a) |
| Q24 | A leftover loop of mine on the admin account | (a) stop it: `! ssh admin@node 'kill 960329'`; (b) leave it | (a) |
| Q23 | The leaf charge has no equation naming it | (a) count it as a correction, at the next step's end; (b) wait for a paper | (a) |
| Q22 | May M2 pick apical values, when you put sharing in M3? | (a) pick nothing, hand to M3; (b) adopt young 0.50, overriding row 68 | (a) |
| Q21 | Wood shade off | (a) correct it now; (b) hold until Q19 and Q26; (c) leave it on; (d) off and retune k, forbidden unless you say | (b) |
| Q19 | The 21 % death line: what's its spread? | (a) read it from the paper; (b) keep it and report light can't be reached | (a) |
| Q18 | Rings sized for next spring's leaves | (a) gate it as my reading; (b) don't adopt without a paper; (c) a storage form | (b) |
| Q17 | The height curve below 20, as INFO? | (a) show it; (b) leave it out | (a) |
| Q16 | If no alpha fits, is it how carbon is shared out? | (a) report as you asked, leads open; (b) name nothing until M3 has run | (a) |
| Q15 | The Niemisto PDF is the wrong paper | (a) save the right one; (b) leave it | (a) if it's easy |
| Q14 | How the height curve is fitted | (a) keep it, simple figure beside it; (b) fit only the taller trees | (a); M4 must settle it |
| Q13 | Targets scored on stands unlike the source's | (a) add density labels; (b) keep scoring, with a note | (b) |
| Q12 | I rewrote a gate test I'd added, to follow your Q8 | Accept it, or restore it | Accept it |
| Q11 | P0's stop rule, on plots | (a) stop now, reopen at M4; (b) compile the carbon solve now | (a) |
