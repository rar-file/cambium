# Round 40 report

PROTOCOL.md was read at commit `31cb4cb`. All runs are the seed-1 stand tree over 60 years, with one option switched on at a time. Phase notes: KNOWN_ISSUES.md, "Phase 40".

## 1. Summary
- **Borchert–Honda:** the published rule makes the see-saw worse, not better. The tree grows no new shoots at all in 10 different years, and the crown still has bands.
- **Run outputs:** every run now saves the light at 1–2 m and a manifest. Light is about 30 % at 50–60 against a target of 6.4–19.8 %, but it can't be scored without a scorecard change.
- **Soil water:** the option now uses published BILJOU formulas. With Uppsala rain, even in 2018, the soil never gets dry enough to matter, so growth doesn't change.
- **Branch wood:** limbs are already thicker than their own weight needs. The branch wood shortfall comes from too few, too short limbs.
- **White patches and germination:** the white patches come from render lighting on the flared stem base and can't be fixed without a choice. No source supports the germination leaf-size rule.

## 2. Scorecard (tools/scorecard.py output, unchanged)

**Default** (`out/bench/p40_default_v2/scorecard.txt`; its rows are identical to `out/bench/p40_default/scorecard.txt`):

```
Targets: reference/targets.yaml at targets-approved (commit 41d18c1). Runs: out/bench/p40_default_v2/1_stand

| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |
|---|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 50)` | 2.990 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 2.952 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | 0.50 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | 0.61 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | 0.67 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.69 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.70 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | 0.50 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | 0.61 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | 0.67 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.69 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.70 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | 880 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | 420 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | See yaml | **NOT APPLICABLE** | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 20)` | 15.20 m | 9.05-14.31 m (SI20-SI26, bh age 16) | **FAIL** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 30)` | 19.97 m | 13.44-19.67 m (SI20-SI26, bh age 26) | **FAIL** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 40)` | 23.09 m | 16.74-23.07 m (SI20-SI26, bh age 36) | **FAIL** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 50)` | 25.02 m | 19.20-25.31 m (SI20-SI26, bh age 46) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 26.11 m | 21.05-26.87 m (SI20-SI26, bh age 56) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | See yaml | **NOT SCORED** | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | See yaml | **NOT SCORED** | Repola (2008) | scorecard.py computes no model value for this target |
| `tree_allometry.wood_basic_density` | N/A | See yaml | **NOT SCORED** | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | See yaml | **NOT SCORED** | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | See yaml | **NOT SCORED** | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | [0.15, 0.35] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | [1.20, 1.80] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.field_layer` | N/A | See yaml | **NOT APPLICABLE** | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | needs a single-seedling or plot run |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | See yaml | **NOT APPLICABLE** | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

### Targets without conditions in targets.yaml (listed for the maintainer's approval)
- none

INFO: information only (scoring: info in targets.yaml), never PASS/FAIL. NOT SCORED: the script computes no model value for that target.
```

**Published Borchert–Honda on** (`out/bench/p40_bhpub/scorecard.txt`):

```
Targets: reference/targets.yaml at targets-approved (commit 41d18c1). Runs: out/bench/p40_bhpub/1_stand

| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |
|---|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 50)` | 2.586 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 2.612 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | 0.54 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | 0.65 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | 0.70 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.73 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.75 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | 0.54 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | 0.65 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | 0.70 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.73 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.75 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | 880 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | 420 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | See yaml | **NOT APPLICABLE** | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 20)` | 14.55 m | 9.05-14.31 m (SI20-SI26, bh age 16) | **FAIL** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 30)` | 18.82 m | 13.44-19.67 m (SI20-SI26, bh age 26) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 40)` | 22.54 m | 16.74-23.07 m (SI20-SI26, bh age 36) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 50)` | 25.00 m | 19.20-25.31 m (SI20-SI26, bh age 46) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 27.35 m | 21.05-26.87 m (SI20-SI26, bh age 56) | **FAIL** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | See yaml | **NOT SCORED** | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | See yaml | **NOT SCORED** | Repola (2008) | scorecard.py computes no model value for this target |
| `tree_allometry.wood_basic_density` | N/A | See yaml | **NOT SCORED** | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | See yaml | **NOT SCORED** | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | See yaml | **NOT SCORED** | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | [0.15, 0.35] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | [1.20, 1.80] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.field_layer` | N/A | See yaml | **NOT APPLICABLE** | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | needs a single-seedling or plot run |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | See yaml | **NOT APPLICABLE** | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

### Targets without conditions in targets.yaml (listed for the maintainer's approval)
- none

INFO: information only (scoring: info in targets.yaml), never PASS/FAIL. NOT SCORED: the script computes no model value for that target.
```

