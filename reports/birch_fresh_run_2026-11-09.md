# Birch: fresh run on today's defaults, 2026-11-09

Branch `fable-top5`, from master `38ce58e` (crown fix C merged). The review's top 5 (`reports/reviews/2026-11-09_logic_review_fable.md`, on the reviewer's branch), done simply.

## Summary

1. Today's defaults, rerun from scratch on the server (20 stand trees, 20 plots, to 60).
   - Stand trees: both scored targets pass at 50 and 60, as in v1. Height sits on the curve in all 1,200 seed-years, as designed.
   - Plots: LAI and light pass. Light at 60 is 19.5 %, 0.3 under the top. The Baltic LAI fails at 50 by 0.01.
2. New reported rows sit outside the targets. They are never PASS or FAIL.
   - Stem wood is within 5 % of Repola at 50 and 60.
   - Branch wood is 26-33 % over Repola.
   - The forest is far too even: at 45 diameters spread half as much as the measured stand, heights a third as much.
3. Carbon: stand trees turn none of their fixed carbon down at 50 and 60, and 6 % at 30. The review's "spare carbon is thrown away" was wrong for those ages.
4. Young crowns by height: stand trees still miss Hynynen & Niemistö's 5-7 m (0.89 m, 0 of 20). Crown fix C helps plots, not stand trees.
5. The spacing switch (off by default) changes little to 60. The fault it targets is in old forests with regeneration, which these runs don't reach.

## 1. Fresh run on the defaults

Runs on the server at `38ce58e`, nothing set:
- `node_f5_trees`: `tools/tree_table.py run --seeds 20`.
- `node_f5_plots`: `tools/forest.py plots --seeds 20 --years 60 --area 1000 --tree-lists 20,30,40,45,50,60`. It sets `mortality.enabled`, `plot.natural_start.enabled` and `plot.stand_measures`, as v1's plots did. No regeneration.
- Files: `out/bench/ensemble/node_f5_trees`, `out/bench/ensemble/node_f5_plots`.

### Stand trees, 20 seeds (mean)

Read by `tools/scorecard.py` and `<scratchpad>\read_trees.py`.

| Age | Height m | Stem cm over bark | LAI | Light % (diffuse) | Crown width m | Crown ratio | CUE |
|---|---|---|---|---|---|---|---|
| 30 | 15.84 | 15.7 | 5.61 | 13.6 | 3.53 | 0.72 | 0.50 |
| 50 | 21.90 | 28.0 | 4.73 | 16.6 | 5.77 | 0.52 | 0.47 |
| 60 | 23.73 | 31.3 | 4.60 | 17.1 | 6.35 | 0.46 | 0.47 |

Against v1 (`node_v1_treesR`):
- LAI 4.82 / 4.68 then, 4.73 / 4.60 now.
- Light 16.2 / 16.4 then, 16.6 / 17.1 now.
- Height is unchanged.

The leader was held by the curve in 1,200 of 1,200 seed-years, as in v1.

### Plots, 20 plots of 1,000 m² (mean, lowest-highest)

Read by `<scratchpad>\read_plots.py`. Top height is the approved definition: the scorecard's own Naslund curve on the tree lists.

| Age | Stems/ha | Basal area m²/ha | Dg cm | Top height m | LAI | Light % (diffuse) |
|---|---|---|---|---|---|---|
| 30 | 2640 (2240-2990) | 18.9 (17.9-20.0) | 9.6 (8.9-10.4) | 15.21 (14.97-15.40) | 5.44 (5.14-5.71) | 16.0 (14.6-17.4) |
| 50 | 667 (590-760) | 24.7 (23.7-26.0) | 21.7 (20.6-23.3) | 21.39 (20.94-21.70) | 4.51 (4.24-4.74) | 18.2 (16.6-20.3) |
| 60 | 474 (430-540) | 26.8 (22.7-28.6) | 26.8 (25.3-28.8) | 23.14 (22.44-23.52) | 4.29 (3.56-4.52) | 19.5 (18.1-20.7) |

Stems/ha at 45: 846 (760-980), against Hagemeier's 880 (INFO).

Against v1 (`node_v1_plots`), at 50 / 60:
- stems 751 / 520, now 667 / 474;
- LAI 4.54 / 4.36, now 4.51 / 4.29;
- light 18.5 / 19.0, now 18.2 / 19.5.

These agree with DECISIONS 107's fix C runs: LAI 4.51 / 4.29, light 18.22 / 19.48.

### Scorecard (unchanged, `tools/scorecard.py --ensemble`)

Stand trees, 20 seeds, approved targets at `targets-approved`:

