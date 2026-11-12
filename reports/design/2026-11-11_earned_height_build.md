# Earned height: the build (plan step E)

2026-11-11. Builder: Opus 5.5 (ID `claude-opus-5-5`). Branch `earned-height` from master 10ebc32. Plan: `reports/design/2026-11-11_plan.md`, step E. Design: `2026-11-11_earned_size.md`, its challenge, and the plan's section 1 row "Earned size". New since the plan: `reports/sources_opened_2026-11-11.md` item 1 (Hynynen et al. 2002 opened). Owner's decisions: DECISIONS 110-111.

CONFIRMED = I checked it in code, in the paper's text or in saved data today. SUSPECTED = not checked. No arm has been run. Section 5 was written before any arm ran.

## In short

1. One switch, `plot.height_status.enabled`, off by default. Off, nothing is set and nothing changes: the full tests, the golden runs and the switch-off rule all agree on the server (section 7).
2. On, a plot tree's yearly height step is the curve's step at its own age × light × water × its **status**. Its random draw no longer multiplies its height. It stays in its carbon at 0.06 (DECISIONS 111, item 10).
3. Status is a published rule of the tree's diameter against the dominants' diameter, divided by the dominants' mean, so the dominants keep the curve's step.
4. There are two rules. `pine_1995` is borrowed from Scots pine. `birch_2002` is sourced for birch, with its limits written down.
5. A tree outside a plot never gets a status, so it is unchanged.
6. What I expect, SUSPECTED: the pine rule narrows heights after 30 and fails do-no-harm. The birch rule spreads heights and never lets a small tree catch up. Its own risk is stems: the plots, already short of stems, may thin themselves faster.

## 1. The two formulas as coded

`treegen/height_status.py`. Each year, before the trees grow, the plot reads its stand as a tree list holds it at the end of last year: DBH over bark to 0.01 cm (tools/bark.py), 0 for a tree under breast height, and height to 0.001 m.

**pine_1995**: Hynynen 1995, Silva Fennica 29(3), eq. 5 and Table 6, p. 235. Scots pine. Not reopened by me; the equation and coefficients are as the 2026-11-11 challenge read them on the publisher's scan.

    modifier = r ^ (a1 · IH + a2 · r ^ a3),   a1 = 0.2445, a2 = −0.4710, a3 = 0.8045
    r  = d / D_dom, held in 0.4-1.1; a tree with no DBH takes r = 0.4
    D_dom = mean DBH of the 100 thickest stems a hectare
    IH = curve(A + 5) − curve(A), held in 0.6-3.6 m;  A = the stand's age

**birch_2002**: Hynynen et al. 2002, Metla Research Papers 835, Eq. 33 p. 40 and Table 24 p. 41. Birch, self-sown (PLANT = 0).

    modifier = r ^ ((a1 + a2 · PLANT) · RDFL),   a1 = 1.54405, a2 = −0.81202
    r  = d / D_dom, with d held in 1.0-41.4 cm; a tree with no DBH takes d = 1.0 cm
    D_dom = mean DBH of the trees thicker than D_g,  D_g = Σd³ / Σd²   (Symbols, p. 9)
    RDFL_i = Σ over trees j with d_j > d_i of (10⁴ / plot area) / N(d_s,j), held at most 1.567   (Eqs. 21-23, pp. 30-31)
    ln N = 14.1979 − 2.2178 · ln d_s   (silver birch self-thinning line, Eq. 50, Table 34 p. 53)
    d_s = 2.0 + 1.25 · d   (stump diameter, cm, Eq. 3 p. 22)

Then, in both rules:

    status_i = modifier_i / mean(modifier over the dominants)
    step_i   = (curve(age_i) − curve(age_i − 1)) · light_i · water_i · status_i      (growth.py _height_limit_plan)

Arm B multiplies every status by one plot-wide factor F = (curve(A + 1) − H) / (curve(A + 1) − curve(A)), held in 0 to `height_driver.catch_up` (1.25). H is the approved top height now. If the Näslund curve can't be fitted, F = 1.

The rest of the height rule is unchanged: the running total, the 1.25 catch-up cap, the leader paid first, light_full 0.6, water_full 0.8.

I checked these against the PDF's text layer: the birch symbols, Eqs. 20-23, Eq. 3, Eq. 50's text, and that a1 and a2 are 1.54405 and −0.81202. Table 34's numbers are scrambled in the text layer. Step S read them on the page image; I did not.