**Germination on** (`out/bench/p41_germ_v2/scorecard.txt`):

```
Targets: reference/targets.yaml at targets-approved (commit 41d18c1). Runs: out/bench/p41_germ_v2/1_stand

| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |
|---|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 20)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 30)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 40)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 20)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 20 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 30)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 30 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 40)` | N/A | [3.60, 5.40] | **NOT APPLICABLE** | Hagemeier & Leuschner (2019) | age 40 outside age_years [45, 65] |
| `stand_canopy.lai_hagemeier (age 50)` | 2.957 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 2.995 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 20)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 20 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 30)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 30 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 40)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | age 40 outside age_years [45, 65] |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | subcanopy light not saved in run output |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 20)` | 0.44 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 30)` | 0.58 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 40)` | 0.64 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.67 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.69 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 20)` | 0.44 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 30)` | 0.58 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 40)` | 0.64 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.67 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.69 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 20)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 30)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 40)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | 880 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | 420 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | See yaml | **NOT APPLICABLE** | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 20)` | 14.09 m | 9.05-14.31 m (SI20-SI26, bh age 16) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 30)` | 18.91 m | 13.44-19.67 m (SI20-SI26, bh age 26) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 40)` | 22.57 m | 16.74-23.07 m (SI20-SI26, bh age 36) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 50)` | 24.79 m | 19.20-25.31 m (SI20-SI26, bh age 46) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 26.33 m | 21.05-26.87 m (SI20-SI26, bh age 56) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | See yaml | **NOT SCORED** | Hansen et al. (2023) | scorecard.py computes no model value for this target |
| `tree_allometry.crown_width_open_grown (age 20)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 30)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 40)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 50)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.crown_width_open_grown (age 60)` | N/A | Crown diameter (m) = 0.932 + 0.177 * DBH_over_bark_cm | **NOT APPLICABLE** | Hemery, Savill & Pryor (2005) | needs a single-tree run |
| `tree_allometry.foliage_biomass` | N/A | See yaml | **NOT SCORED** | Repola (2008) | scorecard.py computes no model value for this target |
| `tree_allometry.wood_basic_density` | N/A | See yaml | **NOT SCORED** | Aosaar et al. (2016) | scorecard.py computes no model value for this target |
| `tree_allometry.carbon_fraction` | N/A | See yaml | **NOT SCORED** | Thomas & Martin (2012) | scorecard.py computes no model value for this target |
| `tree_allometry.critical_turning_moment` | N/A | See yaml | **NOT SCORED** | Krišāns et al. (2022) | scorecard.py computes no model value for this target |
| `juvenile_establishment.natural_clearcut_heights (age 2)` | N/A | [0.15, 0.35] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.natural_clearcut_heights (age 5)` | N/A | [1.20, 1.80] m | **NOT APPLICABLE** | Johansson (1999); Niemistö (1995); Valkonen et al. (2002); Hynynen et al. (2010) | needs a single-seedling or plot run |
| `juvenile_establishment.field_layer` | N/A | See yaml | **NOT APPLICABLE** | Aubin, Beaudet & Messier (2000, Can. J. For. Res. 30:168); SMEAR II Hyytiälä data; Ring & Sikström (2024, Silva Fennica 58:23056) | needs a single-seedling or plot run |
| `juvenile_establishment.seedling_root_shoot_ratio` | N/A | See yaml | **NOT APPLICABLE** | Konôpka et al. (2023, Plants 12:1607); Laitakari (1935, Acta For. Fenn. 41) | needs a single-seedling run |

### Targets without conditions in targets.yaml (listed for the maintainer's approval)
- none

INFO: information only (scoring: info in targets.yaml), never PASS/FAIL. NOT SCORED: the script computes no model value for that target.
```

**Soil water on, normal year and 2018** (`out/bench/p40_swb_norm/scorecard.txt`, `out/bench/p40_swb_dry/scorecard.txt`): every row is identical to the default above. Checker B reran all three and found them byte-identical apart from the header line.

## 3. Task items

