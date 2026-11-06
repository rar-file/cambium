# Milestone M1: Foundations (stopped at a hard stop, not finished)

Protocol hash at the start of the campaign: `0e58497`. Date: 2026-11-06.

## 1. Summary
- M1 stopped on memory: this PC has one 16 GB stick, not 32 GB, so the 8 GB free rule blocks every model run. M1 can't finish, and M2-M6 can't start, until the maintainer picks an option (decision 1).
- Alpha 4.8 is traceable, but it's a one-point model calibration, not a published value. It now carries VERIFY.
- The height band is corrected, as a preview until checker A confirms: one verdict changes (p41_germ at age 20 goes to FAIL).
- Yearly diffuse light scoring, the manifest fingerprint and the phase 33 corrections are done.
- The audit opened sources for 65 of 274 values. On 11 the page doesn't support the value, including my own wrong citation for the distance rule.

## 2. Scorecard
From saved runs only; no new run was possible. p40_default_v3 is the current default's growth (it was made before this campaign's output-only changes).

**Approved targets (the tag, not moved), `out/bench/m1/scorecard_p40_default_v3_tag.txt`:**

Targets: reference/targets.yaml at targets-approved (commit 41d18c1). Runs: out/bench/p40_default_v3/1_stand

| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |
|---|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 50)` | 2.990 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 2.952 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | diffuse subcanopy light not saved in run output (sky-and-sun light 30.1 %, not scored: not the target's measure) |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | diffuse subcanopy light not saved in run output (sky-and-sun light 29.6 %, not scored: not the target's measure) |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.69 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.70 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.69 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.70 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | 880 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | 420 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | See yaml | **NOT APPLICABLE** | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 50)` | 25.02 m | 19.20-25.31 m (SI20-SI26, bh age 46) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 26.11 m | 21.05-26.87 m (SI20-SI26, bh age 56) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | See yaml | **NOT SCORED** | Hansen et al. (2023) | scorecard.py computes no model value for this target |
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

**Preview with the corrected targets (HEAD), `out/bench/m1/scorecard_p40_default_v3_preview.txt`:**

Targets: reference/targets.yaml at HEAD (commit 284a48e). NOT the approved tag targets-approved (commit 41d18c1): results are a preview, not approved. Runs: out/bench/p40_default_v3/1_stand