## 2. Definitions chosen, and why

| What | Chosen | Why |
|---|---|---|
| The dominants for scaling | `scale_over: top_height`, the default: the 100 thickest a hectare. On 1,000 m² that is 10 trees, the thickest first, the tallest among equals. This is the same pick `plot.height_follows_dominants` uses | The curve is a top-height curve (Elfving 2010 p. 58), so the trees whose step it gives are the 100 thickest. The owner's goal is that top height follows the curve |
| The pine rule's own dominants | The same 100 thickest, for D_dom and for scaling | That is Hynynen 1995's D_dom |
| The birch rule's own dominants | Trees thicker than D_g. D_dom is their mean DBH (arithmetic: the report says "mean diameter") | The report's definition (p. 9). Hdom, and so IH_dom, is the mean height of the same trees. Using the 100 thickest as D_dom would sink top height by construction (step S report) |
| Birch with `scale_over: rule` | Scales over the trees thicker than D_g | A setting, not an arm. With it, a tree at D_dom gets about the curve's step, as Eq. 33 gives it. The 100 thickest then get a little more (SUSPECTED, about 1 %), so top height would drift up |
| How the approved top height relates | It is the plot's Näslund curve read at the mean DBH of those same 100 thickest (`scorecard.naslund_top_height`). Their mean status is 1, so their mean step is the curve's step at their own ages. The approved figure differs from their mean height by the curve fit (0.1-0.4 m, plan section 8, item 5) | Under birch_2002, the report's mean dominant tree (d = D_dom) gets 1 / mean(modifier of the 100 thickest). That mean was 1.001-1.007 on the control stands (section 4), so it grows 0.993-0.999 of the curve's step. That is the swap from the report's Hdom to our top height, made explicit |
| IH, and the stand's age | A = the plot's year at the start of the season (the age of the first cohort). IH is the curve's forward five-year step from there | The plan's section 1, and the challenge's fix: Hynynen's IH_dom is the next five years' growth from the measurement |
| A five-year rule, applied yearly | The ratio of five-year growths multiplies each year's step, recomputed each year from last year's stand | Assumed. Both papers predict five-year periods from the state at the start |
| Start | pine_1995: once approved top height reaches 10.0 m (plan section 1). birch_2002: once approved top height reaches 2.6 m **and** the stand is 12 years old. Before the start, every status is 1. Once started, the rule stays on | birch_2002: Table 5 p. 18, where the data start at dominant height 2.6 m and stand age 12. Both must hold for a stand to be inside the data. On SI 23 the age binds: the curve passes 2.6 m at about 8-9 and is 5.2 m at 12. The age gate is my reading of the same table; setting `start_age_years=null` drops it |
| The start's top height | The approved definition (Näslund), as the plot would log it. While the curve can't be fitted, the mean height of the 100 thickest stands in | Plan section 8, item 5: the approved definition everywhere |
| A tree with no DBH | pine: r = 0.4, never status 1 (challenge P2). birch: d = 1.0 cm, the data's smallest DBH. For RDFL it is larger than no tree, and every tree with a DBH is larger than it | In MELA, trees under breast height belong to a separate ingrowth model, not to Eq. 33 |
| RDFL | Every tree with a larger DBH counts once, standing for 10⁴ / area stems a hectare. Equal DBHs don't count each other. Held at the data's highest RDF, 1.567 | Eq. 23 and the report's cohort note (p. 31). RDFL can't exceed the stand's RDF |
| Over bark | Both rules read DBH over bark | The Finnish data measured DBH over bark. The ratio hardly moves |

## 3. Sourced, borrowed, assumed

Labels are in `reference/betula_pendula/labels.yaml`, beside `plot.height_follows_dominants`. No existing value changed.

