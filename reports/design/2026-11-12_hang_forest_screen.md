# Twig softness radius 0.0045: the 5-forest screen, read

2026-11-12. Reader: Fable 5.2 (ID `claude-fable-5-2`). The hang track's first forest run (DECISIONS 119): five plots grown with `mechanics.pendulous_radius` 0.0045 where today's value is 0.012, read against the control by the rules of `reports/design/2026-11-11_plan.md`, section 4. Read only: no model run, no test, no commit; this is the only file I wrote. The runs are the server's, fetched with `tools/node/fetch.sh`. On the PC I only read JSON and did arithmetic, with scripts in the session's scratch folder outside the repository. CONFIRMED = computed today from the fetched files, or read in a job's own command and log, or in the code. SUSPECTED = inferred. Every figure is CONFIRMED unless marked. A screen can only stop a setting: nothing is adopted here. The value is not sourced: today's 0.012 was tuned by eye, and 0.0045 would be tuned against six photos. **Checked by Opus 5.5 (ID `claude-opus-5-5`): every figure a verdict rests on was recomputed with its own code and matched. The check's corrections are made in this version:** why the forest floor is darker at 26-45 (section 3), the wording of items 1, 3 and 4 below, stem tops compared like with like (section 5), and one line in section 4. The figures those corrections needed were recomputed today from the fetched files with new code.

## In short
1. **This screen does not stop the setting.** In five forests grown with stiffer twigs, none of the plan's every-switch limits is broken at 50 or 60: light under the canopy, leaf area and top height all hold. Two limits the plan wrote for other steps would be missed if they bound this setting: no fall in basal area, at 60 (−0.48 ± 0.16 m²/ha, −3.1 SE), and no rise in branch wood over Repola's A3, at 50 (1.365 → 1.440, +4.0 SE, away from its band 0.76-1.31). Nothing is adopted; the two 20-forest runs decide.
2. **What stiffer twigs do to a forest tree:** its crown is 0.3-0.4 m wider and about 1 m shorter. The lowest live branch sits about 1 m higher from 45 on, and the crown takes 42 % / 38 % of the tree's height at 50 / 60, where today it takes 47 % / 42 %.
3. **Light at 50 and 60 did not move beyond noise** (+0.07 ± 0.43 and −0.48 ± 0.42 points). From 26 to 45 the forest floor is about 1 point darker: in years 26-35 mostly because each unit of leaf blocks more light, in years 36-45 because there is more leaf, at ages where the forest already carries too much. The project's own gate tool marks leaf area at 30, 40 and 45 as significantly worse; the plan's rule reads 50 and 60 only. That is a question for the owner.
4. **The stand has more and thinner stems at 50:** +32 ± 7 stems a hectare and −0.61 ± 0.15 cm of mean diameter. At 60 both shifts are inside noise (+16 ± 12; −0.70 ± 0.42). Basal area is 0.2 / 0.5 m²/ha lower at 50 / 60 (at 60 beyond noise) and stem wood 6 % / 5 % higher. Branch wood is 8 % / 9 % lower in tonnes, but against Repola's A3 for the trees' own, now shorter crowns (the tuned row) it reads further over its band: 1.365 → 1.440 at 50 (+4.0 SE) and 1.760 → 1.827 at 60 (+1.7 SE).
5. **What the 20-forest runs still have to show:** the same limits on 20 forests, where every uncertainty halves. Light at 60 has 0.32 points of room. Top height read 0.15 m lower at 60 here, inside noise; if that holds on 20 forests it breaks the owner's rule (SUSPECTED).