| Target | Age | Mean | SD | Share inside | Verdict |
|---|---|---|---|---|---|
| Hagemeier LAI 3.6-5.4 | 50 | 4.730 | 0.700 | 70 % | PASS |
| | 60 | 4.603 | 0.733 | 75 % | PASS |
| Light 6.4-19.8 % (median 14.8) | 50 | 16.580 | 3.601 | 85 % | PASS, +1.8 from the median |
| | 60 | 17.053 | 4.368 | 75 % | PASS, +2.3 from the median |
| Site-index height | 30 / 50 / 60 | 15.84 / 21.90 / 23.73 | | 100 % | PASS, by design |
| Crown ratio, Hynynen ≥ 0.5 | 50 / 60 | 0.520 / 0.459 | | 80 % / 25 % | INFO |

Plots, 20:

| Target | Age | Mean | SD | Share inside | Verdict |
|---|---|---|---|---|---|
| Baltic LAI 2.5-4.5 | 30 | 5.445 | 0.135 | 0 % | **FAIL** |
| | 50 | 4.512 | 0.135 | 50 % | **FAIL**, by 0.012 |
| | 60 | 4.287 | 0.202 | 95 % | PASS |
| Hagemeier LAI 3.6-5.4 | 50 | 4.512 | 0.135 | 100 % | PASS |
| | 60 | 4.287 | 0.202 | 95 % | PASS |
| Light 6.4-19.8 % (median 14.8) | 50 | 18.218 | 1.105 | 90 % | PASS, +3.4 from the median |
| | 60 | 19.476 | 0.730 | 70 % | PASS, +4.7 from the median, 0.3 under the top |
| Stand density, 880 at 45 | 45 | 846 | 53 | | INFO |

Plot top height isn't scored by the scorecard, because plots keep no yearly per-tree records. By hand on the approved definition (table above) it is inside SI 20-26 at 30, 50 and 60, by design.

## 2. Untuned checks, as reported rows

- `tools/independent_checks.py`, also printed by `tools/scorecard.py --ensemble <folder> --independent` after the scorecard's own table.
- The scorecard's verdicts and targets are untouched.
- Each row gives its source and its kind: independent, partly, or tuned against.

Stand trees, 20 seeds:

| Check | Age 30 | Age 50 | Age 60 | Kind |
|---|---|---|---|---|
| Stem wood over Repola at its own size | 0.75 | 0.96 | 1.03 | independent |
| Branch wood over Repola's living branches (Repola's include bark) | 1.41 | 1.26 | 1.33 | independent |
| Stem volume, wood only, m³/ha | 88 | 207 | 292 | independent, no figure in the repo |

Plots, 20. The published figures are Hagemeier's two stands, at 45 and 67 years:

| Check | Age 30 | Age 45 | Age 50 | Age 60 | Published | Kind |
|---|---|---|---|---|---|---|
| Spread of DBH, SD over mean | 0.13 | **0.14** | 0.15 | 0.15 | **0.32 at 45**, 0.12 at 67 | independent |
| Spread of height, SD m | 0.86 | **1.04** | 1.06 | 1.09 | **3 at 45**, 3 at 67 | independent |
| Mean height of stems past 1.3 m, m | 13.8 | 18.9 | 20.0 | 21.9 | 20 at 45, 25 at 67 | partly (top height is by design) |
| Mean DBH over bark, cm | 9.5 | 18.8 | 21.5 | 26.6 | 19 at 45, 25 at 67 | tuned against |
| Basal area over bark, m²/ha | 18.9 | 24.0 | 24.7 | 26.8 | 25.2 at 45, 28.5 at 67 (Q32 open) | tuned against |
| Light, points from the 14.8 % median | +1.2 | +2.9 | +3.4 | +4.7 | 0 | tuned against |

**The forest is too even.** This is the clearest untuned result:
- At 45, diameters spread half as much as Hagemeier's stand (0.14 against 0.32).
- Heights spread a third as much (1.0 m against 3 m).

That fits the review's finding 2. A tree's height is the curve times a drawn vigour with SD 0.06, so trees can't differ much. One stand per age is thin evidence, and the paper's Table 3 has the problems noted in Q32.

### Proposed targets (not used until the maintainer approves; targets.yaml untouched)

1. **Stem volume against a yield table.** No figure is in the repository. Proposal: read a Swedish or Finnish birch yield table at its source (site index, age, stems/ha), and add it as a band under its own conditions.
2. **Diameter and height spread.** Hagemeier's Table 3 prints dbh 19 ± 6 cm and height 20 ± 3 m at 45. A proposed check: the plots' SD over mean against 0.32, and height SD against 3 m, at 45.
   - It is one stand.
   - Stems and Dg were tuned against that stand, so the spread is the only untuned part.
   - The model reads 0.14 and 1.0 m.
   - A second, independent source of stand diameter distributions would be better: a Nordic yield or growth study.
3. **Light against the median.** The approved band stays as it is. Proposal: report the distance from 14.8 % beside the verdict, with a stated tolerance chosen from the paper's own spread. The scorecard already prints the distance.