| Value | Label |
|---|---|
| pine_1995 a1, a2, a3 | VERIFY, **borrowed from Scots pine** (Hynynen 1995 Table 6 p. 235; 11 thinned trials, ages 29-56, mean height 10.0-15.2 m at the start). Never sourced for birch (DECISIONS 110) |
| pine_1995 ratio 0.4-1.1, IH 0.6-3.6 m | VERIFY, borrowed: read off Hynynen 1995 Fig. 5 by eye. Used as limits by design |
| pine_1995 start 10.0 m | VERIFY, borrowed: the plan's reading of the data's start (mean height 10.0-15.2 m in Table 1) |
| birch_2002 a1 1.54405, a2 −0.81202 | **sourced**: Table 24 p. 41. Holds for birch, silver and downy pooled, on mineral soils in Finland. The data are 26 birch stands (14 silver, 12 downy), birch mixed into 181 pine and 95 spruce stands (mostly under 20 % of volume), and 13 thinning trials; 2,572 observations. a2 is not used while `planted` is false |
| Self-thinning 14.1979, −2.2178 | **sourced**: Eq. 50, Table 34 p. 53. Silver birch, unthinned stands (Table 11 p. 23: 10 stands, ages 15-109) |
| Stump 2.0 + 1.25 d | sourced: Eq. 3 p. 22, from the text layer only (not checked on the page image) |
| birch_2002 limits 1.0-41.4 cm, RDFL 1.567, start 2.6 m and 12 years | DERIVED: Table 5 p. 18, the data's range, used as the rule's limits by design |
| `planted: false`, `rule`, `scale_over`, `steer_top_height` | Switches. Self-sown fits the natural start |
| Status ÷ the dominants' mean; arm B's F held in 0-1.25 | By design. 1.25 is the existing `catch_up` (TUNED), not a new value |
| Swaps | IH_dom and the dominants' step come from the approved Swedish curve (Eriksson 1997 as in Elfving 2010, SI 23), not from Hynynen 2002's own dominant-height model, which I did not read (Table 14) |

## 4. A preview on the control's stands (no feedback, SUSPECTED as a forecast)

This is read-only arithmetic on T1's saved control lists (`node_t1r_plots_5cfec02`, seeds 1 and 2). For each living tree it gives the status it would get from that stand. "Today" is the draw ÷ the dominants' mean draw, which multiplies height now. These numbers are CONFIRMED as computed. Reading them as a forecast is SUSPECTED.