### 1. Leader see-saw: published Borchert–Honda
Answer: it does not remove the bands; the see-saw gets larger. I didn't make it the default.
- **Equation:** the extended Borchert–Honda model of Palubicki et al. 2009, a computer-graphics model formulation; Borchert & Honda 1984 was not opened. It reads v_main = v·λQ_m / (λQ_m + (1−λ)Q_l). In code, `treegen/growth.py:906-910`: `denom = lam * Qm + (1.0 - lam) * Ql`, return `lam * Qm / denom`.
- **What the option changes:** λ = 0.62 at every node (`:893-894`), and gravimorphism and scaffold vigour are left out of the bud pull (`:870-873`).
- **What still shapes the split:** water stress, upkeep, the rule that short shoots draw nothing, and the no-axillary-bud rule (`:878-886`).

| Age | Height, default (m) | Height, BH (m) | LAI, default | LAI, BH | Branch wood / Repola, default | Branch wood / Repola, BH |
|---|---|---|---|---|---|---|
| 20 | 15.20 | 14.55 | 1.86 | 1.98 | 0.12 | 0.16 |
| 30 | 19.97 | 18.82 | 2.11 | 1.85 | 0.17 | 0.16 |
| 40 | 23.09 | 22.54 | 2.75 | 2.21 | 0.15 | 0.12 |
| 50 | 25.02 | 25.00 | 2.99 | 2.59 | 0.12 | 0.12 |
| 60 | 26.11 | 27.35 | 2.95 | 2.61 | 0.11 | 0.22 |

Height growth from year to year (change in tree height, years 21–60):

| | Default | BH |
|---|---|---|
| mean / SD (m) | 0.273 / 0.248 | 0.320 / 0.355 |
| mean change from one year to the next (m) | 0.272 | 0.502 |
| years under 0.10 m (of 40) | 14 | 15 |
| years with no new long shoot anywhere on the tree | 1 (year 17) | 10 (18, 23, 29, 32, 34, 36, 38, 40, 44, 46) |

- **Every year from 20 to 60:** the yearly table (height, increment, long shoots) is in `out/bench/p40_bhpub/leader_compare.txt`. At age 50 the increment is 0.075 m (default) against 0.284 m (BH); at 60 it is 0.066 m against 0.248 m.
- **Render:** `out/renders/p40/stand_tree_seed1_age60_default_vs_bhpub.png`. With BH on, the top quarter of the crown is a bare leader, one large limb sits mid-crown, and the lower crown still has bands.
- **Likely mechanism (not tested):** BH keeps λ at 0.62 everywhere, where the default lowers it to 0.50 on old branches. That sends more growth to the main axis, which fits the taller tree and the lower LAI.
- **Not diagnosed:** why the whole tree grows long shoots only every other year.

### 2. Run outputs
Answer: done and committed (`bc4387d`). Every stand-tree and plot run now saves:
- **Light:** `subcanopy_light_pct` for each year, at 1.0, 1.5 and 2.0 m (`treegen/light.py:224`, `:270-285`).
- **Manifest:** `run_manifest`, with the git commit, species and environment file hashes and the options switched on (`treegen/params.py:38-98`).
- **Growth unchanged:** the reruns `p40_default_v2` and `p41_germ_v2` are identical to the earlier runs in every value.

| Age | Light at 1–2 m, default | Light at 1–2 m, germination | Target |
|---|---|---|---|
| 50 | 30.1 % | 30.1 % | 6.4–19.8 % |
| 60 | 29.6 % | 30.1 % | 6.4–19.8 % |

Not scored: the scorecard reads only a single value for the whole run (Decision 2). The model's light is the sky and sun together; the target is diffuse light only.

### 3. Germination audit
Answer: no published relation between leaf size and height or age for young birch was found. The rule leaf size = 0.20 + 0.80 × H / 1.30 m (`treegen/growth.py:1236-1242`) is invented.

| Parameter | Status |
|---|---|
| seed mass 0.21 mg | Cited papers not opened. The USDA seed manual gives ~0.19 mg (0.09–0.30). VERIFY |
| respiration loss 0.35 | No birch source. VERIFY |
| hypocotyl height 1.5 cm | No source. VERIFY |
| first-year leaves 0.20 | Calibrated; Konôpka 2023 has no first-year data. VERIFY |
| leaf ramp: 1.3 m and 0.20 | No source; invented. VERIFY |
| cotyledon area, taproot depth | Not used by the code |