## The runs
| Label | What | Commit | Seeds | Set, on top of the plot command | Exit |
|---|---|---|---|---|---|
| `node_t2_k` | Control: today's 0.012 | `5cfec02` | 1-5 of its 20 | `log.stand=true` | 0 × 5 |
| `node_hang_f45` | Radius 0.0045 | `2d33997` | 1-5 | the control's, and `mechanics.pendulous_radius=0.0045` | 0 × 5 |
| `node_st_plots` | The defaults with stem tops recorded (the stem-top build's proof run, fetched today) | `17abd6e` | 1-2 | the control's, and `log.stem_tops=true` | 0 × 2 |
- Both commands: to year 60, 1,000 m², 16,000 seedlings a hectare, the same 19 tree lists. The manifests differ by the one setting and the commit. A 0.0045 plot took 54-60 minutes and peaked at 6.1-6.7 GB (the control: 59 minutes, 6.3-6.7 GB).
- **Paired.** At 11 every 0.0045 plot has the control's tree ids, places, germination years and draws (1,596-1,599 trees a plot). Storm years are the same in all five seeds. The first yearly row that differs is in years 6-8 (leaf area in four seeds, the stem count in one).
- **Two commits.** The control and the arm ran at different commits, and no default plot was grown at `2d33997`. `node_st_plots`, at a later commit that contains both, equals the control's seeds 1-2 in every value the control holds: all 120 yearly rows and 1,106,903 tree-list values. So the code between the two is SUSPECTED to change no growth. DECISIONS 114 records step E's switch-off check on its branch (plots seeds 1-2 identical to the control), which I did not repeat.

## 1. The screen, rule by rule (plan section 4, "every model switch")
Each cell: 50; 60. Means of the 5 plots. "In SE" is the paired difference over its standard error.

| Rule | Kind | Control, seeds 1-5 | 0.0045 | 0.0045 less control ± SE (in SE) | On this screen |
|---|---|---|---|---|---|
| Light under the canopy at most 19.8 % | tuned against | 19.45; 19.41 | 19.52; 18.93 | +0.07 ± 0.43 (+0.2); −0.48 ± 0.42 (−1.2) | Holds: 0.28 and 0.87 under the limit |
| LAI inside 3.6-5.4 | tuned against | 4.458; 4.357 | 4.490; 4.316 | +0.032 ± 0.063 (+0.5); −0.041 ± 0.039 (−1.0) | Holds |
| LAI, Baltic band: at most 4.5 at 60; at 50 not higher by more than 2 paired SE | tuned against | as above | as above | as above | Holds: 4.316 at 60; +0.5 SE at 50 |
| Top height, approved: inside SI 20-26 (18.76-25.12 m; 20.72-26.73 m), and no lower than today beyond noise (decision 1) | by design for stem tops only | 21.41; 23.28 | 21.36; 23.13 | −0.05 ± 0.10 (−0.5); −0.15 ± 0.13 (−1.1) | Holds: lower, by less than 2 SE |
| Stand trees: LAI 3.6-5.4, light at most 19.8 %, the curve holds the leader | tuned against; by design | 4.36; 4.29 and 18.45; 18.53 | 4.44; 4.35 and 17.54; 18.31 | +0.08 ± 0.08; +0.06 ± 0.06 and −0.91 ± 0.53; −0.22 ± 0.40 | Not this run. The hang track's 5 stand trees (seeds 1-5, recomputed from its saved file): inside, and within 0.01 m of the curve at 30, 50 and 60. The plan asks 20 trees and every year |
| Tests; switch off | – | – | – | – | Not part of a screen. The value is given on the command line and no code changed; its "off" is today's 0.012, the control |
| No approved row from pass to fail | – | – | – | – | Holds: `tools/gate.py` finds no row that leaves its band |
- **Result: not stopped.** No rule of this table is missed, so none is missed by 2 paired SE.
- **The gate tool's other finding.** On the same ten plots it lists three rows as significantly worse, each already outside its band in the control: Baltic LAI at 30 (5.505 → 5.650, +2.3 SE), at 40 (4.842 → 5.047, +4.5 SE) and at 45 (4.785 → 4.870, +2.7 SE). I ran it as a correction, because it refuses to compare two commits as an option. It lists no row as improved. The plan's table reads this row at 50 and 60 only, and calls young LAI a recorded miss (its section 7). PROTOCOL 9, item 4, lets no target get significantly worse. Which of the two binds here is the owner's call (question 1).
- **Rows the plan wrote for other steps, printed here; none is its rule for this setting.**
  - Do no harm (E, C2), at 45 / 50 / 60: height SD −0.2 / −0.9 / −1.2 SE; height range +0.4 / −0.3 / −1.97 SE; DBH spread +0.1 / +0.2 SE (60 is printed only: −1.1). None is past 2 SE; the height range at 60 is at the line.
  - Basal area (B): at most 28.5 holds (highest plot 27.90 at 60). Not lower by more than 2 paired SE: −0.9 / −0.8 / **−3.1 SE** at 45 / 50 / 60. Missed at 60, if it bound.
  - Plot branch wood over A3 must not rise by more than 2 paired SE at 50 or 60 (C2): **+4.0 SE** at 50, +1.7 at 60. Missed at 50, if it bound.
- Plots over 19.8 %: at 50, seed 5 in the control and seeds 3 and 5 at 0.0045; at 60, seeds 3 and 4 in the control and seed 4 at 0.0045. Over years 45-60: 9 of 80 plot-years in the control, 14 of 80 at 0.0045.

## 2. Every row at 30, 45, 50 and 60
Each cell: control mean (SD over the 5 plots) → 0.0045 mean (SD); then 0.0045 less control, paired by seed, ± its standard error; * = more than 2 SE. Seeds 1-5 only, so the control differs a little from T2's 20-seed figures (light at 50: 19.45 here, 18.22 on 20).

| Row (kind) | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| **Light under the canopy, %** (tuned against; at most 19.8 at 50 and 60) | 15.95 (0.55) → 14.69 (0.51); −1.27 ± 0.24 * | 17.46 (0.50) → 16.58 (0.74); −0.88 ± 0.30 * | 19.45 (0.65) → 19.52 (1.56); +0.07 ± 0.43 | 19.41 (0.70) → 18.93 (1.24); −0.48 ± 0.42 |
| **LAI** (tuned against; 3.6-5.4; Baltic top 4.5) | 5.505 (0.139) → 5.650 (0.112); +0.145 ± 0.063 * | 4.785 (0.081) → 4.870 (0.040); +0.085 ± 0.032 * | 4.458 (0.137) → 4.490 (0.191); +0.032 ± 0.063 | 4.357 (0.101) → 4.316 (0.078); −0.041 ± 0.039 |
| **Basal area, m²/ha** (tuned against; guard 28.5) | 18.94 (0.84) → 18.57 (0.41); −0.36 ± 0.25 | 24.30 (0.64) → 23.94 (0.61); −0.36 ± 0.39 | 24.42 (0.20) → 24.19 (0.60); −0.23 ± 0.30 | 27.23 (0.79) → 26.74 (1.02); −0.48 ± 0.16 * |
| **Stems/ha** (tuned against) | 2694 (159) → 2954 (245); +260 ± 55 * | 876 (74) → 912 (36); +36 ± 28 | 666 (40) → 698 (47); +32 ± 7 * | 480 (42) → 496 (29); +16 ± 12 |
| Dg, cm (tuned against) | 9.47 (0.47) → 8.97 (0.43); −0.51 ± 0.05 * | 18.83 (0.67) → 18.29 (0.45); −0.54 ± 0.19 * | 21.63 (0.70) → 21.03 (0.52); −0.61 ± 0.15 * | 26.92 (0.86) → 26.22 (0.82); −0.70 ± 0.42 |
| **Share of the self-thinning line's stems** (INFO) | 0.649 (0.026) → 0.640 (0.012); −0.009 ± 0.008 | 0.838 (0.025) → 0.825 (0.026); −0.013 ± 0.018 | 0.852 (0.010) → 0.843 (0.023); −0.009 ± 0.009 | 0.967 (0.028) → 0.944 (0.034); −0.023 ± 0.004 * |
| **Top height, approved, m** (by design for stem tops only) | 15.22 (0.17) → 15.24 (0.19); +0.02 ± 0.01 * | 20.35 (0.24) → 20.35 (0.14); +0.00 ± 0.10 | 21.41 (0.28) → 21.36 (0.26); −0.05 ± 0.10 | 23.28 (0.27) → 23.13 (0.40); −0.15 ± 0.13 |
| The same, each tree capped at its rebuilt stem limit (SUSPECTED at 45-60) | 15.22 (0.17) → 15.24 (0.19); +0.02 ± 0.01 * | 20.18 (0.21) → 20.17 (0.14); −0.01 ± 0.06 | 21.35 (0.28) → 21.32 (0.26); −0.03 ± 0.08 | 23.27 (0.27) → 23.12 (0.40); −0.14 ± 0.13 |
| Mean height of the 100 thickest/ha, m (model record) | 15.60 (0.14) → 15.62 (0.10); +0.02 ± 0.05 | 20.55 (0.20) → 20.50 (0.26); −0.04 ± 0.10 | 21.63 (0.24) → 21.47 (0.29); −0.16 ± 0.11 | 23.40 (0.21) → 23.18 (0.38); −0.22 ± 0.14 |
| **Height SD, m** (independent; guide row at 45; measured 3 at 45) | 0.836 (0.050) → 0.852 (0.036); +0.016 ± 0.015 | 1.055 (0.051) → 1.048 (0.095); −0.006 ± 0.035 | 1.099 (0.076) → 1.050 (0.100); −0.049 ± 0.053 | 1.119 (0.149) → 1.042 (0.088); −0.077 ± 0.064 |
| Height, 10th to 90th percentile, m (independent) | 2.07 (0.09) → 2.19 (0.09); +0.12 ± 0.02 * | 2.60 (0.33) → 2.67 (0.34); +0.07 ± 0.18 | 2.66 (0.38) → 2.60 (0.32); −0.05 ± 0.16 | 2.84 (0.50) → 2.44 (0.44); −0.40 ± 0.20 |
| **DBH SD over mean** (independent; guide row at 45; measured 0.32 at 45) | 0.123 (0.005) → 0.121 (0.007); −0.002 ± 0.002 | 0.146 (0.007) → 0.147 (0.014); +0.001 ± 0.009 | 0.150 (0.009) → 0.151 (0.008); +0.001 ± 0.006 | 0.151 (0.005) → 0.147 (0.005); −0.004 ± 0.004 |
| **Plot branch wood over Repola's A3, own crown length** (tuned against) | 1.131 (0.061) → 1.244 (0.053); +0.113 ± 0.009 * | 1.191 (0.032) → 1.312 (0.031); +0.121 ± 0.017 * | 1.365 (0.051) → 1.440 (0.027); +0.075 ± 0.019 * | 1.760 (0.037) → 1.827 (0.058); +0.067 ± 0.040 |
| The same over Eq. 9 (tuned against) | 1.319 (0.069) → 1.461 (0.059); +0.142 ± 0.008 * | 1.102 (0.030) → 1.104 (0.033); +0.002 ± 0.014 | 1.137 (0.043) → 1.093 (0.025); −0.044 ± 0.011 * | 1.240 (0.032) → 1.186 (0.032); −0.054 ± 0.024 * |
| The same over A3 at crown ratio 0.58 (tuned against) | 1.182 (0.050) → 1.291 (0.042); +0.109 ± 0.007 * | 1.068 (0.028) → 1.055 (0.020); −0.013 ± 0.014 | 1.136 (0.029) → 1.077 (0.013); −0.059 ± 0.012 * | 1.295 (0.021) → 1.223 (0.039); −0.071 ± 0.022 * |
| Branch wood, t/ha (model record) | 7.35 (0.41) → 7.42 (0.34); +0.06 ± 0.07 | 15.86 (0.55) → 15.04 (0.44); −0.82 ± 0.12 * | 18.89 (0.53) → 17.36 (0.61); −1.53 ± 0.38 * | 27.68 (0.91) → 25.28 (0.72); −2.40 ± 0.35 * |
| Stem wood, t/ha (model record) | 48.4 (2.3) → 48.1 (1.4); −0.3 ± 0.6 | 94.6 (2.9) → 98.6 (2.4); +4.0 ± 1.5 * | 103.5 (2.4) → 109.5 (4.1); +6.0 ± 1.6 * | 132.6 (5.6) → 139.3 (7.3); +6.7 ± 1.3 * |
| **Crown ratio, all stems** (seen, INFO) | 0.603 (0.009) → 0.596 (0.008); −0.007 ± 0.003 * | 0.500 (0.008) → 0.446 (0.005); −0.055 ± 0.003 * | 0.468 (0.006) → 0.415 (0.005); −0.052 ± 0.003 * | 0.419 (0.005) → 0.378 (0.005); −0.041 ± 0.003 * |
| **Lowest live branch, m, all stems** (seen, INFO) | 5.24 (0.11) → 5.36 (0.09); +0.12 ± 0.02 * | 9.17 (0.21) → 10.16 (0.14); +0.99 ± 0.06 * | 10.39 (0.20) → 11.44 (0.10); +1.05 ± 0.10 * | 12.48 (0.07) → 13.32 (0.16); +0.85 ± 0.06 * |
| The same, the 100 thickest/ha | 4.97 (0.31) → 4.92 (0.15); −0.05 ± 0.20 | 8.60 (0.38) → 9.94 (0.28); +1.34 ± 0.24 * | 10.31 (0.29) → 11.39 (0.33); +1.08 ± 0.14 * | 12.45 (0.21) → 13.71 (0.21); +1.26 ± 0.14 * |
| Crown width, m, all stems (model record) | 1.96 (0.08) → 2.09 (0.07); +0.12 ± 0.01 * | 3.72 (0.13) → 3.97 (0.08); +0.25 ± 0.04 * | 4.22 (0.11) → 4.49 (0.08); +0.27 ± 0.03 * | 5.22 (0.17) → 5.63 (0.14); +0.40 ± 0.06 * |
| The same, the 100 thickest/ha | 2.06 (0.05) → 2.33 (0.10); +0.27 ± 0.04 * | 3.94 (0.14) → 4.47 (0.14); +0.53 ± 0.08 * | 4.43 (0.15) → 4.98 (0.10); +0.55 ± 0.07 * | 5.49 (0.19) → 6.13 (0.13); +0.64 ± 0.08 * |
| Crown length, m (model record) | 8.31 (0.22) → 8.20 (0.16); −0.11 ± 0.06 | 9.49 (0.16) → 8.43 (0.09); −1.06 ± 0.07 * | 9.38 (0.12) → 8.31 (0.15); −1.07 ± 0.04 * | 9.20 (0.16) → 8.26 (0.21); −0.94 ± 0.12 * |
| Summed crown area over the ground (model record) | 0.816 (0.018) → 1.012 (0.022); +0.196 ± 0.011 * | 0.954 (0.025) → 1.137 (0.020); +0.183 ± 0.014 * | 0.935 (0.024) → 1.114 (0.044); +0.179 ± 0.017 * | 1.029 (0.030) → 1.242 (0.033); +0.214 ± 0.022 * |
| Leaf area over the tree's own crown area (model record) | 6.72 (0.06) → 5.55 (0.05); −1.17 ± 0.03 * | 4.98 (0.05) → 4.24 (0.08); −0.74 ± 0.05 * | 4.73 (0.07) → 3.98 (0.10); −0.74 ± 0.02 * | 4.20 (0.07) → 3.46 (0.13); −0.74 ± 0.07 * |
| Leaf area a tree, m² (model record) | 20.5 (1.6) → 19.2 (1.5); −1.3 ± 0.2 * | 54.9 (3.9) → 53.5 (1.9); −1.4 ± 1.6 | 67.1 (2.9) → 64.5 (3.3); −2.6 ± 1.1 * | 91.2 (6.4) → 87.3 (5.4); −4.0 ± 2.7 |
| Gap fraction (model record) | 0.003 (0.003) → 0.001 (0.002); −0.002 ± 0.002 | 0.024 (0.013) → 0.004 (0.004); −0.020 ± 0.005 * | 0.041 (0.015) → 0.033 (0.017); −0.008 ± 0.006 | 0.033 (0.015) → 0.015 (0.014); −0.018 ± 0.002 * |
| −ln(light) / LAI (model record) | 0.334 (0.012) → 0.340 (0.004); +0.006 ± 0.004 | 0.365 (0.006) → 0.369 (0.010); +0.004 ± 0.004 | 0.367 (0.008) → 0.364 (0.009); −0.003 ± 0.005 | 0.376 (0.002) → 0.386 (0.011); +0.010 ± 0.005 |
| Carbon fixed in the year per m² of leaf (model record) | 1037 (5) → 1036 (7); −2 ± 1 | 1127 (10) → 1168 (12); +41 ± 4 * | 1165 (10) → 1210 (13); +45 ± 6 * | 1192 (8) → 1230 (10); +37 ± 4 * |
| Share of trees over 0.3 m above their rebuilt stem limit (SUSPECTED at 45-60) | 0.000 (0.000) → 0.000 (0.000); +0.000 ± 0.000 | 0.125 (0.064) → 0.112 (0.054); −0.014 ± 0.025 | 0.056 (0.032) → 0.059 (0.036); +0.003 ± 0.024 | 0.021 (0.002) → 0.012 (0.011); −0.009 ± 0.006 |
- **Branch wood.** It falls by 8 % / 9 % at 50 / 60 in t/ha. Over Eq. 9 and over A3 at crown ratio 0.58 the ratio moves toward 1. Over A3 at the tree's own crown length it moves away, because A3's own figure falls more (13.85 → 12.06 t/ha at 50) with crowns 1 m shorter and stems thinner. At 30 all three ratios rise by 0.11-0.14.
- **Crown ratio at the Swedish stand's ages** (seen, INFO; a guide row by DECISIONS 111): at 33, 0.566 → 0.554 (−0.012 ± 0.002 *), measured 0.50 ± 0.07; at 42, 0.512 → 0.464 (−0.048 ± 0.004 *), measured 0.42 ± 0.03. Toward the measured stand, not past it.
- **Lowest live branch when top height first reads 13-15 m** (the scorecard's reading on the 100 thickest; seen, INFO; the guide says 5-7 m): 2.73 → 2.45 m. One control plot is read at year 26 and the other nine at 25, so that pair is not like for like. At year 25 in all ten plots: 2.59 → 2.45 m (−0.14 ± 0.16), no change found. A miss of the guide on both sides.
- **Stem tops.** The lists hold no stem top, so each tree's stem limit is rebuilt as T2 did. Highest points add 0.16 / 0.05 / 0.01 m to the control's top height at 45 / 50 / 60 and 0.18 / 0.04 / 0.01 m at 0.0045. Stiffer twigs add no height above the stems.
- **Thinning comes later.** Trees that died in the five plots: 5,857 → 5,723 in years 11-30 and 909 → 1,021 in years 31-45.

## 3. What a stiffer or softer twig changes in a forest, and why
- **What the setting is** (read on master in `treegen/mechanics.py:40-43, 103-110`, `treegen/growth.py:2759-2768` and the species file's own note at lines 598-601). One factor, r⁴ / (r⁴ + radius⁴), scales a twig's stiffness and its posture correction, and a new shoot's pull toward its aim and, from order 2, toward light. Wood 12 mm across counts as 5.9 % stiff at 0.012 and 76 % at 0.0045; wood 6 mm across as 0.4 % and 16.5 % (my arithmetic).
- **Leaf placement.** Leaf that hung under the limbs is held out. The crown is 6-8 % wider (about 13 % in the thickest trees) and 10-11 % shorter from 45 on. Leaf area over a tree's own crown area falls from 4.73 / 4.20 to 3.98 / 3.46 at 50 / 60. Crowns summed over the ground go from 0.94 / 1.03 to 1.11 / 1.24 of it, so they overlap more.
- **Light.** Gaps close: the gap fraction is 0.004 → 0.001 over years 26-35, 0.020 → 0.005 over years 36-45 and 0.033 → 0.015 at 60. The floor is 1.0 point darker from 26 to 45. At 50 and 60 no change is found.
- **Why the floor is darker at 26-45: first the leaf blocks more, then there is more leaf** (the check's correction; recomputed today). How much light a unit of leaf blocks is −ln(light) / LAI. The change in ln(light) splits exactly into a part from that figure and a part from LAI.
  - **Years 26-35: the leaf blocks more light per unit of leaf.** −ln(light) / LAI is 0.3445 → 0.3511: +0.0067, or 1.9 %, and +0.0065 to +0.0068 in each of the five seeds. LAI is 1.4 % higher (+0.075). Of the window's change in ln(light), −0.062, leaf that blocks more gives −0.037 (60 %) and more leaf gives −0.025 (40 %): about 0.6 and 0.4 of the 0.97 points. Year by year the figure is over 2 SE in years 26, 27, 28, 29 and 31 (+0.007 to +0.017; 2.3 to 4.6 SE).
  - **Years 36-45: there is more leaf.** LAI is 3.4 % higher (+0.166). −ln(light) / LAI is 0.3588 → 0.3596 (+0.0008 ± 0.0004, inside 2 SE). Of the change in ln(light), −0.063, more leaf gives −0.059 (94 %): about 1.0 of the 1.06 points.
  - My first version said the figure "is the same at every age", from the four ages section 2 prints, and so put the whole darker floor down to more leaf. That was wrong for years 26-35. Why the leaf blocks more there is SUSPECTED: it is held out wider and leaves fewer gaps (summed crown area over the ground 0.82 → 1.01 at 30).
- **Why more leaf at 30-45** (SUSPECTED; no run traced it). The stand thins later, so more and thinner stems stand (+260 a hectare at 30), each with 6 % less leaf, and together they hold more.
- **Why the lowest branch rises** (SUSPECTED; the lists hold no limb light). Wider crowns above and beside shade the low limbs sooner. It starts after 30: +0.12 m at 30, +0.69 m at 40, +0.99 m at 45 (all stems).
- **Carbon.** From 45 on a square metre of leaf fixes 3-4 % more. Stem wood rises 4-6 % and branch wood falls 5-9 %. With more stems sharing it, each stem is 0.5-0.7 cm thinner.
- **A softer twig is the reverse,** and it is today's forest: narrower, deeper crowns with leaf hung below the limbs, more gaps, and about 1 point more light from 26 to 45.

Each seed's mean over the window, then paired; * = more than 2 SE.

| Row (kinds as in section 2) | Years 26-35 | Years 36-45 | Year 50 | Years 51-60 | Year 60 |
|---|---|---|---|---|---|
| Light under the canopy, % | 15.59 → 14.62; −0.97 ± 0.06 * | 17.65 → 16.59; −1.06 ± 0.07 * | 19.45 → 19.52; +0.07 ± 0.43 | 18.69 → 18.68; −0.01 ± 0.19 | 19.41 → 18.93; −0.48 ± 0.42 |
| LAI | 5.411 → 5.486; +0.075 ± 0.011 * | 4.839 → 5.005; +0.166 ± 0.012 * | 4.458 → 4.490; +0.032 ± 0.063 | 4.435 → 4.439; +0.005 ± 0.024 | 4.357 → 4.316; −0.041 ± 0.039 |
| −ln(light) / LAI | 0.3445 → 0.3511; +0.0067 ± 0.0001 * | 0.3588 → 0.3596; +0.0008 ± 0.0004 | 0.3675 → 0.3644; −0.0031 ± 0.0052 | 0.3788 → 0.3789; +0.0002 ± 0.0009 | 0.3764 → 0.3860; +0.0096 ± 0.0054 |
| Gap fraction | 0.004 → 0.001; −0.002 ± 0.001 * | 0.020 → 0.005; −0.015 ± 0.002 * | 0.041 → 0.033; −0.008 ± 0.006 | 0.035 → 0.026; −0.009 ± 0.003 * | 0.033 → 0.015; −0.018 ± 0.002 * |
| Stems/ha | 2784 → 2949; +165 ± 26 * | 1147 → 1217; +69 ± 19 * | 666 → 698; +32 ± 7 * | 555 → 580; +25 ± 11 * | 480 → 496; +16 ± 12 |
| Basal area, m²/ha | 19.05 → 18.66; −0.39 ± 0.07 * | 22.80 → 22.66; −0.14 ± 0.11 | 24.42 → 24.19; −0.23 ± 0.30 | 25.91 → 25.73; −0.18 ± 0.25 | 27.23 → 26.74; −0.48 ± 0.16 * |

## 4. What the 20-forest runs have to show
"2 SE on 20" is twice this screen's paired SD over √20, which equals this screen's own SE. It is SUSPECTED: an SD from five seeds is good to a factor of 0.6-2.9.

| Rule (kind as in section 1) | Control on 20 seeds: 50; 60 | Room to the limit | Shift on this screen | 2 SE on 20 | The 20 forests must show |
|---|---|---|---|---|---|
| Light at most 19.8 % | 18.22; 19.48 | 1.58; 0.32 | +0.07 ± 0.43; −0.48 ± 0.42 | 0.43; 0.42 | A 20-plot mean at or under 19.8 at both ages, with no rounding |
| LAI inside 3.6-5.4 | 4.512; 4.287 | 0.89; 0.69 | +0.032 ± 0.063; −0.041 ± 0.039 | 0.063; 0.039 | The mean inside the band at both ages |
| LAI, Baltic band | 4.512 (fails by 0.012 today); 4.287 | –; 0.21 | as above | as above | At 60 a mean at or under 4.5. At 50 a shift of no more than +2 paired SE |
| Top height, approved, m | 21.39; 23.14 | – | −0.05 ± 0.10; −0.15 ± 0.13 | 0.10; 0.13 | Not lower than the control by more than 2 paired SE, and inside 18.76-25.12; 20.72-26.73 |
| Basal area at most 28.5 m²/ha | 24.70; 26.78 | 3.80; 1.72 | −0.23 ± 0.30; −0.48 ± 0.16 | 0.30; 0.16 | A mean at or under 28.5 |
| Stand trees; no approved row from pass to fail | – | – | – | – | Stand trees exist on seeds 1-5 only at each radius; the plan asks 20 (question 5). The gate tool on all 20 pairs: no row leaves its band |
- **Light at 60 is the tight row.** The room is 0.32 points and 2 SE on 20 forests is about 0.42, so 20 forests cannot tell a shift of +0.3 from none; 33 would be needed (the hang report worked out 21-41 before any plot ran). The plan's rule is the mean alone. The control's 20-seed mean plus this screen's shift gives 18.29 / 18.99 % (SUSPECTED).
- **If the mean is over 19.8,** the plan's one repeat on seeds 21-40 is written for a sourced option. This value is tuned (question 4).
- **If this screen's shifts hold on 20 forests (SUSPECTED), these rows cross 2 SE:** top height at 60 (−0.15 m, −2.2 SE: a miss of decision 1's rule); and, among the rows the plan wrote for other steps, basal area at 60 (−6 SE), the height range at 60 (−3.9 SE), height SD at 60 (−2.4 SE) and branch wood over A3 at 50 (+8 SE). Baltic LAI at 30-45 would stay significantly worse.
- **Holding these rows would not adopt the value** (the check's point). It is tuned, not sourced, so item 1 of PROTOCOL 9's adoption gate is not met. On this screen the gate tool lists no scorecard row it improves (the improvement rule) and three it makes significantly worse (item 4; question 1). By DECISIONS 119 (b) the owner sees the forest numbers and pictures before anything becomes the default.

## 5. The full reading: the rows, the paired control and the join
| Run | Seeds | Commit | Set, on top of the control's command | Stem tops recorded | Paired control |
|---|---|---|---|---|---|
| `node_hang_f47` | 1-20 | `2fd46f0` | radius 0.0047, `log.stem_tops=true` | yes | `node_t2_k`, seeds 1-20 (`5cfec02`) |
| 0.0045, part 1: `node_hang_f45` (this screen) | 1-5 | `2d33997` | radius 0.0045 | no | `node_t2_k`, seeds 1-5 |
| 0.0045, part 2: `node_hang_f45b` | 6-20 | `2fd46f0` | radius 0.0045, `log.stem_tops=true` | yes | `node_t2_k`, seeds 6-20 |

| Rows: means with SD over the 20 plots, and paired differences with their SE, at 30, 45, 50 and 60 | Read from | Control |
|---|---|---|
| The rule table of section 1 and the table of section 4, at 50 and 60 | as below | `node_t2_k`, the same seed |
| Light, LAI, basal area, stems, Dg, gap fraction; the windows of section 3 | `plot.json`, yearly rows | the same |
| Approved top height; mean height of the 100 thickest | `stand_log.json` | the same |
| Height SD and range, DBH spread, share of the self-thinning line, branch wood three ways, stem wood, crown ratio (also at 33 and 42), lowest live branch (also at 13-15 m of top height), crown width and length, summed crown area, leaf area a tree | the 19 tree lists | the same |
| Top height and height SD on stem tops; trees standing over their stem top. **Like with like: rebuilt on both sides** | the tree lists, all 20 seeds of each arm: each tree counted no taller than its rebuilt stem limit, as in section 2 | `node_t2_k`, the same seed, rebuilt the same way |
| The same on recorded stem tops, printed beside it | the arm's `stem_log.json` and `stem_top_m` (0.0047: seeds 1-20; 0.0045: seeds 6-20) | Recorded against recorded only: `node_st_plots`, seeds 1-2. So 0.0047 has two such pairs and 0.0045 has none |
| The gate's band checks at 20, 30, 40, 45, 50 and 60 | `tools/gate.py` on the 20 pairs | `node_t2_k` |
| 0.0047 less 0.0045, paired by seed | both arms, 20 seeds | – |
- **0.0047 needs no join:** one commit, one command, 20 seeds.
- **How the two parts of 0.0045 are joined.** Seeds 1-5 of part 1 and seeds 6-20 of part 2 are stacked into 20 paired differences against `node_t2_k`. The two parts differ in the commit and in the stem-top record.
  - The record changes no growth: `node_st_plots` equals the control's seeds 1-2 value for value (computed today).
  - The code: from `2d33997` to `2fd46f0` the engine gains the stem-top record (`growth.py`, `plot.py`, `logs.py`), a pass-through for two thinning switches that are off (`growth.py`, `damage.py`, `plot.py`) and a leaf look that is off at that commit. No changed line in the engine or the species file names the softness radius. Engine and species files are the same at `17abd6e` and `2fd46f0`. Read in the diffs today; the leaf look's own diff was not read.
  - So the join is CONFIRMED for the defaults and SUSPECTED for 0.0045 itself: no 0.0045 plot has been grown at both commits.
  - The check to make when part 2 arrives: each row's paired difference on seeds 1-5 beside the same on seeds 6-20; they should agree within noise. Print the 0.0045 result on seeds 6-20 alone beside all 20.
  - The direct proof, not run (question 3): grow 0.0045 seeds 1-2 at `2fd46f0` with stem tops and hold them against this screen's plots with `tools/plots_identical.py`. Two plot-hours; five give stem tops on all 20.
- **Stem tops, like with like** (the check's correction). My first version set the arms' recorded stem tops against the control's rebuilt limits on seeds 3-20. That pairs two measures. A rebuilt limit takes the light and water factors as 1, so tree by tree it stands at or above the stem top wherever a leader was slowed or broken, and the two sides were not slowed alike: by light in 66 leader-years at 0.0045 against 34 (of about 182,000 on each side), by water in 271 on both.
  - **The paired stem-top rows use rebuilt limits on both sides, on all 20 seeds.** 0.0045 seeds 1-5 have no recorded stem top, so they use rebuilt limits, as their control does. The recorded reading of 0.0045 therefore has 15 plots (seeds 6-20), not 20.
  - **Recorded against recorded** is printed where both sides hold a record: seeds 1-2 of 0.0047. No seed of 0.0045 holds one on both sides.
  - **The size of the bias is printed:** each arm's own recorded-less-rebuilt difference in every stem-top row, on the seeds that hold a record (0.0047: 1-20; 0.0045: 6-20).
  - **That difference on the default's seeds 1-2** (computed today): top height 0.00 m at 30, 45 and 60, and +0.02 m in one of the two plots at 50, where height SD differs by +0.07 m. Tree by tree the rebuilt limit equals the recorded stem top to 0.01 m in all 997 trees at 30, 40 and 45 and in 239 of 241 at 50 and 60. The other two are 2.66 and 1.92 m under their limit (SUSPECTED: a broken stem).
  - **On this screen's ten plots** neither side holds a record. Living stems more than 0.05 m under their rebuilt limit, where that limit is surely too high: 3 / 7 / 2 in the control at 45 / 50 / 60 (of 438 / 333 / 240) and 1 / 3 / 2 at 0.0045 (of 456 / 349 / 248). A lower bound: a stem top under a higher limb does not show.
- **State at the read** (09:08, server time): `node_hang_f47` had 3 of 20 plots done and `node_hang_f45b` 0 of 15, three at a time. SUSPECTED finish: early afternoon. Free disk 18 GB against the floor of 10.

## Questions only the owner can answer
1. **Young leaf area.** At 30-45 the forest carries 0.09-0.21 more LAI at 0.0045, where it is already over the Baltic band. The plan reads that band at 50 and 60 only; the project's gate counts 30, 40 and 45 as significantly worse. Does that stop the setting, or is it recorded as a wider miss?
2. **Rows written for other steps.** No fall in basal area (written for the branch step) is crossed at 60, and no rise in branch wood over A3 (written for the crown step) at 50. Do those, and the do-no-harm rows on spread, bind a look setting? I changed nothing and judged by the every-switch table.
3. **Seeds 1-5 of 0.0045.** Accept the join as described, or grow two or five of them again at the new commit with stem tops recorded? Without five, the recorded stem-top reading of 0.0045 has 15 plots.
4. **Light at 60.** If a 20-forest mean comes out over 19.8 %, may a tuned value have the one repeat on seeds 21-40, or is it blocked?
5. **Stand trees.** The plan's rule asks 20 stand trees for a model change; only seeds 1-5 exist at each radius. Run 20 at the radius that goes forward?

## Not done, and limits
1. Five seeds give a standard error with 4 degrees of freedom, so a 2 SE line is looser than it looks. Section 2 has 120 cells and some cross 2 SE by chance; basal area at 60 (3.1 SE) may be one. The crown rows (6-28 SE) are not.
2. The hang itself was not measured in the forest: plots keep no geometry, so the near-vertical share exists for single trees only. No picture of a forest was made or looked at.
3. Stem tops are rebuilt, not read, on both sides. Limb light and the height of the leaf are not in the lists, so each "why" in section 3 is SUSPECTED. The split of the darker floor into leaf that blocks more and more leaf is arithmetic on the yearly rows, CONFIRMED; what makes the leaf block more is not.
4. Not read: 0.0047 in a forest; the two 20-forest runs (not finished); 20 stand trees; the tests. No default plot exists at this screen's commit.

## How I checked
- My measures on the control's 20 seeds equal T2's twice-checked figures in all 14 rows I reuse, at every age T2 prints them. The scripts are new, written from T2's definitions.
- `tools/gate.py` (control seeds 1-5 against the arm, six ages) gives the same means, paired differences and SEs for light, LAI and top height. `tools/independent_checks.py` gives the same basal area, DBH spread, height SD, branch wood in t/ha and all three branch ratios. My approved top height equals the plots' own logged figure to 0.00005 m in all ten plots.
- Odd in the runs: at 0.0045 one death in seed 3, year 30, carries no named cause ("died"); the control has none. Light slowed a leader in 66 leader-years at 0.0045 against 34 (0.036 % against 0.019 %).
- For this version, with new code from the fetched files: the split of the darker floor (section 3; the two parts sum to the change in ln(light) exactly, and the other order of the split gives 61 % and 93 %), the figures in items 1 and 4 of the summary, and the stem-top comparison on the default's seeds 1-2 (my top height on recorded stem tops equals the plots' own `stem_log.json` to 0.001 m at 30, 45, 50 and 60).