| Age | 20 | 25 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|---|
| Living trees per plot (1,000 m²) | 984 | 541 | 285 | 92 | 69 | 52 |
| Today: 10th percentile / median | 0.80 / 0.86 | 0.81 / 0.87 | 0.83 / 0.89 | 0.87 / 0.92 | 0.87 / 0.92 | 0.88 / 0.93 |
| pine_1995: 10th percentile / median | 0.80 / 0.89 | 0.90 / 0.95 | 0.95 / 0.98 | 1.01 / 1.02 | 1.01 / 1.04 | 1.01 / 1.05 |
| birch_2002: 10th percentile / median | 0.76 / 0.93 | 0.80 / 0.95 | 0.79 / 0.94 | 0.69 / 0.89 | 0.68 / 0.89 | 0.61 / 0.88 |
| birch_2002: share of stems under 0.8 | 18 % | 11 % | 13 % | 32 % | 30 % | 35 % |
| RDF by the silver birch line | 0.52 | 0.55 | 0.61 | 0.79 | 0.80 | 0.93 |
| Trees thicker than D_g (birch's dominants) | 39 % | 40 % | 40 % | 38 % | 39 % | 36 % |
| Mean birch modifier of the 100 thickest | 1.001 | 1.002 | 1.003 | 1.007 | 1.006 | 1.003 |

The birch modifier for self-sown stands (my arithmetic; it agrees with step S's table):

| d / D_dom | RDFL 0.2 | 0.4 | 0.6 | 0.8 |
|---|---|---|---|---|
| 0.4 | 0.75 | 0.57 | 0.43 | 0.32 |
| 0.6 | 0.85 | 0.73 | 0.62 | 0.53 |
| 0.8 | 0.93 | 0.87 | 0.81 | 0.76 |

## 5. What I expect from each arm, written before any arm ran (SUSPECTED)

Control: T2's K. The plan's figures are approved top height 21.39 / 23.14 at 50 / 60; height SD 1.04 / 1.06 / 1.09 m at 45 / 50 / 60; DBH spread 0.14 / 0.15 / 0.15; stems/ha 846 / 667 / 474.

Another piece of evidence, from T2's arm N (the draw taken off height, nothing in its place; partial, seed 1, read at 21:40 today). N had 11,920 / 5,620 / 1,760 stems/ha at 15 / 20 / 30, against K's 13,820 / 9,520 / 2,790, with the plot's own top height the same (15.84 against 15.80 m at 30). Before its start, every arm here is arm N.

| Arm | Top height (approved), m, 50 / 60 | Height SD, m, 45 / 50 / 60 | DBH spread, 45 / 50 / 60 | Stems/ha, 45 / 50 / 60 |
|---|---|---|---|---|
| A (pine_1995 from 10 m) | 21.0-21.7 / 22.8-23.5 | 0.5-0.8 / 0.5-0.8 / 0.4-0.8 | 0.12-0.15 at each | 650-850 / 500-670 / 360-480 |
| A-early (pine_1995 from the first DBH) | 21.0-21.7 / 22.8-23.5 | 0.6-0.9 / 0.6-0.9 / 0.5-0.9 | 0.13-0.16 at each | 650-850 / 500-670 / 360-480 |
| BIRCH (birch_2002) | 20.9-21.7 / 22.7-23.5 | 1.3-2.0 / 1.4-2.2 / 1.5-2.4 | 0.15-0.19 at each | 600-820 / 460-640 / 330-460 |
| D-A (A, vigour_sd 0) | 20.9-21.7 / 22.7-23.5 | 0.3-0.6 at each | 0.08-0.12 at each | 650-900 / 500-700 / 360-500 |
| D-BIRCH (BIRCH, vigour_sd 0) | 20.9-21.7 / 22.7-23.5 | 0.8-1.5 at each | 0.10-0.15 at each | 600-880 / 460-680 / 330-480 |
| B (A with the steer) | 21.85-22.05 / 23.65-23.85, by design | as A | as A | as A, or up to 5 % fewer |

Why:

- **Top height, all arms.** The 100 thickest have a mean status of 1, and before each start every status is 1. So top height is led by the curve, as now. N's top height at 30 matches K's. The control is 0.6 m under the curve, probably because late germinators' own-age steps and the Näslund fit pull it down. Only B removes that gap. The bands allow for a change in who the dominants are.
- **A.** Until about 20, A is arm N: equal steps per cohort, faster self-thinning, so fewer stems at 20-30 (I expect 1,700-2,300 at 30 against 2,640). From 20 the pine rule separates trees mildly (10th percentile 0.80 at 20, 0.95 at 30). From 45 every status is at or above 1: small trees outgrow the dominants (1.01-1.05). Height SD therefore falls below the control at 45-60. **A fails do-no-harm on height SD.** This is the plan's forecast, and the preview supports it. Stems stay below the control, which moves away from the self-thinning line (0.62-0.89 now).
- **A-early.** From about 6 the ratio is held at 0.4 for many young trees, with IH near its cap of 3.6, so their status is 0.56 ÷ the dominants' mean. That is a stronger split than today until 20, then the same catch-up. Height SD at 30 is above the control, probably 1.0-1.5 m against 0.85. At 45-60 it sits between A and the control. Information only.
- **BIRCH.** The rule is on from 12, and nothing before that differs from N. It splits trees more than today at every age, more so with RDF (10th percentile 0.76-0.79 to 30, 0.61-0.69 at 45-60), and never reverses. Height SD at 45 should rise above the control and could pass do-no-harm's improvement test. Shaded small trees then fix less carbon and die sooner, which removes the lowest stems: SD stops short of the measured 3 m, and stems fall. DBH spread rises a little: the losers lose light before they die.
- **D arms.** Every tree has alpha 4.8. The dominants lose the eighth of carbon their high draws gave them (alpha 5.4-5.5 now). Spreads then come only from germination year, place, seed and the rule's own feedback. Leaf area and LAI fall, so the light under the canopy at 60 (19.5 % now, limit 19.8 %) is the likeliest fail. These arms answer decision 10 and are not candidates.
- **B.** Top height sits on the curve by construction and is not a test. The dominants' own steps and the Näslund-against-mean gap are printed as the check (plan step E). F stays near 1.25 until the 0.6 m is closed, then near 1. All trees grow slightly taller.

**The birch rule's own risk.** The plan's forecast for A, catch-up after 45, does not apply to the birch rule: under it a thinner tree never gets more than the dominants' step. Its risks are these:

1. **Stems.** Suppression compounds from 12 and strengthens as RDF rises. In this model a shorter tree gets less light, so less carbon, so it dies sooner. The plots already sit at 0.62-0.89 of the published self-thinning line, against 0.96-1.03 in measured unthinned stands (step S, 4c). The birch rule can push them further below it, and below the control's stems at 45-60. Fewer stems with the same top height also threatens light at 60, which has 0.3 points of room.
2. **Beyond its data in density.** The data's mean RDF is 0.47 and most of its birches stood among conifers. The plots reach RDF 0.8-0.93 at 45-60 in pure, self-sown birch. The rule is used at the top of its data, where suppression is strongest (exponent 1.2-1.4).
3. **Late germinators.** A tree still under breast height at 12 takes d = 1.0 cm against a D_dom of several cm. Its status is then near 0 and it never gets out. MELA hands such trees to an ingrowth model. Regeneration is off in these runs, so this touches only the stragglers of years 1-3.
4. **The swap of curves.** IH_dom from our approved top-height curve, not from Hynynen 2002's own dominant-height model, which I didn't read. The two are probably within a few per cent (section 2, scaling).

None of these numbers is a target, and nothing is tuned to meet them.

## 6. Arms: settings only, no further code

Each arm uses the control's command, `tools/forest.py plots --years 60 --area 1000 --tree-lists 11,15,20,22,23,24,25,26,27,28,29,30,33,35,40,42,45,50,60`, plus:

| Arm | Settings |
|---|---|
| A | `--set plot.height_status.enabled=true --set 'plot.height_status.rule="pine_1995"'` |
| A-early | A and `--set plot.height_status.pine_1995.start_top_height_m=null` |
| BIRCH | `--set plot.height_status.enabled=true --set 'plot.height_status.rule="birch_2002"'` |
| D-A, D-BIRCH | A or BIRCH and `--set plot.vigour_sd=0` (the draws are still taken, so positions and germination years stay paired) |
| B | A and `--set plot.height_status.steer_top_height=true` (B on the birch rule likewise) |

What each run saves:

- **Per tree,** in every tree list: `height_status`, `height_modifier`, `height_ratio` and, for birch, `height_rdfl`, beside T1's `vigour` and `germination_year`.
- **Per plot-year,** in `plot.json`'s yearly stats as `height_status`:
  - `dominants_mean_modifier`, `dominant_dbh_cm`, `ih_m` (pine) or `dg_cm`, `rdf` and `rule_dominants` (birch);
  - the top height the start read, and the approved one;
  - `started`, and `steer_factor` in B.
- The tree list's header holds the same plot-year as `height_status_year`.

These keys exist only with the switch on.

## 7. The switch off: checks

Results below, at commit 8ebcc03 (the build). The design note's own commit changes no code.

All four checks ran on the server at commit 8ebcc03, on at most 4 cores. All CONFIRMED.

| Check | Job | Result |
|---|---|---|
| Full tests | `node_e_tests_8ebcc03` | 4 failed, 500 passed, 1 skipped (13 min). The 4 are the known environment failures: test_scorecard_runs, test_birchs_targets_are_read_through_the_approved_tag, test_a_different_version_is_reported, test_this_pc_matches_the_lock_file. Master 10ebc32 on the server (`node_m_tests_10ebc32`): the same 4 failed, 483 passed. The 17 new tests all pass |
| Golden runs | `node_e_gold_8ebcc03` against `node_e_gold_10ebc32` (master, newly recorded; no recording of 10ebc32 existed) | IDENTICAL: tree60 3, mesh30 13, plot25 76, regen10 133 files |
| Switch-off rule, plots, seeds 1-2 | `node_e_plots_8ebcc03` against `node_t1r_plots_395355d` | IDENTICAL. Each plot.json is identical (sha256 0b323f5fafc9613f, eecb5d554e0639cb). The tree lists match in 311,190 and 316,638 values over 19 years, ages 50 and 60 among them. The only options that differ are the new switches, off |
| Switch-off rule, stand trees, seeds 1-3 | `node_e_trees_8ebcc03` against `node_t1r_trees_395355d` | IDENTICAL: stats.json, and tree.json in all 997 values both sides have, for each seed |

The named controls predate T1, so T1's new tree-list columns were not compared there. I also compared the plots against T1's own `node_t1r_plots_5cfec02`, which has those columns. Every living tree's row matched in all 259,782 and 270,831 values both sides have. The dead trees' rows differ only because that run had `log.stand` on (switch_off.py's own note on it). So the formal comparison is the one against the named control.

## 8. Not done

- No arm was run. Running the arms is the next sitting, after the build is checked by the other model (plan section 2).
- Hynynen 1995 was not reopened by me. Hynynen 2002's Table 14 (its dominant-height model) and Table 34's page image were not read by me.
- Pay-first (the design's change 2) was not built. The plan builds it only if T2's log shows it would act.
- The plan's per-arm share of variance explained by the draw plus germination year is a reading for the report, not code. The tree lists hold what it needs: `vigour`, `germination_year`, height and DBH.