VERIFY flags were added to the species-file comments; no value changed. The closest lead is Oleksyn et al. 2000 (Trees 14:271), which was not opened. Options are in Decision 4.

### 4. Soil-water option
Answer: each invented piece was replaced with a published one, and the option stays off (`9885e03`).
- **Transpiration:** the factor 0.25 + 0.75·min(1, LAI/3) became Granier et al. 1999 Eq. 2, r = 0.125·LAI up to 0.75.
- **Time step:** the monthly step with a half-month rain rule became BILJOU's daily balance (Eq. 1).
- **Open-grown LAI:** min(3.5, leaf area/10) became the model's own LAI.
- **Dry year:** rain × 0.5 and PET × 1.2 became the real 2018 Uppsala rain.

| Year | Lowest REW at 50 | Lowest REW at 60 | Season T / Tmax | Growth |
|---|---|---|---|---|
| normal (SMHI 1991–2020) | 1.00 | 1.00 | 1.00 | identical to default |
| 2018 | 0.578 | 0.580 | 1.00 | identical to default |

- **Why nothing changes:** at LAI 3, the most the trees can transpire is 30 / 37 / 39 / 26 / 11 mm in May–September. Normal rain is higher in every month. 2018 had 272 mm over that period against a 280 mm normal; only May and June were dry.
- **Still unsourced (VERIFY):** the carbon cut, the season starting at field capacity, no interception term, and the 75 mm water capacity.

### 5. Branch mechanics
Answer: yes, published sources size wood by self-weight, and the model already does this (the stress floor, `treegen/growth.py:1853-1858`, `:1907`). It would add no branch wood, because the limbs are already thicker than their load needs.

| Largest limbs at 60 | Fresh wood (kg) | Leaves (kg) | Moment (N·m) | Radius needed (mm) | Actual radius (mm) |
|---|---|---|---|---|---|
| 1 | 1.51 | 1.05 | 14.2 | 10.4 | 20.3 |
| 2 | 0.67 | 0.51 | 6.8 | 8.1 | 13.1 |
| 3 | 0.78 | 0.58 | 6.0 | 7.8 | 15.7 |

- **Radius needed:** (4·M / (π·16.3 MPa))^(1/3), with leaves and actual lever arms (`out/bench/p40_default_v2/limb_moment_calc.txt`).
- **What Repola's wood would take:** 65 kg instead of 6.8 kg on the same 688 m of branch would need a mean radius of 7.5 mm, not 2.4 mm. The longest limbs reach only 1.3–1.8 m sideways. So the problem is too few, too short limbs.
- **Floor switched off:** 0.12 / 0.16 of Repola at 50 / 60; why is not diagnosed.
- **Sources:**
  - Jirasek 2000 computes deflection only.
  - McMahon & Kronauer and Niklas's books were not opened.
  - Minamino & Tateno 2014: beech fits uniform stress, fir doesn't.
  - No silver-birch constants were found.

### 6. White patches
Not done: the cause lies in mesh and render code, but each possible fix needs a value or method with no source.
- **Cause:**
  - The root ridges tilt the stem base upward (`treegen/mesh.py:309`, `:347`): +0.135 on average at 0.1–0.2 m, against 0.00 above 0.3 m.
  - The renderer lights every surface with full sky and sun and no canopy shadow (`treegen/preview.py:292-299`).
  - Thick stems are near-white (`:312-321`).
- **Effect:** a sun-facing face tilted like the ridges renders 30 % brighter (0.804 against 0.620; `out/renders/p40/white_patch_check.txt`).
- **Not a growth-model issue:** the normals point outward.
- **Options:** Decision 5.

### 7. Notes
Answer: notes for phases 34–36 and 39 were reconstructed from git history and saved files, and the four phase-38 commits were added.
- **Phase 37–38 corrections:** the claimed SI26 match, the taper excess, the branch wood, the form factor, and the phase 36 figures.
- **Not reconstructable:** which commit belongs to phase 34, 35 or 36; any phase 34–36 run outputs; the phase 36 numbers.

## 4. Changes made

