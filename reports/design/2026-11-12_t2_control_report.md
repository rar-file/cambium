# T2: the control runs, read

2026-11-12. Model: Fable 5.2 (ID `claude-fable-5-2`). Step T2 of `reports/design/2026-11-11_plan.md`, section 4. Read only: no model run, no test, no commit. This is the only file I wrote. The runs are the server's, at T1's commit `5cfec02`, fetched with `tools/node/fetch.sh` into `out/bench/ensemble/` (0.3 GB). On the PC I only read JSON and did arithmetic; the scripts are in the session's scratch folder, outside the repository. CONFIRMED = computed today from those files, or read in code. SUSPECTED = inferred. **Corrected the same day after the independent check, whose verdict was fail** (by Fable 5.2, ID `claude-fable-5-2`). The check matched every figure and found three decisions stated more firmly than the plan allows, one finding the data contradicts, and missing spreads. Each is corrected below. Every figure changed or added was recomputed from the fetched files with new scripts. Arm S1 ran late, on master `2d33997`, and is read in section 11. This version was checked a second time (Opus 5.5, ID `claude-opus-5-5`): every figure a decision rests on matched again, and its remaining points were wording (the T2 and E rows, item 4 of "In short", the stem ratio and one paraphrase), made here.

## In short

1. **The controls reproduce the fresh run in everything that grows.** All 20 forest plots and all 20 stand trees are the same as on 2026-11-09, to the last digit. Only records of the run differ: its timing, memory, commit and option list.
2. **Only the random draw separates stems in height, but a tree's reported height is not its stem's.** Light slowed a leader in 2 of every 10,000 tree-years. With the draw off height, stem tops differ only by germination year. Reported height is the tree's highest living point: at 45, 11.5 % of forest trees stand more than 0.3 m above their stem's limit (16.8 % with the draw off). That adds 0.13 m to top height and 0.07 m to height spread at 45, and is half of the no-draw forests' 0.41 m. So "top height follows the curve by design" is true of stem tops only.
3. **Arm A misses its gate, and pay-first's stop is my judgment, not the plan's rule.** Limbs that earn less than their ring hold 16.7 % of branch ring carbon at 60, 2.2 SE under the 20 % gate set before the read; at 50 they sit at the gate (20.2 % as the mean of trees, 19.2 % pooled). Arm A is not built. Pay-first meets the plan's condition: it would have newly acted, in 7 tree-years of 714,764, none after year 30. Not building it is my call, for the maintainer to confirm.
4. **Turning the branch-wood rate off overshoots.** Branch wood falls from 1.47 / 1.76 of Repola's figure at 50 / 60 to 0.47 / 0.44, against a band of 0.76-1.31. The arms become rates in between. D0 itself cost leaf (stand-tree LAI +0.46 at 60, against 0.21 of room in the forests' Baltic row) and stem (DBH +4.6 cm, with the forests 1.7 m²/ha under the 28.5 guard). An arm in between may reach either limit (SUSPECTED; stand trees are not plots).
5. **The forest is still thin when young and far too even; S1 is now read.** The forest holds 0.65 / 0.86 / 0.95 of the published self-thinning line's stems at 30 / 50 / 60. On the Finnish thinning schedule the stand tree's lowest live branch is 2.48 m when the tree first stands 13-15 m tall (the control: 0.89 m), 4.09 m at its first thinning and 3.60 m over the whole 13-15 m window. Written before the run: 2.5-4.5 m, still a miss of the guide's 5-7 m. The miss held on every reading; the range held at the thinning and over the window, and was missed by 0.02 m on the target's own reading. All four of T2's readings are now given.

## The runs (CONFIRMED in each job's own command and log; all 84 runs ended with exit 0)

| Label | What ran | Set on the command line | Did it act? |
|---|---|---|---|
| `node_t2_k` (K) | 20 plots, seeds 1-20, to 60, 1,000 m², 19 tree lists | `log.stand=true` | A record only |
| `node_t2_n` (N) | 4 plots, seeds 1-4, same lists | K's, and `height_driver.reference_alpha=null`: the plot sets no height reference, so every tree's draw factor on its height step is 1 (`plot.py:128`, `growth.py:2555` at `5cfec02`). The draw stays in carbon | Yes: differs from K from year 1-2 |
| `node_t2_kt` (KT) | 20 stand trees, to 60 | `log.rings=true`, `shedding.log_limbs=true` | Records only |
| `node_t2_d0` (D0) | 20 stand trees, to 60 | `pipe_model.branch_sapwood_senescence=null`: side axes take the stem's rate, 0.014 a year, not the tuned 0.30. No limb log | Yes: differs from KT from year 5-7 |
| `node_t2_s1` (S1) | 20 stand trees, to 60. **Run late, on master `2d33997`, not on T1's commit:** at `5cfec02` a thinning list given with `--set` did not load (DECISIONS 114; fixed on master) | KT's, and `stand.thinning`: 1,600/ha, 700 from 14 m, 375 from 20.5 m | Yes: differs from KT from year 4-9 |

## 1. Do K and KT match the fresh run? Yes (CONFIRMED)

| Set, compared by `tools/switch_off.py` with the fresh run (`node_f5_plots`, `node_f5_trees`, commit `38ce58e`) | What was held together | Result at 50 and 60, and every other year |
|---|---|---|
| K, 20 plots | `plot.json`: every yearly stand row to 60 and the damage log. Tree lists at 20, 30, 40, 45, 50, 60: 1,002,990 values on 58,991 tree rows | IDENTICAL in everything that grows, 20 of 20. The yearly log's seconds and memory columns, the run time, peak memory, manifest and option list differ, as they must |
| KT, 20 stand trees | `stats.json` whole (every yearly row to 60). `tree.json`: 19,940 values | IDENTICAL, 20 of 20, with `--switched shedding.log_limbs` |