| Target | Model Value | Target Range / Value | Status | Source | Stated Conditions / Notes |
|---|:---:|:---:|:---:|:---:|---|
| `stand_canopy.lai_baltic_chronosequence (age 50)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_baltic_chronosequence (age 60)` | N/A | [2.50, 4.50] | **NOT APPLICABLE** | Uri et al. (2012); Varik et al. (2015); Aosaar et al. (2016) | needs a plot run |
| `stand_canopy.lai_hagemeier (age 50)` | 2.990 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.lai_hagemeier (age 60)` | 2.952 | [3.60, 5.40] | **FAIL** | Hagemeier & Leuschner (2019) | stand LAI |
| `stand_canopy.subcanopy_light_transmittance (age 50)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | diffuse subcanopy light not saved in run output (sky-and-sun light 30.1 %, not scored: not the target's measure) |
| `stand_canopy.subcanopy_light_transmittance (age 60)` | N/A | [6.40, 19.80] % | **NOT APPLICABLE** | Hagemeier & Leuschner (2019b) | diffuse subcanopy light not saved in run output (sky-and-sun light 29.6 %, not scored: not the target's measure) |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 50)` | 0.69 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.silvicultural_recommendation (age 60)` | 0.70 | >= 0.5 | **INFO** | Hynynen et al. (2010) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 50)` | 0.69 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.managed_stand_empirical (age 60)` | 0.70 | [0.29, 0.96] (mean 0.58) | **INFO** | Repola (2008) | crown ratio of the stand tree |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 50)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.live_crown_ratio.dense_unmanaged_stand (age 60)` | N/A | [0.30, 0.45] | **NOT APPLICABLE** | Niemistö (1995, Paper 1); Repola (2008) | needs a plot run |
| `stand_canopy.stand_density (age 45)` | N/A | 880 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.stand_density (age 67)` | N/A | 420 stems/ha | **NOT APPLICABLE** | Hagemeier & Leuschner (2019, Forests 10(3):265) | needs a plot run |
| `stand_canopy.dominant_height_invariance` | N/A | See yaml | **NOT APPLICABLE** | Niemistö (1995, Scand. J. For. Res. 10:245-255); Hynynen et al. (2010, Forestry 83:103) | needs a plot run |
| `tree_allometry.site_index_curves (age 50)` | 25.02 m | 18.76-25.12 m (SI20-SI26, bh age 44.0-45.0) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.site_index_curves (age 60)` | 26.11 m | 20.72-26.73 m (SI20-SI26, bh age 54.0-55.0) | **PASS** | Eriksson, Johansson & Kiviste (1997) | dominant height = the stand tree's height (neighbours are copies of it) |
| `tree_allometry.bark_thickness` | N/A | See yaml | **NOT SCORED** | Hansen et al. (2023) | scorecard.py computes no model value for this target |
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

## 3. Task items

### M1a. Alpha provenance

Answer: 4.8 is traceable, but it's a one-point model calibration, not a published value. It now carries VERIFY.

**Where it came from.** Commit `c3fd2dc` (2026-11-01, phase 22; KNOWN_ISSUES.md:618-621). The chain:

| Step | Value | Source |
|---|---|---|
| Tree NPP, 10-year-old stand | 13.02 Mg/ha/yr | Aosaar et al. 2016, Table 4, p. 8 (opened) |
| Leaf mass | 2.81 Mg/ha | same table |
| SLA | 15 m²/kg, so LAI 4.21 | Uri et al. 2007, abstract only: an 8-year-old stand |
| Carbon fraction | 0.48 | Thomas & Martin 2012, Table 2, p. 337 (subagent opened) |
| CUE | 0.45 | assumed in that commit; the species file also says 0.47 |
| GPP per m² of leaf | 329 g C, 1080 model units at 0.305 g C per unit | calculation, `tools/alpha_check.py` |
| alpha | 4.8 | the value at which one natural-plot run fixed that much per m² of leaf at years 16-20 |

The knowledge base is right that 4.8 isn't in Aosaar and that the paper has no light or photosynthesis data. "No traceable source" goes too far: the path is in the git log. The species comment's "set from sources, not from heights" also went too far: the inputs are from sources, but the 4.8 comes from a model run. It also mixes a 10-year-old stand's leaf mass with an 8-year-old stand's SLA.

**Before that, it was tuned to height.** The values went 5.6, 6.2, 5.2, 4.8 (`git log -G` on the species file). Earlier values back to 4.6 are in the comment at `species/betula_pendula.yaml:101-109`. Those were tuned to the height curves.

**How much depends on it.**
- **All carbon.** Fixed carbon is alpha × Σ(light × stomatal opening × leaf weight) (`treegen/growth.py:797`). The same alpha sets each branch's carbon balance, so it also drives branch death (`:933`, `:969`), and it pays the late leaves (`:1583-1589`). Plot trees multiply it by their vigour (`treegen/plot.py:85`, `:179`).
- **One value still in use was set with alpha at 4.8:** `maintenance_per_internode` 0.5, in the same commit, to reach a plot CUE of 0.42. `huber_path_exponent` 0.283 was also fitted at 4.8, but stem theory stage 2 switches it off (`treegen/growth.py:1469-1471`). Full list: `out/bench/m1/species_changes_since_alpha.txt`.
- **Every scorecard verdict on a model output** rests on it.
- **Older calibrations were made at other alphas and never redone,** such as `wood_volume_per_carbon` and the phase 16 gravitropism fit. Their dependence on alpha is not calculated.

**Does the derivation still hold?** On the seed-1 stand tree the model fixes 0.92-1.12 times the derived figure per m² of leaf (`out/bench/m1/alpha_check.txt`):

| Age | LAI | g C per m² of leaf | Ratio to the 329 derived |
|---|---|---|---|
| 10 | 2.58 | 305 | 0.92 |
| 20 | 1.86 | 370 | 1.12 |
| 30 | 2.11 | 348 | 1.06 |
| 50 | 2.99 | 302 | 0.92 |
| 60 | 2.95 | 312 | 0.95 |

But the derivation assumed CUE 0.45, and the seed-1 tree's CUE was 0.54 at age 30 (`carbon.cue`, same run). That goes to M2.

Not done: a sensitivity number for alpha itself. It needs model runs.

### M1b. Height target

Answer: the 1.3 m offset and breast-height age were already right; the fixed 4-year shift was not. Corrected, but the tag isn't moved until checker A confirms.

**Source, opened this round** (Elfving 2010, `birch-data/07_stand_dynamics/Elfving_Heureka_prognossystem.pdf`, 99 pages, dated 05/02/2010):
- p. 58: "For birch the equation gives height development above breast height as function of age at breast height."
- p. 56: "For other broad-leaves (birch, aspen etc.) the following relation is applied: T13 = 150/SIS".
- p. 55: "sis site index according to site factors, given as top height at age 100, m".
- p. 58, Table 1: asi 7, beta 394, b2 −1.3870.

**What the code did.** `treegen/reference.py:15-18` subtracts 1.3 from the site index, runs the curve on breast-height age and adds 1.3 back, which agrees with p. 58. `tools/scorecard.py` then used a fixed 4 years to get breast-height age.

**Where the source leaves a gap.** SIS is a top height at age 100, set from site factors for a site-indicative species (pp. 20, 38, 55). The target's site index is birch height at breast-height age 50. Elfving prints no conversion, and I found none in the Heureka wiki pages on disk. The brief's and knowledge base's "150 / site index" (5.8 at SI 26) treats the two scales as the same. I used this curve's own height at total age 100 as SIS, solved together with T13, because that keeps the source's definition. It's still a stand-in: birch, not the site-indicative species. Flagged VERIFY in targets.yaml; decision 2.

| Site index | SIS used | T13 used | 150/SI | Fixed value before |
|---|---|---|---|---|
| 20 | 25.08 m | 5.98 yr | 7.50 yr | 4 yr |
| 26 | 29.93 m | 5.01 yr | 5.77 yr | 4 yr |

**Band before and after (m):**

| Total age | Before (T13 = 4) | After | If T13 = 150/SI |
|---|---|---|---|
| 20 | 9.05-14.31 | 8.05-13.61 | 7.26-13.07 |
| 30 | 13.44-19.67 | 12.66-19.24 | 12.03-18.90 |
| 40 | 16.74-23.07 | 16.16-22.79 | 15.69-22.57 |
| 50 | 19.20-25.31 | 18.76-25.12 | 18.42-24.98 |
| 60 | 21.05-26.87 | 20.72-26.73 | 20.46-26.63 |

The band moves down at both edges. It isn't looser: the top edge drops at every age.

**Rescored** (`tools/rescore_compare.py`, `out/bench/m1/height_rescore.txt`; a preview until the tag moves). Every verdict at 20, 30, 40, 50 and 60:

| Run | 20 | 30 | 40 | 50 | 60 | Changed |
|---|---|---|---|---|---|---|
| p40_default, height (m) | 15.20 | 19.97 | 23.09 | 25.02 | 26.11 | |
| p40_default, before | FAIL | FAIL | FAIL | PASS | PASS | |
| p40_default, after | FAIL | FAIL | FAIL | PASS | PASS | none |
| p41_germ, height (m) | 14.09 | 18.91 | 22.57 | 24.79 | 26.33 | |
| p41_germ, before | PASS | PASS | PASS | PASS | PASS | |
| p41_germ, after | **FAIL** | PASS | PASS | PASS | PASS | age 20 |
| p38_nat, before and after | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE | none; plot top height is still unconfirmed (DECISIONS.md row 15) |

With T13 = 150/SI, these would also change: p40_default at 50 to FAIL (25.02 m against 24.98) and p41_germ at 30 to FAIL (18.91 m against 18.90). The choice matters at the margin, so it's decision 2. Those verdicts are from a calculation in this round, not the scorecard: the scorecard only ran the reading applied.

**Not changed:** `reference.years_to_breast_height: 4` in the species file, used only by the height check inside stats.json, never by growth or the scorecard. A comment now says so.

### M1c. Parameter audit

Answer: the table is built (`reports/parameter_audit.csv`, 274 values; hand checks in `reports/parameter_checks.csv`). Sources were opened for 65 values, the rest say "not checked".

Not done: the sensitivity screen, which should have come first. It's blocked by memory, and the tool is ready (`tools/sensitivity_screen.py`; 160 runs, about 2.3 hours). So I chose which sources to check by their place in the carbon, light, wood and crown chains, not by measured influence. The "most influential first" order is still owed: when the screen runs, its top values get checked next if they aren't already.

| Status | Checked by opening a source | First pass from the file's own comment | Total |
|---|---|---|---|
| sourced | 12 | 29 | 41 |
| derived | 14 | 0 | 14 |
| borrowed | 18 | 0 | 18 |
| calibrated | 8 | 7 | 15 |
| VERIFY | 13 | 173 | 186 |

For the 65 checked: the page supports the value on 25, partly on 23, doesn't on 11, and 6 couldn't be checked (no source exists or the paper couldn't be reached). Species file changes are comments only; values unchanged, checked by loading the YAML before and after.

**What matters most** (the subagents' readings; I opened the first and the Aosaar and Elfving items myself; checker A hasn't run):

| Value | In the file | What the source says | Why it matters |
|---|---|---|---|
| `huber_path_exponent` pattern | Credited Mencuccini et al. 2019 | "Hv tend to remain relatively constant from twig to trunk base" (accepted manuscript p. 19). The opposite. | My citation, wrong. The option is off at the default stage 2, so no current run depends on it; corrected. |
| `woody_shade` k_wood 0.40 | On by default, cites 4 papers | No page read gives 0.40 for wood. The file's own `extinction_coefficient` comment says wood must cast no shade because k already holds it. | Possible double count, which would darken the stand. Needs Hagemeier & Leuschner 2019b, not reachable (decision 3). |
| `extinction_coefficient` 0.37; light target 6.4-19.8 % | Table 5 of the same paper | Not read: full text blocked. exp(−0.37 × 4.6) is 18.2 %, not the 14.8 % the comment sets beside it. | The light target's height and sky conditions aren't confirmed, so scoring it is provisional. |
| `apical_dominance` 0.62, `apical_control` 0.60, 0.50 | [P09], [BH84] | P09 illustrates 0.46-0.54, on synthetic trees. No birch value exists. | Calibrated, not sourced. Bears on the every-other-year pattern (M3). |
| `maintenance_per_internode` 0.5 | "LIGNUM carbon balance" | LIGNUM charges maintenance by tissue mass, summed over the tree (Perttunen 2008 thesis, Eq. 18), not per internode as resource flows. | Calibrated to a CUE; the attribution is too strong (M2). |
| SLA 15, used in alpha's derivation | Constant | 8-year-old stand (Uri 2007 abstract). 13.6 in southern Finland (Lintunen 2013, p. 28). Falls with age: 15 − 0.075 A (Rosenvald 2013): 11.25 at 50, 10.5 at 60. | M2. |
| CUE | 0.45 and 0.47 in the same file | No birch value. Boreal 0.42, temperate 0.48, deciduous broadleaf 0.50 (Collalti & Prentice 2019); falls with age (DeLucia 2007, abstract). | M2. |
| `psi_turgor_loss` −2.1 | No source | Mean −2.47 in B. pendula (Hannus et al. 2021). | Sets when shoots stop expanding. |
| `psi_stomata_open`, `_closed` −1.0, −2.0 | Sellin 2014 | "no threshold level"; at −2.10 stomatal conductance is still 25-32 % of pre-cut. | The closing curve is not what the paper shows. |
| `xylem_conductivity` 4.0 | Klepsch 2018, P50 | P50 is a different trait; no opened source gives 4.0. | Calibrated, not sourced. |
| `mechanics.wood_density` 850 | No source | Green density 0.887-1.032 g/cm³ (Tomczak 2021); ForestGALES 900. | Affects bending and the stress floor. |
| `stress_floor` MOR 57, `wind_load` MOR 63 | Both in the file | 57 is a yellow-birch ratio; 63 has independent support (Nykänen 1997 p. 198). | Two values for one property. |
| `pipe_model.exponent` 2.5 | "the brief asked" | 1.8-2.3 for many species (Eloy 2011, p. 1); no Betula. | Unsourced. |

**In the environment file, not the species file:** `diffuse_fraction` 0.5: May-Sep values of 0.46-0.48 at Stockholm, Norrköping, Karlstad and Borlänge (Persson 2000, SMHI RMK 89; broadband, subagent's calculation). Season 130-273: budburst at day 127-132, colouring at 272, but 50 % leaf fall at 289 (Swedish Forest Phenology data, doi:10.5878/jbab-cy46). Goes to M2b.

### M1d. Round 40 approvals

Answer: done, with one check outstanding.
- **Scorecard reads yearly light:** `tools/scorecard.py` now reads each age's value instead of a run-level value no run saves. Test added.
- **Diffuse-only output:** runs now save `subcanopy_diffuse_light_pct` per year: the light at 1.0-2.0 m with the sky alone, using the model's CIE overcast sky (`treegen/environment.py`, `treegen/light.py`). The scorecard scores only this, because the target measures diffuse light. A run with only the sky-and-sun value shows it in the notes as NOT APPLICABLE.
- **What that means today:** existing runs have no diffuse value, so the light target stays NOT APPLICABLE until a new run is made. p40_default_v3's sky-and-sun light was 30.1 % at 50 and 29.6 % at 60, against 6.4-19.8 %.
- **Fingerprint:** every run manifest now has a SHA-256 of uncommitted tracked changes and untracked files, and the list of those files. Test added.
- **Phase 33:** all three overclaims corrected in KNOWN_ISSUES.md, with the old wording quoted beside each.

Not done: proving growth is unchanged on a full run. A test shows the light field growth reads is identical with and without the diffuse output (`tests/test_run_outputs.py`); the full-run comparison against p40_default_v3 needs a model run.

### Renders

Not done: the seed-1 tree at 10, 30 and 60 needs a model run with full meshes.

## 4. Changes made

| Commit | What | Default | Before / after |
|---|---|---|---|
| `8ca5d46` | Knowledge base and extracts added, unchanged | - | - |
| `0e58497` | PROTOCOL.md section 6 and section 9 | - | Exactly as sent |
| `b222747`, `8ecfca3` | Height band uses T13 = 150/SIS | Target, preview | M1b tables |
| `b4b6df3`, `347d924` | Comments and citations in the species file | Values unchanged | - |
| `7d3db8e` | Diffuse-only light output | Output only | Test only |
| `be7c4ef` | Scorecard reads yearly diffuse light | Scorecard | Was never scored; still NOT APPLICABLE on old runs |
| `9cca522` | Manifest fingerprint | Output only | - |
| `7f2b285` | Phase 33 corrections | - | - |
| `871db5f`, `b6f0870`, `284a48e` | Audit tools and checks | - | - |

Also changed in a fixed folder: `tests/test_scorecard_targets.py`. The existing height-band test now reads T13 from the rule instead of a fixed 56 years of breast-height age, as it must once the target changes; it's no looser (same PASS and FAIL checks at the same margin). Tests were added, none removed. All 48 pass.

No option was adopted: nothing has gone through the adoption gate.

## 5. Target changes (pre-approval (a); not in use until checker A confirms and the tag moves)

| Target | Before | After |
|---|---|---|
| `site_index_curves` | fixed 4 years to breast height | T13 = 150/SIS (Elfving p. 56), per site index. Band in M1b |
| `lai_hagemeier.target_mean` (not scored) | 4.59 | 4.5, the mean of the two stands; no mean is printed |
| `lai_hagemeier.page_table` | "Figure 7 & Section 3.3 (p. 11)" | Section 3.2, p. 9; Figure 7, p. 11 |
| `managed_stand_empirical.page_table` | Table 2, p. 609 | Table 2, p. 608 |
| `foliage_biomass.page_table` | "Table 6 (p. 616, Eq. 12) & Appendix Table A6 (p. 622)" | Eq. 12, p. 612, Table 4, p. 613, valid only for DBH 11-26 cm, N = 21 (p. 617); Eq. A6, p. 621, Table A1, p. 623 |
| `wood_basic_density` | "Table 4 (p. 9)", a wrong paper title, "basic density" | Section 3.1, p. 7, the right title, "stemwood density" (the paper doesn't say basic) |
| `carbon_fraction` | "Table 1 (p. 336)", "48.0 % ± 1.2 %" | Table 2, p. 337, 48.8 ± 0.6 % observed, 48 ± 2 % IPCC. Value stays 0.48 |

No range the scorecard reads changed, other than the height band.

## 6. Checker results

Not done: the three checkers haven't run. They review a finished milestone, and the screen and renders are missing. Running them twice would cost about 600,000 tokens more, going by the research subagents' use. So the tag hasn't moved, and every source reading above that I didn't open myself is a subagent's report until checker A re-opens it.

## 7. Corrections to earlier reports
- **Distance rule, my error (KNOWN_ISSUES.md:177, :297; species comment).** I credited its pattern to Mencuccini et al. 2019. The paper says the Huber value stays about constant from twig to trunk. Corrected. The value is a calibration on Konôpka and Repola; the only birch support for the pattern is within the crown (Sellin & Kupper 2006, abstract). It isn't active at the default stage.
- **Species comment "In use (phase 30)"** on that option was stale: stage 2 switches it off. Corrected.
- **Phase 33:** three overclaims corrected (M1d).
- **Knowledge base:** "no traceable source" for alpha goes too far (M1a); "about 5.8 at SI 26" treats two site-index scales as one (M1b). The file stays as supplied, as asked.
- **Commit `284a48e`:** its message says it applied the source corrections, but it held only the checks table, because my script stopped before changing anything. `347d924` holds the changes and says so. History left as it is.
- **While writing the corrections** I first wrote volume and page numbers for two papers that no opened source gave me. I replaced them with DOIs before committing.

## 8. Decisions for the maintainer

1. **Memory: this blocks everything.** One 16 GB stick, 15.9 GB visible, 4.5-6.4 GB free over the last day. The rule needs 8.65 GB free for a seed-1 tree run, and 11.8-13 GB for a natural plot (recent plots peaked at 3.8-5.0 GB: `out/bench/p38_nat`, `out/bench/p33_nat`). M4's natural density and M5's 200-year run may not fit on 16 GB under any option; they'd use the largest plot that fits.
   - (a) **Set the floor to 4 GB while on one stick, one heavy run at a time.** That's a quarter of the RAM, as 8 GB is of 32. Tree runs can start right away; a plot needs 7.8-9 GB free, so some apps closed. **Recommended.**
   - (b) Keep 8 GB and close other apps (about 5.5 GB by the counts in CAMPAIGN.md). That should reach about 11 GB: enough for tree runs, not for a plot, and they'd have to stay closed for hours. M4-M6 would stay blocked.
   - (c) Get the second stick working. The rule as written then fits.

   Whichever you pick, section 6 says "32 GB machine", which isn't true today. Changing it is yours to approve.
2. **Which site index goes into T13 = 150/SIS?**
   - (a) This curve's own height at total age 100 (applied). It keeps Elfving's definition of SIS as top height at age 100, though with birch in place of the site-indicative species. **Recommended.**
   - (b) The band's own site index (your brief's and the knowledge base's reading). Simpler, but it puts a height at breast-height age 50 where the source has a height at age 100. Two more verdicts go to FAIL.
3. **Please save one PDF:** Hagemeier & Leuschner 2019, https://www.mdpi.com/1999-4907/10/10/925 (open access; the site blocks automated downloads, and copies elsewhere were refused by the permission system, so I stopped there). Put it in `birch-data\`. It settles whether woody shade double-counts wood, and whether the light target compares like with like. M2 and M3 also want Ilomäki et al. 2003 and Perttunen et al. 1996 if you can get them; full list in `reports/research_notes.md`.
4. **A copy from a third-party site.** A research subagent read parts of Borchert & Honda 1984 from a JSTOR scan on a university site, and two others (Hale et al. 2015, a Tokyo thesis abstract) through web archive copies, before the block in decision 3. They're outside the repo: `scratchpad\research_crown\bh84\bh84.pdf`, `scratchpad\research_wood\`.
   - (a) Delete those copies and treat the rows that rely on them as unread until you supply a copy. **Recommended,** at least for the JSTOR scan.
   - (b) Keep them.
5. **`round41_research_pack.md`** isn't on this PC. Not blocking: I read Repola directly. If you have it, put it in `reports/` and say so.