| Commit | What | Default | Before / after |
|---|---|---|---|
| `bc4387d` | Save the light at 1–2 m and a run manifest | output only | Growth identical (p40_default vs p40_default_v2) |
| `9885e03` | Soil-water option: BILJOU formulas | off | Default identical (p40_default_v2 vs v3); with the option on, identical growth (Task 4) |
| (this round's last commits) | Phase notes, report, DECISIONS rows 16–17; VERIFY comments and citation fixes in the species file; soil-water assumptions stated in the code comments | no values changed | Parsed species values identical to `9885e03` |

Tests: 39 passed.

## 5. Proposed targets
None.

## 6. Checker results

| Checker | What it caught | What I did | Unresolved |
|---|---|---|---|
| A (sources and targets) | targets.yaml unchanged and used within its conditions. Fixes needed: PET table page (44, not 45); the Granier wording "fitted on"; unstated soil-water assumptions; the fir result described as supporting; the Borchert–Honda label; missing VERIFY flags | All corrected | — |
| B (numbers) | Every number recomputed. Wrong or loose: the zero-long-shoot years (10, plus year 17 in the default); the hand moment (8.7 mm); the white-patch +0.23, brightness and 76/78 figures; some phase 37–38 numbers; the lowest REW (0.566 at 59) | Recomputed with saved scripts (`limb_moment_calc.txt`, `white_patch_check.txt`) and corrected | — |
| C (rules and completeness) | Fixed files untouched, tests 39/39. Flags: the "transport attenuation" statement wrong; file:line references missing; tasks 3, 5 and 6 incomplete; the invented soil-water pieces not listed; species copies not purely one option; more 37–38 overclaims; missing commits; no DECISIONS row; no Answer:/Not done: | All corrected in the notes and this report | Task 6 not fixed (Decision 5). Phase 33 overclaims left alone because they're outside the brief (Decision 6). Light not scorable (Decision 2) |

## 7. Corrections to earlier reports
- **Round 39 scorecard:** `32bbe54` filled in an invented light value. Disregard every PASS/FAIL produced before `e0b8d10`.
- **Phase 37 & 38 notes:**
  - "matches Eriksson SI26": height is inside the band, below the SI26 curve itself.
  - Taper excess: 12–20 % only at 50; 14–22 % at 60.
  - Branch wood: 0.11–0.17 of Repola, and the stated mechanism was never tested.
  - Form factor: the model gives 0.45–0.47.
  - Phase 36 figures: can't be recomputed.
- **Soil-water citations:** Granier 1999's fourth author is Villette. The PET is for Forsmark, not "Uppland" in general. The Uppsala station is 97520.
- **Germination:** Konôpka et al. 2023 has no first-year seedling data.

## 8. Decisions for the maintainer
1. **Published Borchert–Honda option.**
   - (a) Keep it off.
   - (b) Make it the default.
   - Recommendation: **(a)**. It makes the see-saw worse and puts height above the band at 60.
2. **Scoring the light under the canopy.**
   - (a) Approve a scorecard change to read the light for each year.
   - (b) Also add a diffuse-only light output, so it compares like for like with the target.
   - (c) Leave it unscored.
   - Recommendation: **(a) + (b)**.
3. **Soil-water option.**
   - (a) Drive the soil water potential the trees feel from the bucket, using a published water-retention curve for till (needs a source).
   - (b) Keep the carbon cut as it is (unsourced).
   - (c) Drop the option.
   - For interception: daily SMHI weather would make BILJOU's own equation usable.
   - Recommendation: **(a)** plus daily weather, or **(c)** if water stress isn't a priority. Under Uppsala rain the option currently does nothing.
4. **Germination leaf-size rule.**
   - (a) Remove the juvenile leaf-size ramp until there is a source.
   - (b) Get Oleksyn et al. 2000 (Trees 14:271) through a library and fit a rule to it.
   - (c) Keep it, flagged VERIFY.
   - Recommendation: **(b)**, keeping the germination option off meanwhile.
5. **White patches.**
   - (a) Shade the sun and sky in stand renders using the model's own light field.
   - (b) Darker birch bark at the stem base, needs a source for colour and extent.
   - (c) Lower the root ridges (changes the published collar height).
   - Recommendation: **(a)**.
6. **Phase 33 overclaims.** "Solved the leader growth paradox", "approaching target" and "successfully reduced" contradict phase 40 or use banned words.
   - Recommendation: approve correcting them.
7. **Run manifest.** Add a fingerprint of uncommitted code changes, so runs made before a commit can still be identified.
   - Recommendation: yes; it's small.
8. **Next round's priority:** diagnose why the whole tree grows long shoots only every other year (10 years with none under BH, 1 under the default). This is the likely source of the crown bands.
   - Recommendation: make it the top task.
