# Validation design: tests nobody tuned against, and claims that match the evidence

Model: Fable 5.2, ID `claude-fable-5-2`. Written 2026-11-11. A design only: no target, scorecard, README or code was changed, and no model was run.

**What I read.** The review, the fresh run report, PROTOCOL, DECISIONS 90-108, KNOWN_ISSUES (birch v1), Q40, `targets.yaml`, `labels.yaml`, the species file, `independent_checks.py`, `scorecard.py`, `thinning.py`, parts of `plot.py` and `growth.py`, both READMEs.

**Saved runs read.** 20 plots `node_cd2_C` + `node_cd2_C2` (natural, 1,000 m², to 60; they reproduce the fresh run's figures at 30, 50 and 60) and 20 stand trees `node_f5_trees`. My reading scripts are in `<scratchpad>\val` (`plots.py`, `more.py`, `trees.py`, `causes.py`, `labels_cover.py`).

**Sources.**
- Opened by me today at the publisher: Aosaar 2016, Repola 2008, Varik 2009, Dahlgren Lidman 2021, Hynynen & Niemistö 2009.
- Opened by the 2026-11-09 sources job, not reopened: Hagemeier 2019a/b, Jones 2021 and 2023, Zeltins 2018, Fedorov 2024.
- Could not open, so UNVERIFIED: Oikarinen 1983 (Luke's repository shows a bot check), Fries 1964 (the SLU link now lands on the front page), Uri 2012 (ScienceDirect CAPTCHA; a co-author's thesis site refused the connection), Siipilehto & Kangas 2015 (not tried beyond a search), and the paywalled Johansson 1996, Niemistö 1995, Eriksson 1997, Hynynen 2010.

CONFIRMED means I checked it in code or saved data. SUSPECTED means I didn't.

## Summary

1. `targets.yaml` holds 18 targets. Five are scored on default runs: height (by design), two leaf-area bands and light (tuned, and one result), and young crown ratio by age (independent, fails). **No independent scored target even applies at 50 or 60.** CONFIRMED.
2. **Two rows reported as "independent" are not.** A default value was tuned against Repola's branch wood (`species/betula_pendula.yaml:652-654`). Stem wood against Repola was on the table when an earlier crown value was chosen (`:1826-1829`). CONFIRMED.
3. **The labels file doesn't cover the species file.** 381 of 812 values have a label. Leaving out on/off switches and the 312 look settings, 58 values have none, and 37 of those say TUNED in their own comment. CONFIRMED.
4. **New evidence, opened today.** An unthinned Swedish natural birch stand on a site like the model's has 4 times the model's stems at 30 and 1.4 times its basal area at 42. The model's stocking ceiling, tuned on one Estonian stand, sits under three other stands.
5. **Leaves.** By leaf mass the model's forests are inside measurements from age 20 (2.25-2.94 t/ha against 2.1-3.7). By leaf area they are over: the model has 19-20 m² of leaf per kg, against a measured 12.7-15.1.
6. **The 5-7 m young-crown reading flatters the model.** On the leading trees, which the source describes, plots read 2.6 m at top height 13.3 m and 5.0 m at 15.6 m.
7. Twelve public claims and eleven on master say more than the evidence. Corrected wording is in section 4.

## 1. Every target and its kind today

`targets.yaml` has no "kind" field. Kinds live in reports and in `independent_checks.py`. Plots unless said; "st" is stand trees.

| Target (key) | Scored? | Kind today | Why | Model at 50 / 60 |
|---|---|---|---|---|
| `lai_baltic_chronosequence` 2.5-4.5 | yes | **tuned against** | `stem_theory.wind_speed_m_s` set "against Dg, stems and LAI on plots"; tied to light by k | 4.51 (fail by 0.01) / 4.29 |
| `lai_hagemeier` 3.6-5.4 | yes | **tuned against** | the same; k 0.37 comes from the same two stands | 4.51 / 4.29 |
| `subcanopy_light_transmittance` 6.4-19.8, median 14.8 | yes | **tuned against** | three labelled values (`short_shoot_light`, `short_shoot_survival_light`, `light_per_leaf_threshold`) and two unlabelled (`shade_softness`, `spacing_overlap`) | 18.2 / 19.5 |
| `site_index_curves` SI 20-26 | yes | **by design** | the height driver; held by the curve in 1,200 of 1,200 stand-tree years | 21.39 / 23.14; st 21.90 / 23.73 |
| `dense_unmanaged_stand` 0.30-0.45, ages 11-22 | yes | **independent**, fails | nothing was set against it; source unopened; planted trials labelled natural | not applicable (0.94, 0.97, 0.87, 0.82 at 11, 15, 20, 22) |
| `stand_density` 880 at 45, 420 at 67 | INFO | **tuned against** | `wind_speed_m_s`; `mortality.shape` "near Hagemeier"; quoted when fix C was adopted | 667 / 474 (846 at 45) |
| `managed_stand_empirical` 0.58 ± 0.14 | INFO | **seen** | quoted as the yardstick when crown fix C was adopted (DECISIONS 107) | 0.47 / 0.42; st 0.52 / 0.46 |
| `silvicultural_recommendation` ≥ 0.50 | INFO | not a measurement | a guideline; crown length was tuned by eye (`af_zero`) | as the row above |
| `foliage_biomass` Repola Eq. 12, A6 | INFO | **independent** in effect | the two values fitted to Eq. 12 aren't in use | A6: 0.89 / 1.02 of Repola; Eq. 12: 0.65 / 0.59 |
| `dominant_height_invariance` | INFO | **by design** | height comes from the curve at any density | - |
| `crown_width_open_grown` (Hemery) | INFO | **by design** | `crown_frame.crown_a/b` cap the crown; its DOI is wrong | - |
| `bark_thickness`, `wood_basic_density`, `carbon_fraction`, `critical_turning_moment`, `field_layer` | INFO | **inputs** | the model takes them as given | - |
| `natural_clearcut_heights` | needs the field layer on | by design (SUSPECTED) | the height driver | not run |
| `seedling_root_shoot_ratio` 0.25-0.50 | seedling runs only | independent | no label names it; the band is worked out, not printed | not run |

**Has an "independent" row been tuned to?** Yes, three, all CONFIRMED in the files:
- **Branch wood over Repola.** `independent_checks.py:77-78` says "no value was set against it". The species file says `branch_sapwood_senescence: 0.30` is "TUNED, against Repola's branch wood". It has no label. The row is tuned against, and still 26-33 % over.
- **Stem wood over Repola.** `twig_bud_every` was "TUNED, against crown ratio and stem wood". Today's defaults don't read that value, so the row is "seen", not clean.
- **Repola's crown ratio 0.58.** DECISIONS 107 reports crown fix C against it.

Diameter spread and height spread are independent: `plot.vigour_sd` is labelled a guess, set against nothing.

## 2. The independent tests the model should face

Model figures are means of 20 plots unless said. "My arithmetic" marks anything I worked out from a table.

### Forests

| # | Test | Published number and its conditions | Source; opened? | Model at the matching point | Model at 50 / 60 | Kind |
|---|---|---|---|---|---|---|
| F1 | Stems/ha at 30, unthinned, self-sown, similar site | birch 10,642-11,425/ha, mean diameter 5.2-5.7 cm, basal area 22.9-27.1 m², dominant height 13.8-14.8 m; 2 Swedish sites, spruce underneath | Dahlgren Lidman et al. 2021, Silva Fennica 55(4):10485, Table 1; OPENED | age 30: 2,640/ha, 9.6 cm, 18.9 m², top height 15.6 m | 667 / 474 (source ends at 42) | independent |
| F2 | Basal area at 42, the same stands' unthinned control | birch 31.4 m² (SD 2), mean diameter 9.5 cm, leading trees 17.4 cm; about 4,400 birch/ha (my arithmetic) | same, Table 5; OPENED | age 42: 23.0 m², 17.3 cm, 984/ha | 24.7 / 26.8 m² | independent |
| F3 | Stocking ceiling, on the model's own density index | 848 (Varik, 32 y), 949-1,022 (F1), 956 (F2). The model's ceiling 763 was tuned on Aosaar | my arithmetic from the tables | peak 664 at age 28 | 561 / 547 | independent |
| F4 | Structure by height, Estonian natural stands on a faster site | at mean height 11.5 m: 1,350/ha, 10.6 m²; at 17.0 m: 3,208/ha, 29.2 m²; at 25.6 m: 941/ha, 29.8 m² (ages 14, 32, 45) | Varik, Aosaar & Uri 2009, Forestry Studies 51:5-16, Table 1 p. 7; OPENED | at 11.5 m (age 26): 4,586/ha, 16.5 m²; at 17.0 m (age 39): 1,196/ha, 22.5 m² | mean height 20.0 / 21.9 m; 25.6 m not reached | independent |
| F5 | Stems and basal area by height, Aosaar's stand | at 6.6 m: 11,633/ha, 11.3 m²; 9.3 m: 9,500, 16.6; 13.2 m: 4,233, 20.7; 16.0 m: 2,733, 20.9 | Aosaar et al. 2016, Silva Fennica 50(4):1628, Table 3; OPENED | 12,741, 11.4; 7,768, 14.3; 2,925, 18.4; 1,482, 21.5 (ages 17, 22, 29, 36) | - | **tuned against** |
| F6 | Diameter spread, SD over mean | 0.30 at 15 and 0.25, 0.28 at 19 (planted trials); 0.32 at 45; 0.12 at 67 | Jones 2023 Table 1; Jones 2021 Table 2; Hagemeier 2019a Table 3; opened 11-09 | 0.24 at 15; 0.16 at 20; 0.14 at 45 | 0.15 / 0.15 | independent |
| F7 | Height spread, SD | 3 m at 45; 3 m at 67 | Hagemeier 2019a Table 3; opened 11-09 | 1.04 m at 45 | 1.06 / 1.09 m | independent |
| F8 | Mean height at mean diameter | 19 cm, 20 m (45 y); 25 cm, 25 m (67 y); 17.7 cm, 17.2 m (24 Finnish stands) | Hagemeier Table 3; Repola 2008 Table 1 p. 607, OPENED | 18.8 cm, 18.9 m at 45 | 21.5 cm, 20.0 m / 26.6 cm, 21.9 m | partly: height is by design |
| F9 | Height-diameter curve (Näslund) | Finnish birch parameters | Siipilehto & Kangas 2015, Metsätieteen aikakauskirja; UNVERIFIED | model's own fit at 45: a 0.79, b 0.196 | a 0.84, b 0.192 / a 0.94, b 0.185 | partly |
| F10 | Crown ratio by age, unthinned natural | 0.50 ± 0.07 at 33; 0.42 (SD 0.03) at 42; crown length 6.1 m | Dahlgren Lidman 2021, Results 3.1, Tables 4-5; OPENED | 0.57 at 33; 0.51 at 42; crown length 9.3 m | 0.47 / 0.42 | independent |
| F11 | Stand leaf mass, t/ha | 2.1-3.7 at 8-13 y; 2.46, 3.05, 2.12 at 14, 32, 45 | Aosaar Table 3; Varik Table 5 p. 13; OPENED | 2.75 at 20; 2.94 at 25; 2.65 at 30; 2.40 at 45 | 2.32 / 2.25 | partly: tied to leaf area |
| F12 | Leaf area per kg of leaf, m²/kg | 13.4, 15.1, 12.7 at 14, 32, 45 | Varik Table 5; OPENED | 18.6 at 20; 20.5 at 30; 19.7 at 45 | 19.4 / 19.1 | independent |
| F13 | Branch wood over stem wood, whole stand | 0.14 at 11 y, 0.11 at 17 (dense); 0.24, 0.08, 0.08 at 14, 32, 45 (my arithmetic; bark on branches) | Aosaar Table 3; Varik Table 4 p. 11; OPENED | not saved for plots; stand trees 0.34 at 20, 0.30 at 30 | st 0.26 / 0.26 | independent |
| F14 | Total stem volume grown, unthinned | 315 m³/ha at 42, dead trees counted | Dahlgren Lidman Table 4; OPENED | not comparable: dead trees' volume isn't saved | standing only, roughly 228 / 259 m³/ha | independent |
| F15 | Volume and basal area by age and site, yield table | - | Oikarinen 1983 (planted), Fries 1964, Koivisto 1959; UNVERIFIED | - | - | would be independent |
| F16 | A 60-year natural stand; old stands to 111 y | 8 stands aged 6-60; 6 plots remeasured | Uri 2012 Tables 1, 4; Starikova 2025; UNVERIFIED by me | - | - | would be independent |
| F17 | Light under the canopy, Nordic | relative light against density, stands of 20-40 y | Johansson 1996, Trees 10:223; UNVERIFIED, paywalled | 15.9 % at 20; 16.0 at 30; 17.5 at 40 | 18.2 / 19.5 % | would be independent |

F14's model figure uses a published volume formula known here only second-hand (`KNOWN_ISSUES.md:1715`).

### Trees

| # | Test | Published number and its conditions | Source; opened? | Model at the matching point | Model at 50 / 60 | Kind |
|---|---|---|---|---|---|---|
| T1 | Lowest live branch at first thinning | 5-7 m when dominant height is 13-15 m; planted at 1,600/ha; the leading trees | Hynynen & Niemistö 2009, waldwissen.net; OPENED. A guide; it cites no measurements | stand trees: 0.89 m, 0 of 20 inside. Plots' 100 thickest/ha: 2.56 m at top height 13.3 m (age 25), 5.00 m at 15.6 m (age 30) | plots 10.4 / 12.5 m | stand trees independent; plots **tuned against** |
| T2 | Lowest live branch on big planted trees | 11.2 m on trees 26.2 m tall, 27.7 cm, 400/ha, age 40 | Zeltins 2018 Table 1; opened 11-09 | plot trees 23-26 m tall: 12.4 m at 31.8 cm | st 10.3 / 12.6 m | independent |
| T3 | Crown ratio by tree size | 0.58 ± 0.14 at mean height 17.1 m; 127 trees, 24 stands | Repola 2008 Table 2 p. 608; OPENED | plot trees 15-19 m tall: 0.55-0.51; stand trees 0.68 | 0.47 / 0.42 | seen |
| T4 | Foliage per tree, from diameter and crown ratio | Eq. A6; a stand's mean within ×0.81-1.23 (twice the between-stand SD); diameters 11-26 cm only | Repola Table A1 p. 623 and p. 617; OPENED | 0.58 at 30; 0.73 at 40 | 0.89 / 1.02 | independent |
| T5 | Foliage per tree, from diameter alone | Eq. 12; no between-stand spread printed | Repola Table 4 p. 613; OPENED | 1.14 at 30; 0.77 at 40 | 0.65 / 0.59 | independent, INFO |
| T6 | Stem wood per tree at its own size | Eq. 7; ×0.90-1.11 | Repola Table 4; OPENED | stand trees 0.86 at 20; 0.75 at 30; 0.86 at 40 | 0.96 / 1.03 | seen |
| T7 | Branch wood per tree | Eq. 9; ×0.72-1.39; Repola's branches include bark (p. 608) | Repola Table 4; OPENED | stand trees 1.64 at 20; 1.41 at 30; 1.55 at 40 | 1.26 / 1.33 | **tuned against** |

### What these rows say

- **Too little stocking (F1-F3).** At the same age and nearly the same top height, the real unthinned stand has 4 times the stems. Its basal area at 42 is 31.4 m² against the model's 23.0. Three stands the model was never set against carry a density index of 848-1,022; the model never passes 664.
- **Too even (F6, F7): the evidence is thinner than the reports say.** Diameter spread is low at 20 and 45. At 60 the only stand nearby (67 years) reads 0.12, under the model's 0.15, so the diameter claim isn't shown at 60. Height spread rests on two stands, both 3 m.
- **Leaves (F11, F12).** Leaf mass is inside the measured range; leaf area per kg is about 35-50 % over the three stands' mean of 13.7. The stats count every leaf at 15 cm² (`growth.py:3161`, `plot.py:595`). CONFIRMED numbers; the cause is SUSPECTED.
- **Crowns (F10, T2).** Model crowns are longer than a dense natural stand's at 42, though its stand is far sparser, and shorter than wide-planted trees' at 40-60. SUSPECTED: crown length answers to density too weakly.
- **Branch wood (T7, F13).** 26-33 % over Repola's line is inside Repola's own stand-to-stand spread, but Repola's figure includes bark and the model's doesn't, so the real gap is wider. The whole-stand ratio is the cleaner test: stand trees carry 0.26-0.34 of their stem wood as branches, against 0.08-0.24 measured. Stand trees are thinned to 450/ha, sparser than all but one of those stands.
- **At 50 and 60 the opened record is thin.** Only Repola's equations and Hagemeier's two stands reach those ages. The yield tables and Uri's 60-year stand are the first sources to open.

**What runs must save to score these:** each plot tree's stem and branch wood and stem volume; the volume of trees that die each year; a tree list for every year top height is 12-16 m; what thinning removes from stand trees.

## 3. Q40 written as proper targets

The by-age band stays scored until the maintainer approves anything else. By age it reads:

| | 11 | 15 | 20 | 22 | 50 | 60 |
|---|---|---|---|---|---|---|
| Crown ratio, 20 plots | 0.94 | 0.97 | 0.87 | 0.82 | 0.47 | 0.42 |
| Approved band 0.30-0.45 (Niemistö 1995, unopened) | FAIL | FAIL | FAIL | FAIL | does not apply | does not apply |

Proposed entries, none in use:

| Proposed key | What is measured, and how it is matched | Band | Source and its conditions | Run it holds for | Kind | Model now | Proposed scoring |
|---|---|---|---|---|---|---|---|
| A `clear_stem_at_first_thinning` | lowest live branch of the 100 thickest/ha, in the years top height is 13-15 m | 5-7 m | Hynynen & Niemistö 2009: planted, 1,600/ha, before the first thinning; a guide with no data table | stand trees, or a plot planted at 1,600/ha (none saved) | independent for those | stand trees 0.89 m | INFO until a measured source is opened. Scored today it would FAIL |
| A on natural plots | the same | 5-7 m | not the source's conditions: the plots hold 5,078-2,640/ha | natural plots | tuned against (it chose crown fix C) | 2.6 m to 5.0 m | reported only, never a pass |
| B crown ratio 0.55-0.6 at 15 m | - | - | A's figure turned into a ratio | - | - | - | drop |
| C `natural_by_height` | stems/ha and basal area the year mean height reaches 9.3, 13.2, 16.0 m | Aosaar's rows | Aosaar Table 3: one stand on old farmland, 0.03 ha | natural plots | tuned against | 82 %, 69 %, 54 % of its stems | reported only |
| D `leaf_mass_by_height` | stand leaf mass at mean height 6.6-17 m | 2.1-3.7 t/ha | Aosaar Table 3, Varik Table 5: 9 stand-years | natural plots | partly | 2.65-2.94 | reported only |
| E `natural_unthinned_by_age` (new) | crown ratio of all birch, at 33 and 42 | 0.36-0.64 at 33; 0.36-0.48 at 42 (mean ± 2 SD) | Dahlgren Lidman 2021: self-sown, unthinned, top height within 2 m of the model's at 30 | natural plots | independent | 0.57; 0.51 | scored: in band at 33, FAIL at 42 |

**Matching rule for all of these.** Compare by age only when the run's top height at that age is within 2 m of the source's. Otherwise compare by height and print both. If the run's stems/ha is outside the source's range, the row says "density not matched" and is INFO.

DECISIONS 105 says stems matched by height are "close to Aosaar's from about 8.5 m". Today that is 91 % at 8.5 m and falls to 54 % at 16 m.

## 4. Claims that say more than the evidence

### Public front page (`cambium-publish/overlay/README.md`)

| Line | Claim | What the evidence says | Corrected wording |
|---|---|---|---|
| 7, 150 | "Trees that grow themselves"; "a self-organising tree growth model" | Height came from the curve in 1,200 of 1,200 stand-tree years. Main limbs' number, angle and furthest reach come from published data | "Trees grown year by year from a seed"; "a tree growth model guided by published growth curves" |
| 31-33 | "built from what the tree can afford" | Carbon doesn't set height | "Height follows a published growth curve. Within it, buds compete for light, and wood, leaves and roots are paid for from the carbon the tree fixes." |
| 33 | "thin each other out" | 22,969 of 31,052 deaths in the 20 plots are a stand-density rule tuned on one stand; 1 is the carbon upkeep rule (`plot.py:456-467`) | "they shade each other, and a crowding rule fitted to a measured stand thins them" |
| 61 | "Shape comes from light, carbon and mechanics, not presets." | See line 7 | "Height and the main limbs' number, angle and reach follow published measurements. Light, carbon and mechanics decide the rest." |
| 73 | "anchors the tree against wind" | The anchorage figure is a line through two site averages | "with an anchorage figure from pulling tests at two sites" |
| 78 | "the tree's whole growth history" | Births, deaths and thickness yearly; positions every 5 years | "its growth history: births, deaths and thickness by year, positions every 5 years" |
| 121 | "Every setting in the birch says where it came from" | 381 of 812 values are labelled: 92 sourced, 21 worked out, 56 tuned, 212 estimates | "Each labelled setting says if it is sourced, worked out, tuned or still an estimate. About 3 in 10 rest on a published source; over half are estimates. The look settings and about 60 model values aren't labelled yet." |
| 122 | "compared with measured Nordic and Baltic birch stands" | The bands the forests sit inside come from two German stands. The Baltic band fails at 30 and 50 | "compared with measured stands in Germany, Estonia, Finland and Sweden" |
| 122-123 | "By 50-60 years they're close to the published figures for height, stem wood and the light under the canopy." | Height is by design. Light is tuned. Stem wood was measured on single trees, not forests, and is 0.75 of Repola at 30 | "At 50 and 60: height sits on the published curve because the model follows it. Light under the canopy is 18.2 and 19.5 % against a measured 6.4-19.8 % (median 14.8 %), after tuning. A single forest-grown tree's stem wood is within 5 % of Finnish equations. No test the model wasn't tuned against passes yet at 50 or 60." |
| 123 | link to `birch_v1_final.md` | That report describes v1's settings | link the fresh run report |
| 126-127 | "young crowns now match real stands of the same height (5.4 m on 14 m trees; real: 5-7 m)" | Section 3, rows A | "After a tuning step, stems 13-15 m tall have their lowest living branch at about 5.4 m. A Finnish guide gives 5-7 m for the leading trees of planted stands; the model's leading trees read 2.6-5.0 m, and single stand-grown trees 0.9 m." |
| 128 | "branch wood is about 30 % over published equations" | True, and a value was tuned against them | add "even after tuning" |

Missing from its Status: young crown ratio by age still fails (0.82-0.97 against 0.30-0.45); the Baltic leaf-area band fails at 30 and 50; forests carry less basal area than unthinned real stands.

### `README.md` on master

| Line | Claim | What the evidence says | Corrected wording |
|---|---|---|---|
| 1 | "treegen: procedural tree generator core" | The public name is Cambium | retitle |
| 9, 14 | "install it with pip", `pip install pycambium` | Not on PyPI today (404, checked 2026-11-11) | "`pip install .` from a clone; PyPI is coming" |
| 50 | "every species parameter; each is labelled" | 381 of 812 | as the public line 121 |
| 95 | "ForestGALES-style regression on silver-birch pulling tests" | A line through two site averages (Q35) | say that |
| 104 | "The core follows Palubicki et al. (2009)", then 8 steps | The steps leave out the height curve, the crown frame, damage and the crowding rule | add them as steps |
| 106 | "below the 21 % at which birch shade leaves die" | The model uses 15 %, tuned against light; the labels say it no longer follows its source | "below 15 % light, a tuned value; the source gives 21 %" |
| 108 | carbon use efficiency "comes out near the published 0.47" | `maintenance_per_internode` is tuned against 0.47 | "is tuned to" |
| 120 | "at the measured 43°" | Measured on grafted clones; the source doesn't define the angle | add that |
| 126 | "the extinction coefficient measured in closed birch stands (0.37)" | Wood shade is added on top, which counts wood twice (label, `light.woody_shade`) | add that |
| 132 | "a heritable growth factor" | A random draw, SD 0.06, a guess, that multiplies each tree's yearly height step (`plot.py:131`, `growth.py:2523-2529`) | say that |
| 136 | "`natural` never thins. A tree dies when its own carbon no longer pays" | 1 death in 31,052 by that rule; 74 % by the crowding rule | "trees die by a crowding rule, suppression, background loss, snow, wind and age" |

Also: Q40's "plot trees pass the 5-7 m check" is a pass written by hand on an unapproved, tuned row. `cambium/__init__.py:15` says "the same bits on every machine"; `pyproject.toml:14` promises less.

## 5. Scorecard layout and the pass rule

Three blocks, always in this order, each with its own words. Only block C can say PASS.

```
Independent rows that apply:  age 50: 0    age 60: 0        Independent passes:  0 of 0

A. BY DESIGN - the model follows these. They show the machinery holds, nothing more.
| Row                      | Source (stands)             |    50 |    60 | Reads                 |
| Top height, plots, m     | Eriksson 1997, SI 20-26     | 21.39 | 23.14 | HELD (by design)      |

B. TUNED AGAINST - a value was set with this figure on the table. Inside is expected.
| Row                      | Source (stands)   | Values set   |   50 |   60 | Reads                      |
| Leaf area, 3.6-5.4       | Hagemeier (2)     | wind_speed   | 4.51 | 4.29 | IN BAND (tuned)            |
| Leaf area, 2.5-4.5       | Varik (3)         | wind_speed   | 4.51 | 4.29 | FAIL / IN BAND (tuned)     |
| Light, 6.4-19.8 %        | Hagemeier (2)     | 5 values     | 18.2 | 19.5 | IN BAND (tuned), +3.4 +4.7 |
| Branch wood over Repola  | Repola (24)       | branch_sap.. | 1.26 | 1.33 | IN BAND (tuned), no bark   |

C. INDEPENDENT - nobody set a value against these.
| Row                      | Source (stands)   | Matched on   |   50 |   60 | Reads                      |
| Crown ratio, 0.30-0.45   | Niemistö (unopened) | age 11-22  |    - |    - | FAIL at 11, 15, 20, 22     |
| Diameter spread          | Hagemeier (1 + 1) | age 45, 67   | 0.15 | 0.15 | INFO, one stand per age    |
| Height spread, m         | Hagemeier (2)     | age 45, 67   | 1.06 | 1.09 | INFO, two stands: 3 and 3  |
```

**A row may be called PASS only when all of these hold:**
1. **Independent.** No species value was ever set, chosen or kept with this figure on the table, nor a figure tied to it by a formula inside the model (light and leaf area; stems, diameter and basal area).
2. **Approved and opened.** It is in the approved `targets.yaml`, with page or table, read at an allowed place.
3. **Matched.** Species, natural or planted, density and site agree with the source by the matching rule in section 3. If not, INFO.
4. **A band with a stated basis.** One of: three or more stands (lowest to highest, or mean ± 2 SD); a published SD between stands; an equation's own between-stand spread. One or two stands with no spread is INFO. The row prints how many stands stand behind it.
5. **20 runs on the shipped defaults at one commit.** The mean is inside the band, with the share of runs inside printed beside it.
6. **Frozen first.** The band was approved before the run. Once a row is used to choose a fix it moves to block B for good, with a DECISIONS line.
7. **Written by the scorecard**, never by hand.

In blocks A and B an inside row reads HELD or IN BAND (tuned). A row outside its band reads FAIL in every block, so nothing is loosened.

**Two pools of independent rows.** Rows that may guide fixes will become tuned: F1-F3, F6 at 15-20, F10, F13. Rows held back and read only at a release: F4, F7, T2, T4, F12, and F15-F17 once opened.

**File changes this needs, proposals only:** `targets.yaml` gains `kind`, `values_set`, `tied_to`, `band_basis`, `stands` and `match_on` per target. `labels.yaml` gains `against_targets` and the 58 missing labels. `scorecard.py` prints the three blocks from those fields. `independent_checks.py` corrects two kinds.

## 6. Decisions for the maintainer

1. Approve the three kinds and the pass rule?
2. Q40: A as INFO until a measured source is read; drop B; C and D reported; E scored. The age band stays scored. This is my recommendation.
3. Count stem wood over Repola as tuned? I recommend yes: it was watched while choosing a value.
4. Foliage: score A6 and show Eq. 12 as INFO? Note that I saw the result (0.89, 1.02) before proposing the band.
5. Which rows are held back from tuning.
6. Sources to open in Chrome: Oikarinen 1983, Fries 1964, Uri 2012, Siipilehto & Kangas 2015, Johansson 1996, Niemistö 1995a.

## 7. What I did not check

- Repola's and Varik's numbers I read in the publishers' own PDFs. Aosaar's, Dahlgren Lidman's and the Finnish guide's were read through a page summariser; I asked for Dahlgren Lidman's twice. Its Table 4 and Table 5 volumes disagree (315 against 257 m³/ha), so the volume row is weaker than the others. I didn't check whether its "±" is an SD or a standard error, which changes row E's band.
- The stand's density at 42 in F2 and the density indexes in F3 are my arithmetic, not printed figures. Varik's index uses a plain mean diameter, so it is a low reading.
- I didn't run the scorecard or any model. Figures at 33 and 42 for crowns lie between two tree lists.
- I didn't check the hero pictures, the season rule or the bark claims on the public page.
- The fetch tool kept the two publisher PDFs in this session's own tool-results folder, outside the repository. Nothing was added to the repository but this file.

## Appendix: the 20 saved plots by age

Means of `node_cd2_C` and `node_cd2_C2`. Top height is the approved definition; the stand's own measure reads 0.1-0.4 m higher. Crown ratio and lowest live branch are over all stems past 1.3 m.

| Age | Stems/ha | Basal area m²/ha | Dg cm | Top height m | Diameter spread | Height SD m | Crown ratio | Lowest live branch m | LAI | Light % | Leaf mass t/ha |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 13,737 | 2.3 | 1.5 | 4.15 | 0.53 | 0.66 | 0.94 | 0.18 | 1.27 | 87.6 | 0.80 |
| 15 | 13,220 | 8.4 | 2.8 | 7.14 | 0.24 | 0.73 | 0.97 | 0.18 | 3.65 | 47.3 | 2.00 |
| 20 | 9,324 | 13.5 | 4.3 | 10.41 | 0.16 | 0.78 | 0.87 | 1.02 | 5.12 | 15.9 | 2.75 |
| 22 | 7,319 | 14.5 | 5.0 | 11.51 | 0.15 | 0.79 | 0.82 | 1.58 | 5.27 | 14.6 | 2.81 |
| 25 | 5,078 | 16.0 | 6.3 | 13.05 | 0.13 | 0.82 | 0.72 | 2.93 | 5.59 | 13.4 | 2.94 |
| 30 | 2,640 | 18.9 | 9.6 | 15.21 | 0.13 | 0.85 | 0.60 | 5.26 | 5.44 | 16.0 | 2.65 |
| 35 | 1,620 | 21.1 | 12.9 | 17.15 | 0.14 | 0.90 | 0.55 | 6.76 | 5.05 | 16.9 | 2.50 |
| 40 | 1,122 | 22.7 | 16.1 | 18.84 | 0.14 | 0.95 | 0.52 | 8.08 | 4.85 | 17.5 | 2.43 |
| 45 | 846 | 24.0 | 19.0 | 20.31 | 0.14 | 1.04 | 0.50 | 9.17 | 4.72 | 17.7 | 2.40 |
| 50 | 667 | 24.7 | 21.7 | 21.39 | 0.15 | 1.06 | 0.47 | 10.36 | 4.51 | 18.2 | 2.32 |
| 60 | 474 | 26.8 | 26.8 | 23.14 | 0.15 | 1.09 | 0.42 | 12.46 | 4.29 | 19.5 | 2.25 |

Where the opened sources are: Aosaar `silvafennica.fi/article/1628`; Repola `silvafennica.fi/pdf/236`; Varik `reference-global.com`, DOI 10.2478/v10132-011-0073-y; Dahlgren Lidman `silvafennica.fi/article/10485`; the guide at `waldwissen.net`, "Silviculture of silver birch in Finland".