- Not compared, because only T2 has them: 13 more list ages, 13 new columns on every tree, `stand_log.json`, `limbs.json`, the new yearly fields. The species file differs between the two commits by 17 added lines: one switch that is off, and the `log` block. Without `--switched` the tool prints DIFFERENT for KT. The one difference is the option `shedding.log_limbs` (false, true): a log whose name doesn't start with `log.`. Every value is the same.

The plan's control rows, recomputed from K and KT. Mean of 20 (lowest-highest):

| Row | Kind | 30 | 50 | 60 | Fresh run |
|---|---|---|---|---|---|
| Plots: light under the canopy, % | tuned against | 16.0 (14.6-17.4) | 18.2 (16.6-20.3) | 19.5 (18.1-20.7) | the same |
| Plots: LAI | tuned against | 5.44 (5.14-5.71) | 4.51 (4.24-4.74) | 4.29 (3.56-4.52) | the same |
| Plots: top height, approved definition, m | by design for stem tops only (section 10) | 15.21 (14.97-15.40) | 21.39 (20.94-21.70) | 23.14 (22.44-23.52) | the same |
| Plots: stems/ha; basal area, m²/ha | tuned against | 2,640 (2,240-2,990); 18.9 (17.9-20.0) | 667 (590-760); 24.7 (23.7-26.0) | 474 (430-540); 26.8 (22.7-28.6) | the same |
| Stand trees: LAI / light % | tuned against | 5.61 (4.49-6.21) / 13.6 (10.5-18.2) | 4.73 (3.45-5.79) / 16.6 (11.7-24.4) | 4.60 (2.79-5.69) / 17.1 (11.5-29.6) | the same |
| Stand trees: reported height; stem top, m | by design for stem tops only | 15.84 (15.83-15.84); the same | 21.90 (20.79-22.21); 21.89 (20.79-21.95) | 23.73 (23.02-24.12); 23.71 (23.02-23.75) | the same height |

- The curve held the leader in 1,200 of 1,200 seed-years. Light at 60 is over 19.8 in 6 of 20 plots; the mean is 0.3 under. The Baltic LAI row still fails at 50 by 0.012. The new yearly top height in `stand_log.json` equals my own reading of the tree lists to 0.00005 m. Stand trees when first 13-15 m tall (age 25): lowest live branch 0.89 m (0.31-2.26), 0 of 20 in 5-7 m; S1 is read against this in section 11.

## 2 and 3. What held a leader back, and would pay-first have acted? (CONFIRMED)

K, 20 plots, every tree that grew in each year (`stand_log.json`). Model records; there is no measured figure.

| Years | Leader-years | Light slowed the height step | Share, % (highest plot) | Water slowed it | Pool didn't cover the year's must-haves | Of those, leader already cut today |
|---|---|---|---|---|---|---|
| 1-5 | 126,273 | 0 | 0.000 | 1,069 | 1,069 (0.85 %) | 1,069 |
| 6-10 | 150,621 | 3 | 0.002 (0.03) | 0 | 0 | 0 |
| 11-20 | 259,323 | 89 | 0.034 (0.09) | 0 | 4 | 2 |
| 21-30 | 113,862 | 49 | 0.043 (0.19) | 0 | 14 | 9 |
| 31-40 | 35,577 | 2 | 0.006 (0.06) | 0 | 0 | 0 |
| 41-50 | 17,689 | 3 | 0.017 (0.12) | 0 | 0 | 0 |
| 51-60 | 11,419 | 3 | 0.026 (0.58) | 0 | 0 | 0 |
| Year 50 alone | 1,403 | 2 | 0.143 (1.45) | 0 | 0 | 0 |
| Year 60 alone | 972 | 0 | 0.000 | 0 | 0 | 0 |
| All | 714,764 | 149 | 0.021 (0.05) | 1,069 | 1,087 (0.15 %) | 1,080 |

| Trees alive at | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Trees in the 20 plots | 5,280 | 1,692 | 1,334 | 948 |
| Light factor under 1 that year | 0 | 0 | 2 | 0 |
| Light at the leader: 1st percentile (lowest tree). The rule bites under 0.6 | 0.945 (0.82) | 0.959 (0.90) | 0.933 (0.26) | 0.914 (0.77) |
| Ever short of the must-haves | 0 | 0 | 0 | 0 |
| Stand trees: light at the leader, mean (lowest) | 0.995 (0.990) | – | 0.989 (0.947) | 0.969 (0.892) |

- **Leader light.** It slowed 0.021 % of leader-years, 134 of the 149 in years 13-28. At the list ages the slowed trees' factor averaged 0.3 to 1.0. Stand trees: 0 of 1,200 seed-years.
- **Pay-first.** It would cut the leader when the pool can't cover the must-haves. That happened in 1,087 tree-years. In 1,080 of them today's rule already cuts the leader, because its own shoot costs more than the whole pool (`growth.py:1949-1955`). So pay-first would have newly acted in **7 tree-years**: 2 in years 11-20 and 5 in years 21-30, and none in 31-60. The plan's condition, "would have acted", is therefore met; whether 7 tree-years are worth a rule is a judgment (section 12). The 1,069 in years 1-5 are seedlings, and none lived: no tree alive at 11 had a short year. In those years the water, carbon and must-have counts are equal in every year (SUSPECTED: the same seedlings, with an empty pool). Stand trees: 0 of 1,200; their must-haves take 0.51 / 0.37 / 0.38 of the pool at 30 / 50 / 60.

## 4. The limb screen for branch arm A: fails the gate (CONFIRMED)

KT's limb log, 20 stand trees. A limb "earns less than its ring" when its own carbon, less its upkeep, is under the carbon its rings took that year. The log holds over 99.9 % of branch ring carbon. Model records.