## 3. Young-stand test: the by-height proposal

The approved band, crown ratio 0.30-0.45 at ages 11-22 (Niemistö 1995), is unchanged and still the scored one. These are proposals for the maintainer, nothing more.

| # | Proposal | Source | Conditions | Status |
|---|---|---|---|---|
| A | Lowest live branch 5-7 m when dominant height is 13-15 m | Hynynen & Niemistö 2009, waldwissen.net (`reports/birch_knowledge_base.md` C1): "self-pruning clears stems to 5-7 m by the first thinning" | Planted stands at 1,600/ha. So stand-tree runs (thinned to 1,800 then 1,000/ha), read on the dominants, at the year dominant height reaches 13-15 m | A web guide, not a measurement table. Approve or reject |
| B | Crown ratio about 0.55-0.6 at 13-15 m (DECISIONS 105) | **Not a second source.** It is A's 5-7 m worked into a ratio: (13−5)/13 = 0.62, (15−7)/15 = 0.53 | As A | Drop as a separate target; it double-counts A |
| C | Niemistö 1995's 0.30-0.45, at the trials' own heights | Niemistö 1995, Table 2, Fig. 1; still unopened | Needs the trials' heights at 11-22 from the paper | Open the paper first. Until then, by age it fails: v1 plots read 0.92-0.96 |
| D | Stems/ha and stand leaf mass at a given height | Aosaar et al. 2016 (9.3 m at 11 years) | Plots, at stand height 9.3 m | Read the table at its source first |

Not usable as a test: Konopka et al. 2023 Eq. 4 (young leaf area for height). Crown fix C was tuned against it.

What the fresh run reads on proposal A:
- **Stand trees,** the first year each is 13-15 m tall (age 25, all 20): lowest live branch 0.89 m (0.31-2.26); 0 of 20 in 5-7 m; crown ratio 0.89. **A miss.**
- **Plots at 30,** every living stem 13-15 m tall (3,844 stems in 20 plots): lowest live branch 5.28 m (median 5.31); 68 % in 5-7 m; crown ratio 0.61.
  - These stems sit under a 15.2 m canopy, so most aren't dominants.
  - That reading flatters the model. A fair one needs a tree list at the year top height is 13-15 m (about 25), which this run didn't save.

**Crown fix C labelled "tuned against".**

| Place | State |
|---|---|
| Species file, `crown_frame.chase` and `limb_shoot_floor_m` comments | Both say TUNED against Konopka 2023 Eq. 4 (from `a5be3cb`) |
| `labels.yaml`, `crown_frame.chase` | TUNED, already |
| `labels.yaml`, `crown_frame.limb_shoot_floor_m` | Had no label; now TUNED with what it was tuned against |
| KNOWN_ISSUES.md, young crown ratio and young crown base rows | Said "Fixed after v1"; now "Tuned after v1, not fixed". The crown-base row now also gives this run's stand-tree miss |
| README.md | Said every parameter has its source. Now it names the labels file and says about a fifth are sourced and height follows a curve by design |
| `docs/site/how-real.md` | Gives v1's young crowns and makes no claim for fix C, so it is left alone. Its stand-tree line (0.8 m, 0 of 20) still holds |

## 4. Carbon turned down

- **Tool:** `tools/carbon_ledger.py`.
- **What it reports:** the carbon no sink took (`carbon.sink_limited`, which `growth.py` takes off "fixed"), as a share of fixed plus turned down.
- **Stand trees:** read every year.
- **Plots:** read from the tree lists. A plot's share is the sum over its living trees.
- **Not counted:** the roots' unspent rest isn't saved, so it isn't in these figures.

| Share of fixed carbon no sink took | Age 30 | Age 50 | Age 60 |
|---|:---:|:---:|:---:|
| Stand trees, each tree (20) | 6.3 % (0.0-16.1) | 0.0 % (0.0-0.0) | 0.0 % (0.0-0.0) |
| Plots, each plot as a whole (20) | 1.1 % (0.7-1.6) | 0.0 % (0.0-0.2) | 0.0 % (0.0-0.0) |
| Plots, each living tree | 0.8 % (0.0-20.1), 5,280 trees | 0.0 % (0.0-18.7), 1,334 trees | 0.0 % (0.0-0.1), 948 trees |

Carbon use efficiency (NPP/GPP) of stand trees is 0.50, 0.47, 0.47 at 30, 50, 60. It is computed before the turned-down carbon is taken off "fixed" (`growth.py:942-955`); with 0 % turned down at 50 and 60 that makes no difference there.

So the review's finding 1 overstated one part:
- At 50 and 60 a stand tree turns down no carbon. What it fixes is spent: on the leader the curve sets, the limbs the frame sets, twigs and rings.
- The rest of that finding stands. Height is set by the curve in every seed-year, and carbon doesn't decide it.

## 5. Tests and the spacing fault

**New tests,** in `tests/test_defaults.py`, all marked slow:
- `test_a_default_stand_tree_is_a_sane_birch_at_50_and_60`.
  - Grows the shipped defaults to 60, with nothing set.
  - Requires height inside the SI 20-26 band, DBH 10-45 cm, LAI 2-7, crown ratio 0.2-0.9 and crown width 1.5-12 m at 50 and 60.
  - Requires growth from 50 to 60, a DBH that never shrinks, and finite radii.
  - The bounds are sanity bounds, not targets.
- `test_crown_fix_c_is_the_default_and_young_limbs_reach_further_with_it`.
  - Checks the shipped values: chase 1.0, floor 0.5.
  - Grows the same seed to 15 with fix C and with the values before it (0.5, 0.2).
  - Requires the same height within 0.3 m, and a wider crown with more leaf area with fix C.
- `test_plot_spacing_counts_every_tree_by_default_and_only_the_canopy_with_the_switch`.

**Test run on the server** (`node_f5_tests`, `613f630`, `pytest -q`): 410 passed, 1 skipped, 4 failed.
- The 4 are the known environment ones; the server's copy has no git tag and no `.python-version`:
  - `test_scorecard_runs`;
  - `test_birchs_targets_are_read_through_the_approved_tag`;
  - two in `test_worker`.
- The three new tests pass.
- No existing test was changed.

**Spacing switch.** `plot.spacing_min_height_share`, null (off) by default.
- When set, the spacing that caps limb reach and sets the wind load counts only trees at least that share of the canopy top's height (`treegen/plot.py`).
- Off, the code path is the one before.
- Paired on seeds 1-5: switch at 0.5 (`node_f5_space`, `613f630`) against the fresh default (`node_f5_plots`, `38ce58e`). The off path is line for line the old code.
- "Over 2 SE" is the paired difference's mean against 2 standard errors.

| Age | Measure | Default | Switch 0.5 | Paired difference ± SE | Over 2 SE |
|---|---|:---:|:---:|:---:|:---:|
| 30 | Stems/ha | 2694 | 2590 | −104 ± 83 | no |
| 30 | Top height m (100 thickest) | 15.60 | 15.48 | −0.12 ± 0.02 | yes |
| 30 | LAI | 5.50 | 5.48 | −0.03 ± 0.08 | no |
| 30 | Light % | 15.95 | 15.97 | +0.02 ± 0.31 | no |
| 50 | Stems/ha | 666 | 638 | −28 ± 5 | yes |
| 50 | Basal area m²/ha | 24.42 | 24.09 | −0.33 ± 0.51 | no |
| 50 | LAI | 4.46 | 4.37 | −0.09 ± 0.03 | yes |
| 50 | Light % | 19.45 | 19.75 | +0.29 ± 0.62 | no |
| 60 | Stems/ha | 480 | 452 | −28 ± 13 | yes |
| 60 | Basal area m²/ha | 27.23 | 26.36 | −0.86 ± 0.14 | yes |
| 60 | Top height m (100 thickest) | 23.40 | 23.11 | −0.28 ± 0.13 | yes |
| 60 | LAI | 4.36 | 4.29 | −0.06 ± 0.02 | yes |
| 60 | Light % | 19.41 | 18.94 | −0.47 ± 0.29 | no |

Read by `<scratchpad>\paired_space.py`. Top height here is the stand's own measure (mean of the 100 thickest), not the Naslund one.

Reading:
- To 60, with no regeneration, the switch changes little: a little lower basal area, LAI and stems, and light within noise.
- The fault it targets is a veteran's crown capped by a forest of seedlings, which this run doesn't reach. A 200-year plot with regeneration would show it.
- **Not adopted;** the default stays off.

## Corrections to earlier reports

- **The review (`2026-11-09_logic_review_fable.md`):**
  - Finding 1 and the verdict said spare carbon is thrown away at maturity. The fresh run says 0.0 % at 50 and 60 for stand trees (section 4).
  - Finding 5 suspected the stand trees weren't rerun after fix C. True until now; they are rerun here.
- **KNOWN_ISSUES.md:** the young crown-base row read "Fixed after v1" from plot stems. Stand trees still miss (section 3), and the row now says so.

## What I'd merge

- Merge:
  - the tests;
  - `tools/independent_checks.py` and the scorecard's `--independent` flag (verdicts unchanged);
  - `tools/carbon_ledger.py`;
  - the label for `limb_shoot_floor_m`;
  - the KNOWN_ISSUES and README wording.
- The spacing switch is safe to merge, being off. It needs a 200-year plot with regeneration before anyone thinks of turning it on.
- The proposals in sections 2 and 3 wait for the maintainer.