| | Year 50 | Year 60 | Years 41-50 | Years 51-60 |
|---|---|---|---|---|
| Such limbs' share of branch ring carbon: mean of 20 trees (SD; lowest-highest) | 20.2 % (10.4; 0.5-40.4) | 16.7 % (6.7; 3.3-32.3) | 20.8 % (7.5; 9.1-34.3) | 17.7 % (7.1; 6.7-33.4) |
| Standard error of that mean | 2.3 | 1.5 | 1.7 | 1.6 |
| The same, all 20 trees pooled | 19.2 % | 16.1 % | 19.9 % | 16.8 % |
| Trees at or over 20 % | 9 of 20 | 5 of 20 | 9 of 20 | 6 of 20 |
| Ring carbon the rule would actually take away | 10.8 % | 8.2 % | 11.7 % | 9.3 % |

- **Gate (the plan's, set before the read): at least 20 % at 50 and at 60.** At 50 it is at the gate: 20.2 % as the mean of trees, 19.2 % pooled. At 60 it is under on both: 16.7 % and 16.1 %, 2.2 standard errors below 20. **FAIL. Arm A is not built.**
- Such limbs are 11.4 of 48.5 a tree at 50 and 10.5 of 43.4 at 60. They are older (24 / 28 years against 13 / 15) and lower on the stem. They hold 38 % / 36 % of limb wood and 21 % / 19 % of the leaf. An average limb earns 2.3 / 2.2 times its ring after upkeep. No limb's carbon before upkeep is under its ring. All branch ring carbon at 50 and 60 is the sapwood rule: 70 % / 75 % replaces sapwood that stopped conducting, the rest is for more leaf, and the wind adds none.

## 5. D0 (branch rate off) beside the control: outside the band, on the low side (CONFIRMED)

Stand trees, 20 seeds each, paired. Ratios are geometric means. Repola's branches include bark; the model's don't. In brackets: the SD over the 20 seeds, or for a ratio its lowest and highest tree.

| Row | Kind | 30: control, D0 | 50: control, D0 | 60: control, D0 | D0 less control at 50; at 60 (± SE; a ratio's factor is good to x/÷ 1.02-1.04) |
|---|---|---|---|---|---|
| Branch wood, kg | – | 14.1 (2.0), 8.7 (0.9) | 64.4 (11.9), 28.7 (4.3) | 88.9 (16.7), 32.9 (6.4) | −35.7 ± 2.0; −56.0 ± 2.7 |
| **Over A3, own crown length** | tuned against | 1.12 (0.88-1.65), 0.56 (0.44-0.64) | **1.47** (1.17-1.84), **0.47** (0.32-0.59) | **1.76** (1.36-2.55), **0.44** (0.34-0.62) | x 0.32; x 0.25 |
| Over Eq. 9 | tuned against | 1.37 (0.93-2.54), 0.68 (0.52-0.85) | 1.23 (0.85-1.95), 0.37 (0.32-0.50) | 1.29 (0.85-2.63), 0.32 (0.23-0.46) | x 0.30; x 0.25 |
| Over A3 at crown ratio 0.58 | tuned against | 1.37 (0.95-2.28), 0.70 (0.54-0.86) | 1.30 (0.90-1.79), 0.43 (0.36-0.56) | 1.35 (0.87-2.36), 0.36 (0.26-0.50) | x 0.33; x 0.27 |
| Stems inside Repola's diameters (2.5-38 cm), of 20 | – | 20, 20 | 20, 20 | 20, **16** | – |
| Stem wood, kg | – | 46.6 (4.5), 52.0 (3.3) | 243 (36), 295 (33) | 343 (58), 426 (55) | +51.7 ± 3.9; +82.7 ± 4.5 |
| Stem wood over Repola Eq. 7 | seen | 0.75 (0.71-0.89), 0.74 (0.67-0.79) | 0.96 (0.89-1.02), 0.95 (0.87-1.05) | 1.03 (0.93-1.14), 1.04 (0.93-1.14) | ×0.989 ± 0.007 at 50, ×1.004 ± 0.008 at 60 (paired, log SE; the second checker's recomputation) |
| LAI (rule 3.6-5.4) | tuned against | 5.61 (0.54), 5.84 (0.44) | 4.73 (0.70), 4.95 (0.57) | 4.60 (0.73), 5.06 (0.59) | +0.22 ± 0.06; +0.46 ± 0.09 |
| Light, % (rule: at most 19.8) | tuned against | 13.6 (2.3), 14.0 (2.1) | 16.6 (3.6), 17.0 (2.7) | 17.1 (4.4), 15.6 (2.6) | +0.4 ± 0.3; −1.4 ± 0.7 |
| Limbs over 2 cm | not a target | 23.1 (2.8), 10.3 (2.4) | 29.1 (2.4), 25.1 (2.5) | 27.4 (3.0), 24.6 (3.2) | −3.9 ± 0.6; −2.9 ± 0.9 |
| Branch length 1 cm or thicker, m | not a target | 65 (8), 42 (4) | 183 (32), 112 (14) | 216 (36), 121 (19) | −71 ± 5; −95 ± 6 |
| Limb over stem at the joint, 90th percentile | not a target | 0.46 (0.03), 0.36 (0.02) | 0.59 (0.02), 0.37 (0.02) | 0.64 (0.04), 0.35 (0.03) | −0.22 ± 0.01; −0.29 ± 0.01 |

- **The plan's rule for an arm: inside 0.76-1.31 at 50 and at 60.** The control is over (1.47, 1.76). D0 is under (0.47, 0.44), in 20 of 20 trees. **D0 does not land in the band, so it is not the first arm.** The two runs bracket the band. At 60, 4 of D0's 20 trees are thicker than Repola's largest sample tree (38 cm). The 16 inside are over the two thirds T1's rule asks, so the row is not INFO. D0's leader stays on the curve in 1,200 of 1,200 seed-years (stem tops 21.89 / 23.72 m at 50 / 60; reported height 21.92 / 23.81 m, section 10).
- **Where the freed carbon went:** stem wood (+21 % at 50, +24 % at 60; DBH +3.7 ± 0.3 and +4.6 ± 0.3 cm, which is 29 % and 32 % more basal area a tree) and leaf (LAI +0.22 and +0.46). The stem ratio doesn't show it, because it is read at the tree's own, thicker, diameter. Branch rings fall from 38 % / 41 % of the year's pool to 13 % / 12 %. Carbon turned down stays at 0.0 % at 50 and 60.
- **The Nordic scans** (trees 15.5-19.7 m tall). At that height, age 35: limbs over 2 cm are 58 in the scans, 30.0 (SD 2.8) in the control, 21.3 (2.7) in D0 (−8.7 ± 0.8). Branch length is 869 m, 120 (17), 71 (7) (−49 ± 3). Limb over stem is 0.67, 0.52 (0.03), 0.37 (0.02) (−0.16 ± 0.01). D0 moves all three away from the scans by far more than 2 paired SE. SUSPECTED: any lower rate moves them the same way. Half of D0's shift would still be several paired SE, so that trade almost surely goes to the maintainer. The control columns above are the "from KT" values the plan's B table asks for.
- **The rate in between. SUSPECTED: a line through two points (rate 0.014 and 0.30), not a result.** A3 would read 1.0 at a rate of 0.17 at 50 and 0.13 at 60 on a straight line, and at 0.20 and 0.18 on a log scale: 0.13-0.20, moving with the age and the line's form. The band's edges fall at 0.10-0.20 (straight) and 0.13-0.24 (log) at both ages. The design's 0.10, 0.15 and 0.20 are the arms to run. **What such a rate would cost (CONFIRMED for D0; SUSPECTED for an arm in between).** Leaf: D0 lifted stand-tree LAI by 0.22 ± 0.06 at 50 and 0.46 ± 0.09 at 60, and the plots' Baltic LAI row has 0.21 of room at 60 (4.29 against 4.5) and fails already at 50. Stem: D0 added 32 % to a tree's basal area at 60, and the plots stand at 26.8 m²/ha against the guard's 28.5 (decision 8): 6 % away, with 2 of the 20 plots over it today. An arm near half of D0's shift could reach either limit. Stand trees are not plots, which thin themselves, so this is a warning, not a forecast. Light moved the other way at 60 (−1.4 ± 0.7 points).

## 6. N (the draw off height) against K, seeds 1-4 (CONFIRMED)

Each cell: K → N; N less K ± SE of the 4 paired differences. * = over 2 SE. Four seeds can neither adopt nor stop anything.

| Row (kind) | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Top height, approved, m (by design for stem tops) | 15.17 → 15.94; +0.77 ± 0.09 * | 20.31 → 20.94; +0.63 ± 0.15 * | 21.35 → 21.95; +0.60 ± 0.14 * | 23.22 → 23.72; +0.50 ± 0.15 * |
| Height SD, m (independent) | 0.85 → 0.39; −0.45 ± 0.03 * | 1.06 → 0.41; −0.65 ± 0.04 * | 1.10 → 0.23; −0.87 ± 0.01 * | 1.13 → 0.14; −0.99 ± 0.09 * |
| Height, 10th to 90th percentile, m | 2.09 → 0.90; −1.19 ± 0.05 * | 2.62 → 1.00; −1.63 ± 0.22 * | 2.70 → 0.45; −2.25 ± 0.17 * | 2.93 → 0.31; −2.62 ± 0.26 * |
| DBH spread, SD over mean (independent) | 0.124 → 0.109; −0.015 ± 0.003 * | 0.147 → 0.102; −0.045 ± 0.004 * | 0.152 → 0.099; −0.053 ± 0.004 * | 0.151 → 0.096; −0.055 ± 0.006 * |
| Stems/ha (tuned against) | 2,745 → 1,725; −1,020 ± 76 * | 900 → 710; −190 ± 27 * | 675 → 585; −90 ± 31 * | 488 → 445; −42 ± 30 |
| Basal area, m²/ha (tuned against) | 18.7 → 20.3; +1.7 ± 0.2 * | 24.5 → 23.9; −0.5 ± 0.5 | 24.4 → 24.4; 0.0 ± 0.6 | 27.2 → 25.8; −1.5 ± 0.5 * |
| Light, % (tuned against) | 15.84 → 16.25; +0.41 ± 0.55 | 17.53 → 17.95; +0.42 ± 0.10 * | 19.27 → 19.44; +0.17 ± 0.93 | 19.41 → 19.64; +0.24 ± 0.36 |
| LAI (tuned against) | 5.45 → 5.09; −0.36 ± 0.05 * | 4.80 → 4.57; −0.23 ± 0.05 * | 4.47 → 4.36; −0.11 ± 0.12 | 4.36 → 4.13; −0.23 ± 0.07 * |

- **Without the draw, every tree's stem limit is the curve at its own age. Its reported height is not always** (corrected: the first version said "every tree's height is the curve"). At 30 all 690 trees are within 0.01 m of the curve at their own age. At 45, 16.8 % of trees (SD over the 4 plots 5.0; 12.5-23.3) stand more than 0.3 m above it, by up to 1.9 m, because reported height is the tree's highest point (section 10). With each tree capped at its limit, N's height SD at 45 is 0.21 m, not 0.41: half of N's spread at 45 is points above stem tops, and the rest is germination year (no tree is under its limit). At 50 in seed 1 the three germination years stand at 21.98, 21.73 and 21.51 m, against limits of 21.95, 21.73 and 21.51. Light, water and carbon add no spread to stem tops. The share of height explained by the draw alone falls from 0.80-0.97 to 0.01-0.06.
- **Top height returns to the curve** (15.84 / 20.80 / 21.95 / 23.75), to within 0.14 m. At 45, 0.16 ± 0.03 m of N's top height is points above stem tops (K: 0.13 m). The control's 0.5-0.8 m shortfall comes with the draw on height. This bears on decision 1. **Diameters lose a third of their spread** (0.15 to 0.10 at 50 and 60), so part of today's DBH spread is the height draw. **N thins much sooner:** 5,575 against 9,640 stems/ha at 20. SUSPECTED cause: in K the mean tree gets 0.88 of the curve's step (1 ÷ the dominants' mean draw, 1.13); in N every tree gets all of it, so basal area builds sooner (13.2 against 8.3 m²/ha at 15). Storm years are the same in N and K, seed by seed.

## 7. The spread rows, K on all 20 seeds (CONFIRMED)

Mean of 20 plots (SD over plots; lowest-highest). Measured: Hagemeier & Leuschner 2019, one stand at 45 and one at 67.

| Row | Kind | 30 | 45 | 50 | 60 | Measured |
|---|---|---|---|---|---|---|
| Height SD, m | independent; a guide row at 45 | 0.85 (0.04; 0.78-0.92) | 1.04 (0.07; 0.91-1.18) | 1.06 (0.09; 0.93-1.25) | 1.09 (0.13; 0.92-1.38) | 3 at 45; 3 at 67 |
| Height, 10th to 90th percentile, m | independent | 2.17 (0.13; 1.97-2.48) | 2.58 (0.22; 2.11-2.92) | 2.62 (0.27; 2.22-3.22) | 2.73 (0.33; 2.31-3.42) | – |
| DBH spread, SD over mean | independent; a guide row at 45 | 0.129 (0.008; 0.117-0.145) | 0.143 (0.013; 0.120-0.165) | 0.148 (0.015; 0.120-0.174) | 0.148 (0.016; 0.119-0.189) | 0.32 at 45; 0.12 at 67 |
| Crown ratio, all stems | seen, INFO | 0.60 (0.01; 0.59-0.62) | 0.50 (0.01; 0.48-0.51) | 0.47 (0.01; 0.46-0.48) | 0.42 (0.01; 0.41-0.44) | Swedish stand: 0.50 ± 0.07 at 33, 0.42 ± 0.03 at 42 |
| Height; DBH explained by draw and germination year | model record | 1.00 (0.00); 0.84 (0.02) | 0.89 (0.03); 0.83 (0.04) | 0.93 (0.06); 0.84 (0.04) | 0.99 (0.02); 0.85 (0.05) | – |
| Plot branch wood, t/ha; over A3, own crown length | tuned against | 7.3 (0.2; 6.9-8.0); 1.12 (0.06; 1.01-1.22) | 15.8 (0.8; 14.4-16.8); 1.19 (0.04; 1.14-1.29) | 19.3 (0.6; 18.3-20.6); 1.38 (0.04; 1.29-1.45) | 27.3 (1.3; 23.7-29.2); 1.77 (0.04; 1.70-1.85) | 1.0 |

- **At 45 the miss stands, in 20 of 20 plots:** height spread is 0.35 of the measured stand's, diameter spread 0.45. At 60 diameter spread is over the 67-year stand's (0.15 against 0.12); height spread is a third of it. Of the 1.04 m at 45, 0.07 m is points above stem tops (section 10): on stems the spread is 0.97 m, 0.32 of the measured. Crown ratio at the Swedish stand's ages: the model reads 0.57 at 33 and 0.51 at 42 (SD over plots 0.01 at both). At 42 that is a miss by three of the stand's SDs. Plot branch wood is saved for the first time. Over Eq. 9 it reads 1.30 / 1.10 / 1.14 / 1.25 at 30 / 45 / 50 / 60; over A3 at crown ratio 0.58, 1.17 / 1.07 / 1.14 / 1.30 (SD over plots 0.03-0.07). At least 98 % of stems are inside Repola's diameters in every plot at every age.

## 8. Stems against the Hynynen et al. 2002 self-thinning line (CONFIRMED arithmetic; the comparison is INFO)

The line (Table 34, silver birch): ln N = 14.1979 − 2.2178 ln(Dgs). Dgs = 2 + 1.25 x the basal-area-weighted mean diameter, the report's own Eq. 52. Under 12 cm the report uses the line's tangent at 12 cm. K, 20 plots, stems past 1.3 m. Weighting by basal area at stump height instead moves the share by 0.01 at most at these ages.

| Age | Stems/ha | Weighted mean diameter, cm | The line's stems/ha | Share the model holds (SD; lowest-highest) | Share on the plain mean diameter |
|---|---|---|---|---|---|
| 15 | 13,220 | 3.1 | 12,664 (tangent) | 1.04 (0.04; 0.96-1.11) | 1.01 |
| 20 | 9,324 | 4.5 | 10,775 (tangent) | 0.86 (0.03; 0.82-0.92) | 0.84 |
| 25 | 5,078 | 6.5 | 7,972 (tangent) | 0.64 (0.01; 0.61-0.67) | 0.61 |
| 30 | 2,640 | 9.8 | 4,080 | 0.65 (0.02; 0.62-0.68) | 0.61 |
| 35 | 1,620 | 13.3 | 2,254 | 0.72 (0.02; 0.69-0.75) | 0.67 |
| 40 | 1,122 | 16.6 | 1,448 | 0.78 (0.02; 0.74-0.83) | 0.72 |
| 45 | 846 | 19.6 | 1,026 | 0.83 (0.03; 0.73-0.88) | 0.76 |
| 50 | 667 | 22.4 | 776 | 0.86 (0.03; 0.81-0.90) | 0.79 |
| 60 | 474 | 27.7 | 501 | 0.95 (0.05; 0.79-1.02) | 0.87 |

- **The model leaves the line between 15 and 27 and climbs back to it by 60.** The lowest point is 0.61 at 27. Kind: stems were tuned against Hagemeier's 880 at 45, so this is not an independent test; the line itself was used in no setting.
- The measured unthinned stands in `reports/sources_opened_2026-11-11.md` read 0.96-1.03 on the plain mean diameter. The like-for-like model column is the last one: 0.61 at 30, 0.79 at 50, 0.87 at 60. The line's stands had weighted mean diameters of 7.4-25.5 cm. The rows to age 25 are outside that, and the row at 60 is just past it. The report says of the young end: "stands with mean diameter under 10 cm were poorly represented".
- SUSPECTED, my use of the line's printed SDs (0.160 between stands, 0.106 residual): one stand scatters about x/÷ 1.21 round the line. The model is about 2 SDs under at 30, under 1 at 50, a quarter at 60. N on seeds 1-4 reads 0.66 at 20 (K 0.88), 0.68 at 30 (0.64), 0.82 at 50 (0.85) and 0.88 at 60 (0.97).

## 9. Ages 50 and 60 by storm history (CONFIRMED)

A storm fell in years 45-50 in seeds **1, 3, 4, 5, 6, 8, 10, 11, 17, 20** (years 49, 49, 49, 49, 46, 50, 45, 48, 45, 46). Each killed 4-9 trees of 68-101. No storm then: seeds **2, 7, 9, 12, 13, 14, 15, 16, 18, 19**. Storms in 51-60: seeds 4, 7, 10, 12, 17. Mean (SD over plots); the difference is unpaired. Kinds as in sections 6 and 7.

| Row | 50: storm | 50: none | 50: difference ± SE | 60: storm | 60: none | 60: difference ± SE |
|---|---|---|---|---|---|---|
| Stems/ha | 660 (49) | 674 (44) | −14 ± 21 | 470 (24) | 478 (39) | −8 ± 14 |
| Basal area, m²/ha | 24.6 (0.6) | 24.9 (0.7) | −0.3 ± 0.3 | 26.7 (1.6) | 26.9 (1.2) | −0.2 ± 0.6 |
| Top height, approved, m | 21.37 (0.21) | 21.41 (0.15) | −0.05 ± 0.08 | 23.15 (0.33) | 23.14 (0.16) | +0.01 ± 0.12 |
| LAI | 4.47 (0.15) | 4.55 (0.11) | −0.08 ± 0.06 | 4.27 (0.26) | 4.31 (0.14) | −0.04 ± 0.09 |
| Light, % | 18.6 (1.1) | 17.9 (1.1) | +0.7 ± 0.5 | 19.7 (0.6) | 19.2 (0.8) | +0.5 ± 0.3 |
| Height SD, m | 1.09 (0.11) | 1.04 (0.05) | +0.05 ± 0.04 | 1.13 (0.15) | 1.05 (0.10) | +0.08 ± 0.06 |
| DBH spread | 0.149 (0.015) | 0.146 (0.017) | +0.003 ± 0.007 | 0.154 (0.017) | 0.141 (0.012) | +0.013 ± 0.007 |

- **No row differs by more than 2 SE at 50 or 60.** Stems close the gap within five years: storm plots lost 178 ± 16 stems/ha from 45 to 50, the others 180 ± 11. Both groups hold 0.86 of the self-thinning line at 50 and 0.95 at 60. Light is over 19.8 in 1 of 10 and 1 of 10 plots at 50, and in 4 of 10 and 2 of 10 at 60. Counting any storm in 45-60 (12 plots against 8), light at 60 is 19.7 against 19.1: +0.67 ± 0.33, just over 2 SE. The 12 are 0.06 under the limit as a group. Storm years go with the seed, so paired arms share them.

## 10. Trees above the curve (CONFIRMED in the files and the code; the cause is SUSPECTED)

A tree's reported `height_m` is its highest living point, not its stem's top (`growth.py:3130`; line numbers here are at `5cfec02`, and this one is 3136 on master). The curve limits only the leader's step (`growth.py:2562`). A plot tree's limit is rebuilt here as the curve's step at its own age, times its draw over the plot's dominant draw, summed over its years. At 30 that gives 5,274 of K's 5,280 trees to 0.01 m (the other 6 are under it) and all 690 of N's. "Capped" means each tree counted no taller than its limit. Mean of plots (SD over plots; highest plot).

| Row | 30 | 40 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| K, 20 plots: trees more than 0.3 m above their limit, %; the furthest, m (model record) | 0.0; 0.01 | 7.9 (3.0; 13.2); 1.83 | 11.5 (4.0; 23.5); 2.11 | 6.0 (2.6; 12.3); 1.95 | 1.8 (1.3; 4.7); 1.58 |
| K: approved top height (by design for stem tops), reported less capped, m (± SE; largest plot) | +0.001 | +0.033 ± 0.009 (+0.145) | +0.126 ± 0.015 (+0.280) | +0.046 ± 0.007 (+0.114) | +0.011 ± 0.003 (+0.037) |
| K: height SD, m (independent; a guide row at 45): reported; capped; difference ± SE | 0.85; 0.85; 0.000 | 0.95; 0.94; +0.007 ± 0.004 | 1.04; 0.97; +0.067 ± 0.007 | 1.06; 1.04; +0.020 ± 0.005 | 1.09; 1.09; +0.002 ± 0.003 |
| N, 4 plots: trees over, %; height SD reported; capped | 0.0; 0.39; 0.39 | 3.9 (1.5; 5.6); 0.31; 0.26 | 16.8 (5.0; 23.3); 0.41; 0.21 | 5.4 (3.3; 9.4); 0.23; 0.17 | 1.2 (2.3; 4.7); 0.14; 0.12 |

- **How large in stand trees.** Over the curve by more than 0.3 m in 10 of the control's 1,200 seed-years (seeds 11 and 14, up to 1.44 m), 29 of D0's (seeds 5, 8, 11, 12, up to 1.85 m) and 19 of S1's (the same four seeds, up to 1.44 m), none before year 36. Of 20 trees in the control, D0 and S1: 0, 1, 0 at 40; 1, 2, 2 at 45; 0, 1, 0 at 50; 1, 2, 0 at 60. In all 720 snapshots of the three arms the stem's own top is never more than 0.006 m over the curve.
- **What it means for "top height follows the site curve by design".** It is true of stem tops only. Plot top heights are built on each tree's highest point: the yearly log's approved top height (`plot.py:582-587`), the plot's own top height (`plot.py:632`, `660`) and the tree lists. So the control's reported top height carries 0.13 m at 45, 0.05 m at 50 and 0.01 m at 60 that no curve set, and its height SD at 45 carries 0.07 m. **Height SD at 45 is E's adoption row:** an arm that changes limbs or crowns can move it without changing one stem. In plots, which part of a tree is above its stem is SUSPECTED, by analogy with the stand trees: tree lists hold no stem top. A proposal for the maintainer, not done: record each tree's stem top in the tree lists, which changes no growth.
- **The part found, in one tree.** Control seed 11: the stem top is on the curve at every snapshot (20.80 m at 45, 21.95 at 50), and the tree reads 0.40 m over in year 39 and 1.41 to 0.47 m over in years 42-49. One first-order limb, born in year 34 at 16.9 m up the stem, lengthened 1.8 → 3.0 → 3.8 → 3.8 → 5.0 → 6.1 m over years 37-42 (1.17 m in year 42, against the leader's 0.28 m). Then it stopped lengthening until year 52, while its base thickened from 1.9 to 4.6 cm by 50. It is the only logged limb whose base height plus length (23.0 m) reaches the reported height: CONFIRMED as the only candidate, SUSPECTED that its tip is the highest point. Seed 14 (0.37 m over at 60): no logged limb's own axis reaches the height (23.69 against 24.12 m), so the part is not identified. D0 has no limb log. **Not the cause: a lost leader, as the first version suspected.** 14 of the 20 control trees lost a leader, all by the age-10 snapshot (7 of them by the age-5 one), and only 2 stand over, more than 25 years later. SUSPECTED, read in the code and not traced in a run: the frame holds a limb's tip under the leader only for buds that point up, on a straight line from the bud (`growth.py:2361-2375`), and lets a tree's second top come up beside the leader. A shoot that starts shallow and turns up is not held. Seed 11's count of reiterated limbs rises in years 36 and 41.

## 11. Arm S1: stand trees on the Finnish schedule (CONFIRMED; INFO only: the schedule's source is a guide with no measurements)

`node_t2_s1`, 20 seeds, on master `2d33997`: 1,600/ha (the guide's planting density), 700 from 14 m, 375 from 20.5 m. The control KT has 1,800, 1,000 from 11 m and 450 from 16 m. The tree is 13-15 m tall in years 25-28, at the same height in both arms. Each cell: S1; KT; S1 less KT ± SE of the 20 paired differences (* = over 2 SE). In brackets: SD over seeds, or a ratio's lowest and highest tree.

| Row | Kind | 13.5 m (year 25): the target's reading | 14.5 m (year 27): S1's first thinning | 50 | 60 |
|---|---|---|---|---|---|
| Lowest live branch, m | seen; INFO. The guide: 5-7 m at 13-15 m | 2.48 (0.64); 0.89 (0.46); +1.59 ± 0.18 * | 4.09 (0.50); 1.78 (0.90); +2.31 ± 0.20 * | 10.21 (0.94); 10.33 (0.91); −0.11 ± 0.19 | 13.31 (0.76); 12.64 (1.16); +0.66 ± 0.23 * |
| Height, m | by design for stem tops only | 13.46; 13.46 | 14.46; 14.46 | 21.91 (0.17); 21.90 (0.27); +0.01 ± 0.02 | 23.74 (0.08); 23.73 (0.19); +0.01 ± 0.03 |
| DBH over bark, cm | – | – | – | 27.6 (1.7); 28.0 (2.2); −0.43 ± 0.24 | 31.5 (2.3); 31.3 (2.7); +0.19 ± 0.25 |
| Crown ratio | seen | – | – | 0.52 (0.04); 0.52 (0.04); 0.00 ± 0.01 | 0.42 (0.04); 0.46 (0.05); −0.03 ± 0.01 * |
| Branch wood, kg | – | – | – | 67.7 (10.6); 64.4 (11.9); +3.3 ± 2.3 | 95.9 (17.5); 88.9 (16.7); +7.0 ± 2.6 * |
| Branch wood over A3, own crown length (all 20 stems inside Repola's diameters) | tuned against, on KT's schedule | – | – | 1.61 (1.09-2.10); 1.47 (1.17-1.84); x 1.10 * | 2.02 (1.55-2.36); 1.76 (1.36-2.55); x 1.14 * |

- **The reading the plan asks for.** Written before the run: 2.5-4.5 m, still a miss of the guide's 5-7 m. The target reads a stand tree in the first year it is 13-15 m tall, as the control's 0.89 m was read. **On that reading S1 gives 2.48 m** (SD over seeds 0.64; 1.42-3.68): 0.02 m under the predicted range's low edge, which is a seventh of its SE (0.14). 11 of 20 trees are inside 2.5-4.5 m, 9 are under it, and none is in 5-7 m. The branch climbs through the window: 2.48, 3.28, 4.09 and 4.58 m at 13.5, 14.0, 14.5 and 14.9 m. At S1's first thinning it is 4.09 m (3.21-4.96) and over the four years 3.60 m (SD 0.40; 2.89-4.23), both inside the prediction. No tree is in 5-7 m until the last year (4.58 m; 3.66-5.69), where 6 of 20 are. **So "still a miss of 5-7 m" held on every reading, and the predicted range held at the thinning and on the window's mean but was missed by 0.02 m on the target's own reading.** The control reads 1.60 m over the same window; S1 is 2.00 ± 0.14 m higher.
- **What else moved.** In both arms the lowest branch all but stops rising from the year after a thinning (S1: 4.58 m in years 28-30; the control: 0.78-0.81 m in years 22-24). S1 thins later: it is at 1,600/ha through year 26 and 700/ha from year 27, where the control is at 1,000/ha from year 21. SUSPECTED that this is why S1's branch is higher at 13-15 m. At 50 the two arms' lowest branches are the same. At 60 S1's is 0.66 ± 0.23 m higher and its crown ratio 0.03 lower. Branch wood is further from Repola on this schedule. LAI is 4.26 (SD 0.58) at 50 and 4.36 (0.67) at 60, lower than the control's by 0.47 ± 0.09 and 0.25 ± 0.08. Light is 20.8 % (4.3) and 18.8 % (4.2), higher by 4.2 ± 0.9 and 1.7 ± 0.5 points. At 50 that is over the 19.8 rule, which was tuned on the control's schedule: INFO, no verdict.
- **Limits.** S1 ran on master and KT on T1's commit. DECISIONS 114 records that step E, with its switch off, left stand trees seeds 1-3 identical to the control's, and that the merged master's golden runs (stand trees seeds 1 and 2 to 60 among them) match the tracked hashes. I did not recheck either, and neither covers seeds 4-20. The sources file's worked Finnish equation (its own SUSPECTED arithmetic) gives 4.5 / 5.3 / 6.3 m at 13 / 14 / 15 m for a planted stand at 1,600/ha: S1 is about 2 m under it across the window.

## 12. What T2 decides, under the plan's own rules (no target, band or gate was moved)

| Step | The plan's rule | What T2 read | Result |
|---|---|---|---|
| T2 itself | K and KT bit for bit; four readings before E | Identical in everything that grows. All four readings are now given. S1 ran late, and on master, not on T1's commit | **K and KT match bit for bit, and all four readings are now given. Two parts of the plan were not kept: E was built and screened before the readings (DECISIONS 114), and S1 ran on master `2d33997`, not on T1's commit. Both go to the maintainer to accept.** S1's lowest live branch is 2.48 m on the target's reading, 0.02 m under the written 2.5-4.5 m, and 4.09 m at its first thinning, inside it. "Still a miss of 5-7 m" held in 20 of 20 trees on both |
| Pay-first | Built only if the control log shows it would have acted | It would have: 7 new tree-years of 714,764, none after year 30; no tree alive at 30-60 was ever short | **The plan's condition is met. Not building it is my judgment on size, not the rule's result.** Flagged to the maintainer, who may ask for it |
| A new leader-light rule, or the tuned 0.6 | "If light never slows a tree, that is reported as a cause" | 0.021 % of leader-years | **Reported as a cause.** No rule in this plan; it needs its own design |
| E, status on height | After T2 and decisions 1, 2 | The control's rows are reproduced and the four readings given. Height SD at 45, E's adoption row, carries 0.07 m from points above stem tops | **By the plan's letter E waited on the readings. They are given now, so E may continue once the maintainer accepts the two departures in the row above; that is the maintainer's call, not something T2 settles.** E's 5-seed screens were started before the readings (DECISIONS 114), against the plan's order; a screen can only stop an arm, so nothing is adopted on one. N says stems differ in height only by the draw and germination year, so spread an arm adds to stem tops is the status rule's. An arm that changes limbs or crowns can also move reported height SD and top height (section 10). N also says the draw off height thins the young stand sooner |
| C2, crown space; EC | C2 only if C1 passed; EC only if E and C2 both pass alone | C1 failed, by its own report | **C2 is stopped by C1, not by T2, and EC stops with it.** T2 files C2's control rows (crown ratio 0.57 / 0.51 at 33 / 42; plot branch wood over A3 1.38 / 1.77 at 50 / 60) |
| B, arm A | Built only at 20 % or more at 50 and 60 | At 50 it is at the gate: 20.2 % as the mean of trees, 19.2 % pooled. At 60 it is 16.7 %, 2.2 SE under | **Stops: it misses the gate set before the read.** Not built |
| B, D0 first | "D0 first if it lands in the band" | 0.47 / 0.44, under 0.76-1.31 | **Not an arm.** D0 stays a diagnostic |
| B, the arms | "then rates, then the partner value" | The band lies between rate off and 0.30. A line through those two points puts A3 = 1.0 at 0.13-0.20, moving with the age and the line's form (SUSPECTED) | **Changes.** B's arms are rates in between (0.10, 0.15, 0.20), then `branch_sapwood_thick_m`. Decision 6(b) can now be put to the maintainer with the costs D0 shows: leaf (stand-tree LAI +0.46 at 60; the plots' Baltic row has 0.21 of room), stem (DBH +4.6 cm; the plots are 1.7 m²/ha under the 28.5 guard), and limbs moving away from the Nordic scans |
| R, release check | After all | – | Unchanged |

## What I could not compute, and why

1. **Which part of a plot tree stands above its stem, and the cause in any tree.** Tree lists hold no stem top, D0 has no limb log, and tracing the cause needs a run.
2. **Which trees the 149 light-slowed years belong to, and how hard pay-first would have cut a plot tree's leader.** The yearly log keeps counts. It doesn't name trees or keep the share paid. Per tree I have only the 19 list ages.
3. **The limb screen on forest trees, and D0's plot rows** (the basal area guard, plot LAI and light). The limb log and D0 are stand trees only.
4. **A measured spread at 50 or at 60** (the two stands are 45 and 67 years old), **wood-for-wood branch ratios** (no birch branch-bark share is opened), **and the tests row of the plan** (not T2's, and I ran nothing).

## What looks wrong or odd in the runs

1. **A tree's reported height can stand above the curve** (section 10). A stand tree's thinning schedule reads that height too. In S1 it brought the last thinning forward by two years in seed 8 and one year in seed 12. In S1's seed 10 a wind snap in year 45 took the tree under 20.5 m, and the schedule put the removed neighbours back for years 45-47 (700/ha). Seed 10 is 1.2 m under the curve at 50 in the control and 1.1 m in D0.
2. `tools/switch_off.py` reads `shedding.log_limbs` as a real difference (section 1). With the draw off height, the seedlings whose leader is cut for carbon in years 1-5 go from 221 to 396 on seeds 1-4.
3. K's folder is 246 MB; the plan guessed 150. A plot took 54-62 minutes and peaked at 6.1-6.9 GB. The server had 18 GB of disk free at the read and 17 GB at the correction, against the plan's floor of 10. Checks on my own reading: my plot and branch-wood rows equal `tools/independent_checks.py`'s on the same folders and the plan's control values. The line's definitions (Eqs. 3 and 52, the 12 cm rule) were read in the paper's text layer with a PDF text tool; the quoted line is the only quote.
