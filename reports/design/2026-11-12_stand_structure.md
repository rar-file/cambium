# Stand structure: why the forest is too even, and a design

2026-11-12. Model: Fable 5.2 (ID `claude-fable-5-2`). Read only: no model run, no test, no server job, no model code. This is the only file I wrote. Data: the fetched runs in `out/bench/ensemble/` (`node_t2_k`, 20 control plots, called K; `node_t2_n`, 4 plots with the draw off height, N; `node_e_s5_birch_6c0ebb6`, 5 plots under birch's own height rule, BIRCH). On the PC I only read JSON and did arithmetic with new scripts in the session's scratch folder. CONFIRMED = computed today from those files, or read today at the source named. SUSPECTED = inferred, or my arithmetic on published numbers. Every cell is a mean over plots with the SD over plots in brackets unless it says otherwise. The spread targets are reported rows in `tools/independent_checks.py` (kind "independent"; guide rows at 45, plan section 8.1): DBH SD over mean 0.32 at 45 and 0.12 at 67, height SD 3 m at both, from Hagemeier & Leuschner 2019, Table 3, one stand per age. No target is changed here.

## In five lines

1. **In the model only two things make trees differ: a random draw and the year a tree came up.** Neighbours, place and damage together add about one twentieth to a tree's diameter and nothing to the height of its stem.
2. **Real self-sown birch stands start very uneven and lose it slowly.** Diameter spread is 0.62 at 8-9 years, 0.46 at 17-18 and 0.36 at 22-23 in four untreated Czech stands (one stand per age). The model has 0.53 at 11 but 0.16 at 20 and 0.13 at 30, because its late trees catch up; by the published birch rule they would fall behind.
3. **The model's deaths are close to a lottery.** Of the trees that die at 24-30, 40 % are of mean diameter or thicker. A tree in the thickest fifth at 20 has an 88 % chance of being dead by 60. A tree that does fall behind is gone in about two years. The published birch model all but spares large trees and lets small ones linger for years.
4. **The published rules do not make an even forest uneven.** Carried forward on paper, the model's own stand stays at 0.14-0.15. A stand that starts as uneven as a measured one keeps 0.18-0.24, and 1.9-2.7 m of height spread, at 45-60.
5. **The design is four parts that only work together, each a switch that is off:** a patchy start, height by standing (built already), death by standing (the published survival rule; the one to build first), and a vigour spread of measured size. I expect about 0.16-0.22 at 45, not the 0.32 of the one measured stand, whose history its paper doesn't state.

## 1. The model's variance budget (CONFIRMED)

Shares of the variance among living trees, per plot, adjusted for the number of terms, added in this order: the draw; germination year; crowding at the start (stems within 2 m, those that came up no later, nearest stem); density now (living stems within 3, 5 and 8 m, their basal area within 5 m, nearest stem); damage (snow bends, snaps that didn't kill). "Left" is the rest. First the control K, 20 plots.

| Row | 20 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| Height SD, reported height, m | 0.78 (0.02) | 0.85 (0.04) | 1.04 (0.07) | 1.06 (0.09) | 1.09 (0.13) |
| the draw | 0.44 (0.03) | 0.79 (0.02) | 0.84 (0.03) | 0.90 (0.06) | 0.97 (0.02) |
| germination year | 0.54 (0.03) | 0.21 (0.02) | 0.05 (0.01) | 0.02 (0.01) | 0.02 (0.01) |
| crowding at the start; density now; damage | 0.00; 0.00; 0.00 | 0.00; 0.00; 0.00 | 0.00; 0.00; 0.00 | 0.00; 0.00; 0.02 | 0.00; 0.00; 0.00 |
| left | 0.01 (0.02) | 0.00 (0.00) | 0.11 (0.04) | 0.05 (0.03) | 0.01 (0.01) |
| DBH, SD over mean | 0.161 (0.005) | 0.129 (0.008) | 0.143 (0.013) | 0.148 (0.015) | 0.148 (0.016) |
| the draw | 0.40 (0.03) | 0.55 (0.04) | 0.71 (0.06) | 0.75 (0.05) | 0.78 (0.06) |
| germination year | 0.58 (0.03) | 0.29 (0.03) | 0.11 (0.03) | 0.08 (0.03) | 0.06 (0.05) |
| crowding at the start; damage | 0.00; 0.00 | 0.00; 0.00 | 0.00; 0.00 | 0.00; 0.00 | 0.00; 0.00 |
| density now | 0.00 (0.00) | 0.04 (0.01) | 0.06 (0.03) | 0.06 (0.02) | 0.05 (0.03) |
| left | 0.01 (0.00) | 0.11 (0.02) | 0.11 (0.03) | 0.10 (0.03) | 0.11 (0.04) |
| Same draw and year: SD left, DBH cm; height m | 0.08; 0.07 | 0.48; 0.03 | 1.13; 0.35 | 1.28; 0.28 | 1.54; 0.11 |

**Arms N (4 plots) and BIRCH (5 plots).** Each cell: draw / germination year / density now / left. Start crowding and damage are 0.04 or less everywhere. SD over plots is 0.00-0.16, and up to 0.28 in N's height at 50.

| Row | 20 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| N: height SD, m | 0.61 (0.01) | 0.39 (0.01) | 0.41 (0.03) | 0.23 (0.08) | 0.14 (0.03) |
| N: height shares | 0.00 / 1.00 / 0.00 / 0.00 | 0.01 / 0.99 / 0.00 / 0.00 | 0.00 / 0.25 / 0.01 / 0.72 | 0.01 / 0.54 / 0.00 / 0.45 | 0.04 / 0.86 / 0.00 / 0.07 |
| N: DBH SD over mean | 0.149 (0.003) | 0.109 (0.002) | 0.102 (0.008) | 0.099 (0.007) | 0.096 (0.008) |
| N: DBH shares | 0.05 / 0.85 / 0.02 / 0.06 | 0.15 / 0.57 / 0.07 / 0.20 | 0.37 / 0.27 / 0.11 / 0.23 | 0.42 / 0.21 / 0.12 / 0.24 | 0.41 / 0.18 / 0.16 / 0.24 |
| BIRCH: height SD, m | 1.23 (0.04) | 0.98 (0.05) | 1.09 (0.11) | 1.01 (0.23) | 0.94 (0.19) |
| BIRCH: height shares | 0.00 / 0.99 / 0.00 / 0.01 | 0.00 / 0.93 / 0.00 / 0.05 | 0.05 / 0.70 / 0.01 / 0.21 | 0.10 / 0.67 / 0.00 / 0.19 | 0.16 / 0.55 / 0.02 / 0.22 |
| BIRCH: DBH SD over mean | 0.183 (0.005) | 0.114 (0.006) | 0.111 (0.014) | 0.106 (0.021) | 0.103 (0.021) |
| BIRCH: DBH shares | 0.03 / 0.93 / 0.00 / 0.04 | 0.14 / 0.61 / 0.06 / 0.18 | 0.29 / 0.40 / 0.08 / 0.21 | 0.38 / 0.29 / 0.08 / 0.23 | 0.44 / 0.19 / 0.11 / 0.21 |

- **What each ingredient is worth, as spread.** At 45-60 the draw gives 0.12-0.13 of DBH spread while it also multiplies height (K), and 0.06-0.07 when it is in carbon only (N, BIRCH). Germination year gives 0.04-0.07 at 45-60. Density now gives 0.03 in every arm. What is left is 0.05 in every arm.
- **Two trees with the same draw and germination year** differ by 5-6 % of the mean diameter at 30-60 (SD 0.48-1.54 cm) and, on stems, not at all in height. The 0.35 m of height left at 45 is trees whose highest point stands above the stem top (T2, section 10); N's "left" at 45 and 50 is the same thing. What can make them differ: their place (light, so carbon, so rings), their own seed (their branching), damage, and which neighbours died. A tree's height step never reads any of these: light slowed 0.021 % of leader-years (T2).
- **Not a cause.** The basal area of larger neighbours within 5 m adds 0.01-0.06 for DBH in K, but it holds the tree's own rank. Counted from the sizes the draw and year alone predict, it adds nothing beyond density.
- **Carbon is already uneven; height doesn't answer.** In K the carbon a tree fixes has an SD over mean of 0.28-0.34 at 20-60, leaf area 0.21-0.28, crown width 0.04-0.08. Wood goes with carbon: stem volume spreads 0.27-0.31 at 30-60, and the two go together tree by tree (correlation of logs 0.95-0.97). For each metre a tree stands under the plot's tallest it fixes 2-7 % less carbon per m² of leaf and 12-43 % less in all, with the draw held.

**Rank, and who is left.** DBH order among the living; "taken out" removes the draw and germination year from both ages.

| Row | K | N | BIRCH |
|---|---|---|---|
| Rank at 20 against rank at 45; 50; 60, survivors | 0.74 (0.06); 0.72 (0.06); 0.68 (0.09) | 0.63 (0.11); 0.57 (0.15); 0.51 (0.19) | 0.72 (0.06); 0.69 (0.10); 0.65 (0.09) |
| The same, draw and year taken out | 0.03 (0.13); 0.00 (0.13); −0.05 (0.22) | 0.19 (0.13); 0.16 (0.11); 0.16 (0.23) | 0.35 (0.13); 0.35 (0.11); 0.24 (0.13) |
| Rank at 15 against rank at 45; 60 | 0.62 (0.07); 0.55 (0.10) | 0.51 (0.12); 0.40 (0.22) | 0.47 (0.09); 0.39 (0.04) |
| Alive at 45, % of each fifth at 20, smallest first | 2.7 / 6.2 / 8.3 / 10.8 / 17.5 | 6.0 / 11.2 / 14.5 / 13.3 / 18.7 | 0.8 / 6.2 / 11.5 / 17.5 / 23.9 |
| Alive at 50 | 2.0 / 4.6 / 6.3 / 8.1 / 14.7 | 3.8 / 9.3 / 12.3 / 11.7 / 15.4 | 0.3 / 3.9 / 9.6 / 13.5 / 20.4 |
| Alive at 60 (SD 0.0-3.6) | 1.3 / 2.8 / 4.2 / 5.6 / 11.6 | 3.1 / 7.3 / 8.9 / 8.4 / 12.3 | 0.0 / 2.1 / 7.4 / 10.3 / 16.6 |
| The 100 thickest a hectare at 45; 50; 60 that were in the top fifth at 20, % | 92 (7); 90 (11); 82 (16) | 68 (17); 62 (13); 58 (10) | 96 (5); 94 (9); 84 (5) |

**Who dies, and how fast.** Yearly death rate, %, by fifth of the DBH order at the start of the period, smallest first.

| Period | K | N | BIRCH |
|---|---|---|---|
| 20-25 | 15.7 / 12.8 / 11.0 / 10.0 / 8.5 | 16.8 / 13.0 / 10.6 / 10.2 / 7.8 | 25.8 / 12.7 / 12.6 / 9.6 / 6.7 |
| 30-35 | 14.3 / 10.5 / 8.5 / 7.6 / 6.9 | 7.9 / 9.3 / 7.1 / 6.1 / 5.1 | 13.4 / 7.3 / 5.7 / 6.8 / 5.9 |
| 40-45 | 10.0 / 5.9 / 4.9 / 4.9 / 2.7 | 7.6 / 3.9 / 3.9 / 5.8 / 2.6 | 8.4 / 4.7 / 2.8 / 2.9 / 3.2 |
| 45-50 | 7.3 / 6.0 / 4.6 / 3.7 / 2.4 | 4.6 / 4.1 / 3.4 / 3.7 / 3.7 | 8.4 / 3.2 / 3.4 / 4.9 / 2.9 |
| 50-60 (SD over plots 0.4-5.5) | 6.7 / 4.1 / 3.4 / 2.4 / 1.5 | 3.5 / 3.3 / 2.0 / 2.4 / 2.6 | 6.0 / 3.2 / 2.1 / 1.7 / 1.6 |

- **By cause (K):** the crowding rule takes 93 % of deaths in years 21-45 and 79 % in 46-60 (wind 11 %). **The tree that dies (K, 7,668 deaths in years 24-30, read on the yearly lists):** its diameter is 0.96 of the plot mean, and its growth in the year before was 0.94 of the mean. 12 % were under 0.8 of the mean diameter, 48 % at 0.8-1.0, 40 % at or over it. Only 3 % had grown less than half the mean.
- **After it falls behind (K, years 23-30):** a tree that grew less than half the plot mean the year before dies at 28 % a year (SD 8-12), so half are gone in 2.1 years; one that grew 1.0-1.5 of the mean dies at 9.8 % (0.7). Under BIRCH the slowest class dies at 36-43 % a year. Only 1.5 % of tree-years are in the slow class at all.
- **How regular the stand is:** Clark and Evans' index is 1.47 (0.01) for the places a plot begins with, 1.28 at 20 and 1.12-1.15 at 30, 45, 50 and 60 (1 is random; under 1 is clumped). Counts of trees on 10 m² cells at 11 have an SD over mean of 0.17, against 0.27 for trees placed at random.

## 2. Against the published tree-level models for birch (a seen comparison, not a target)

Hynynen, Ojansuu, Hökkä, Siipilehto, Salminen & Haapala 2002, Metla Research Papers 835, read today on the page scans of the copy in `birch-data/hynynen_2002/` (CONFIRMED). Silver and downy birch pooled.

| Model | As printed | Units and data |
|---|---|---|
| Basal-area growth, Model 31, Table 23, p. 39 | ln(i_ba5) = −3.98207 + 0.76027 ln SI + 14.97845/Hdom − 32.15540/Hdom² + 1.314906 ln(d+1) − 0.00053 d² + 0.37444 ln cr − 0.96221 RDFL − 0.59253 ln(RDF+1) + 1.16996 TS/1000 + 0.36701 PLANT + 0.19411 THIN − 0.16571 SPbb (downy birch) | i_ba5 cm² in 5 years; d cm; Hdom m, the mean height of trees thicker than Dg; cr crown ratio; TS degree days over 5 °C. 3,757 observations; plot SD 0.338, tree SD 0.505 (log). Data: d 1.0-41.4 cm, Hdom 2.6-31.2 m, age 12-193, RDF 0.03-1.57, SI 6.6-27.0, TS 659-1,350 (Table 5, p. 18) |
| Density, Eqs. 20-23, pp. 30-31; Eq. 3 | ga = e^−14.1979 × d_s^2.2178 ha a tree, d_s = 2 + 1.25 d; RDF = sum of ga a hectare; RDFL = the same over trees larger than this one | the silver birch line's values |
| Survival, Eq. 47, Table 32, pp. 50-51 | p5 = 1 / (1 + exp(3.014 + 0.1015 d_s − 9.313 RDFL + 0.4073 d_s RDFL)) | chance of dying of competition in 5 years. 7,427 birches, 476 dead (6.4 %); five experiments with untreated controls, planted and self-sown, fertile mineral soil; plots aged 17-50, dominant height 12.3-22.4 m, 370-3,051 stems/ha (p. 24) |
| Crown ratio, Eq. 65, Table 38, pp. 59-60 | cr = 1 − exp(−2.02622 × ln(Hdom)^−0.62383 × d^0.54674 × ln(h)^−1.67423 × exp(−0.32816 RDF)), self-sown | 5,235 observations, RMSE 0.100 |
| Self-thinning line, Eq. 50, Table 34, p. 53; Eqs. 52, 61, pp. 55-58 | ln N = 14.1979 − 2.2178 ln D_gs, D_gs = 2 + 1.25 Dg; its tangent under 12 cm. Stems over the line are taken evenly from every tree | 10 unthinned stands, 17 plots; Dg 7.4-25.5 cm (as read on 2026-11-11) |

Assumed: SI 23 (the model's), TS 1,300 (my guess for 60° N; 100 degree days move the level by 12 %), self-sown, no thinning, silver birch; crown ratio from the list's crown base; RDF and RDFL over the whole 1,000 m² plot; log growth turned back with no correction (a mean would be about 1.2 times higher); the report's later calibration (chapter 5) not applied. So levels are SUSPECTED; the pattern across sizes doesn't depend on SI or TS. The table is the control K: trees at 0.6 / 0.8 / 1.0 / 1.2 of the plot's mean diameter (classes ±0.1; growth of survivors).

| Row | 20-25 | 30-35 | 40-45 | 45-50 | 50-60, per 5 years |
|---|---|---|---|---|---|
| Stems in the class, % | 3.0 / 24.2 / 45.6 / 24.2 | 1.0 / 21.0 / 55.9 / 21.2 | 1.1 / 23.9 / 50.9 / 21.8 | 1.2 / 23.2 / 52.1 / 21.2 | 2.0 / 22.9 / 51.2 / 21.5 |
| Diameter growth, model, cm in 5 years (SD 0.07-0.35) | 1.62 / 1.81 / 1.95 / 2.07 | 1.80 / 2.40 / 3.04 / 3.82 | 1.29 / 2.00 / 2.57 / 3.17 | 1.11 / 1.84 / 2.40 / 2.96 | 0.99 / 1.63 / 2.20 / 2.67 |
| The same trees, published | 1.43 / 1.56 / 1.85 / 2.26 | 0.92 / 1.02 / 1.30 / 1.71 | 0.71 / 0.78 / 1.00 / 1.34 | 0.63 / 0.69 / 0.90 / 1.20 | 0.57 / 0.63 / 0.81 / 1.07 |
| Growth as a power of relative diameter: model; published | 0.42 (0.10); 0.98 (0.03) | 1.45 (0.10); 1.53 (0.07) | 1.38 (0.11); 1.53 (0.11) | 1.42 (0.13); 1.50 (0.19) | 1.46 (0.18); 1.45 (0.17) |
| Deaths, model, % a year | 22 / 14.1 / 11.4 / 8.8 | 61 / 13.5 / 8.8 / 6.6 | 58 / 9.2 / 4.9 / 3.3 | 34 / 7.3 / 4.5 / 2.9 | 53 / 6.0 / 3.2 / 1.3 |
| Deaths, published, a tree at exactly that size | 15.5 / 10.5 / 3.3 / 0.7 | 9.3 / 4.3 / 0.9 / 0.2 | 3.1 / 0.65 / 0.13 / 0.06 | 1.6 / 0.22 / 0.05 / 0.03 | 0.74 / 0.08 / 0.02 / 0.02 |
| All trees: model; published | 11.5 (0.5); 4.3 (0.1) | 9.3 (0.6); 1.4 (0.2) | 5.5 (0.8); 0.24 (0.06) | 4.6 (1.0); 0.09 (0.03) | 3.4 (0.6); 0.04 (0.01) |

- The 0.6 class holds 20-51 trees in all 20 plots from 30 on, so its model death rates are rough (SD over plots 43-49). The stand at 20-25 (9,324 stems/ha) is denser than the survival model's data.
- **With the draw off height the model's growth is half as steep as the published.** The power is 0.78 / 0.85 / 0.97 / 1.01 in N at 30-35 / 40-45 / 45-50 / 50-60, where the published model gives 1.71 / 1.94 / 2.09 / 2.07 on the same trees. Under BIRCH it is 1.56 / 1.88 / 1.99 / 1.92 against 1.86 / 1.94 / 2.16 / 2.22. In K the draw supplies the steepness.
- **Crown ratio** by class is near the published at 45-50 (0.44 / 0.47 / 0.50 / 0.54 against 0.41 / 0.45 / 0.48 / 0.50). The stand's mean is 0.87 at 20 and 0.60 at 30 against 0.46, then 0.50 / 0.47 / 0.42 at 45 / 50 / 60 against 0.48 / 0.48 / 0.49.

**Stems against the line** (mine; T2's twice-checked 0.65 / 0.83 / 0.86 / 0.95 differ by 0.01 because I weight the stump diameter by basal area).

| Row | 20 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| K: stems/ha; the line's; share | 9,324; 10,853; 0.86 (0.03) | 2,640; 4,115; 0.64 (0.02) | 846; 1,032; 0.82 (0.03) | 667; 781; 0.85 (0.03) | 474; 503; 0.94 (0.05) |
| N; BIRCH: share | 0.65 (0.01); 0.69 (0.01) | 0.68 (0.03); 0.69 (0.01) | 0.80 (0.02); 0.85 (0.02) | 0.82 (0.04); 0.84 (0.02) | 0.88 (0.02); 0.92 (0.03) |

**A desk projection (arithmetic with the printed rules in 5-year steps; not a run of the model; SUSPECTED as a forecast).** Growth by Model 31, crown ratio by Eq. 65, height by Eq. 33 on the model's curve, deaths by Eq. 47, then the line. "Evenly" is the report's own Eq. 61; "by odds" raises every tree's own odds by one factor until the line is met (my variant). Twenty stands each.

| Start at 30 | Deaths over the line | DBH SD over mean, 30 / 45 / 50 / 60 | Height SD, m | Stems/ha | Basal area, m²/ha |
|---|---|---|---|---|---|
| K's own stands | evenly | 0.128 / 0.139 / 0.142 / 0.150 (SD 0.003-0.008) | 0.85 / 1.26 / 1.35 / 1.53 | 2,640 / 2,159 / 1,951 / 1,552 | 18.9 / 28.4 / 29.3 / 29.1 |
| K's own stands | by odds | 0.128 / 0.139 / 0.138 / 0.135 | 0.85 / 1.26 / 1.30 / 1.31 | 2,640 / 2,159 / 1,925 / 1,476 | 18.9 / 28.4 / 29.4 / 29.4 |
| K's, with a lasting tree effect on growth, SD 0.25 (log) | evenly; by odds | 0.128 / 0.154 / 0.165 / 0.186; … / 0.153 / 0.155 / 0.164 | … / 1.26 / 1.36 / 1.54; … / 1.26 / 1.26 / 1.25 | … / 2,133 / 1,841 / 1,404 | … / 28.8 / 28.7 / 28.0 |
| As uneven as a measured stand (2,800/ha, 10.2 cm, SD over mean 0.36; heights my guess) | evenly | 0.360 / 0.243 / 0.235 / 0.227 | 2.65 / 2.47 / 2.54 / 2.74 | 2,800 / 1,498 / 1,337 / 1,103 | 25.8 / 26.3 / 26.5 / 26.6 |
| The same | by odds | 0.360 / 0.210 / 0.197 / 0.182 | 2.65 / 2.00 / 1.97 / 1.94 | 2,800 / 1,400 / 1,227 / 981 | 25.8 / 27.3 / 27.6 / 27.9 |

**Where the model's forest is too equal.**

| Where | Verdict |
|---|---|
| How they start | **Yes, and it matters most.** The start is more regular than random, and by 20 the spread it had is gone (section 3). A tree that came up three years late has 0.15 of a first-year tree's diameter at 11, 0.49 at 15, 0.67 at 20, 0.79 at 30, 0.88 at 45 and 0.92 at 60: it catches up, because every tree gets the curve's step at its own age |
| Growth by size | **Hidden by the draw.** With the draw on height the model is as steep as the published model. Without it, it is half as steep. Local crowding moves diameter by 0.03 |
| Who dies | **Yes.** A mild lean towards small trees on top of a lottery; mean and large trees die about 50 to 150 times as often as the published model says for trees of their size at 45-60, and a slow tree is removed at once |
| How many stand | **Partly.** 0.64 of the line at 30, 0.82-0.94 at 45-60. Three measured unthinned stands sit at 0.96-1.03 (`reports/sources_opened_2026-11-11.md`) |

**Found, and not designed here: the forest turns over fast.** Survivors' diameters grow 2.3-2.7 times what Model 31 gives for the same trees at 30-60 (SUSPECTED as to level). Stem wood grows 12.8 / 15.6 / 13.4 / 12.4 / 11.2 m³/ha a year at 20-30 / 30-40 / 40-45 / 45-50 / 50-60 (SD 0.2-0.3), and 8.2 / 9.6 / 8.2 / 8.1 / 6.4 of it dies, because the trees that die are mean-sized. By 60 the forest has made 585 (7) m³/ha of stem wood without bark and holds 246 (13). Fries's table for thinned stands at h50 22 gives 257 m³/ha under bark by 60 (as read on 2026-11-11; I did not re-read it). Stands and site differ, so this is SUSPECTED, but any rule that stops large trees dying will stop hiding it.

## 3. Where real spread comes from, at the source

**Measured stands.** SD over mean is my division of the printed SD by the printed mean.

| Stand (source, table) | Kind of stand | Age | Stems/ha | DBH SD over mean | Height |
|---|---|---|---|---|---|
| Tipecek, Czech Republic (Martiník et al. 2018, Table 1) | sown after windthrow; untreated; pure (others under 5 %, left out); all live trees over 1.3 m on ten 10 m² plots | 4; 5 | 42,890; 43,670 | 0.79; 0.68 | upper height 4 m |
| Breziny (same) | self-sown after windthrow; untreated | 8; 9 | 18,720 | 0.62; 0.63 | 7 m |
| Dubska (same) | self-sown after felling; untreated; ten 25 m² plots | 17; 18 | 4,720 | 0.46; 0.47 | 15 m |
| Skrchov (same) | self-sown after felling; untreated | 22; 23 | 2,800 | 0.36; 0.36 | 17 m |
| Lehrer Wald, Germany (Hagemeier & Leuschner 2019, Table 3): the target | origin and management not stated; 85 % birch, alder admixed | 45 | 880 | 0.32 | 20 ± 3 m |
| Lappwald (same): the target | not stated; 98 % birch | 67 | 420 | 0.12 | 25 ± 3 m |
| Central Latvia (Zeltiņš et al. 2018, Table 1) | planted grafted clones, 400/ha, former farmland | 40 | 400 | 0.20 (27.7 cm, SD 5.6) | 26.2 m, SD 2.2 |
| Three Latvian progeny trials (Gailis et al. 2020, Tables 2, 3) | planted at 2 × 2 and 2 × 2.5 m | 14 | about 2,000-2,500 | 0.14-0.28 (SUSPECTED: additive spread over the root of heritability) | 0.07-0.13 of the mean at 14 |
| Two sites, Sweden (Dahlgren Lidman et al. 2021, Table 5) | self-sown, unthinned control, birch over spruce | 42 | about 4,430 birch | the 300 thickest a hectare are 17.4 cm, the quadratic mean 9.5: 1.83 times | – |
| The model, K | self-sown, 16,000/ha at the start | 11; 15; 20; 23; 30; 45; 50; 60 | 13,752; 13,220; 9,324; 6,474; 2,640; 846; 667; 474 | 0.53; 0.25; 0.16; 0.14; 0.13; 0.14; 0.15; 0.15 | SD 0.66; 0.73; 0.78; 0.80; 0.85; 1.04; 1.06; 1.09 m |

- **Like for like:** Skrchov and the model at 30 have the same stems and mean diameter (2,800/ha at 10.2 cm; 2,640/ha at 9.5 cm). The spread is 0.36 against 0.13. The model's thickest 6.8 % of stems at 42 are 1.27 (0.04) times its quadratic mean, against 1.83 in the Swedish stand. Its Gini of basal area is 0.16 at 45-60; Bourdier et al. 2016 cite 0.2-0.7 as usual for stands over 0.25 ha, a loose yardstick.
- **Martiník's table checks itself:** stems, mean and SD give the printed basal area in all eight rows (25.8 against 25.77; 22.0 against 22.02).
- **Spread falls with age in self-thinning stands.** 0.79 to 0.36 from 4 to 23 years above. Metsaranta & Lieffers 2008 (four fire-origin jack pine stands, 69-84 years at breast height, 1,267-2,089 living stems/ha, rebuilt from tree rings) found the inequality of stem volume generally falling from 1950 to 2004, and more unequal growth in poor years.
- **How clumped the start is.** Martiník's ten plots range from 2,000 to 95,000 stems/ha at 4 and from 6,400 to 48,000 at 8. That is an SD over mean of about 0.7 between 10 m² plots, where random placing gives 0.15-0.23 (SUSPECTED: from the printed lowest and highest). By 17 it is 0.25 (random 0.29) and by 22, 0.19 (random 0.38). Dahlgren Lidman et al. (New Forests 55:157, Table 2; six clear-fellings, Sweden) counted 0-19 birch seedlings per m² by seedbed and moisture: 0-0.2 on untouched ground on dry and mesic sites, 1.3-17.6 on bared mineral soil on mesic sites.
- **How many years it takes.** In that table plots scarified one, two and three years before hold 1.7 / 10.2 / 9.2 and 1.3 / 11.6 / 17.6 seedlings per m² (mesic, mineral soil): few are there after one year, and most have come by the second or third (SUSPECTED: one count year, different plots). The model's four years with weights 0.4 / 0.3 / 0.2 / 0.1 are a guess (`labels.yaml`: VERIFY).
- **How long suppressed birches live.** By Eq. 47 a birch of 10 cm with RDFL 0.8 dies at 3.1 % a year (half gone in 22 years); one of 5 cm at 22 % (3 years); one of 20 cm at under 0.1 %. Measured rates: 6.4 % of 7,427 birches in 5 years (Hynynen et al. 2002, p. 24); 9.67 % of 6,009 in 5 years on 348 Estonian plots, 16.67 % where birch is 81-100 % of the neighbours, with the odds falling with 5-year diameter growth and relative diameter (Maleki & Kiviste 2016, Tab. 1, 3); 610 stems/ha a year in the Swedish control from 30 to 42; 35 % and 26 % in two years in a self-sown stand going from 11,633 to under 3,000/ha between 8 and 17 (Aosaar et al. 2016, Table 3).
- **How much trees differ in vigour on one site.** Clones at 400/ha, 40 years: genotypic SD over mean 9.5 ± 1.5 % for DBH and 3.2 ± 0.5 % for height, heritability 0.21 and 0.14, so about four fifths of the tree-to-tree variance there is not genetic (Zeltiņš et al. 2018, Table 1). Progeny at 14 years: additive SD over mean 4.7-18.7 % for DBH, 5.5-8.5 % for height (Gailis et al. 2020, Table 3). The published growth model's own tree-to-tree residual within a plot is 0.505 in the log of 5-year basal-area growth. The model's draw is 0.06.
- **Size-asymmetric competition and growth dominance.** I opened no primary source on these (below). Second-hand, from the introductions of Metsaranta & Lieffers 2008 and Kolisnyk et al. 2025: larger trees take light first, so inequality rises before self-thinning and falls as it proceeds. The model's own numbers say the same loop is cut at height.

**Sources: what I took, and how each was opened.**

| Source | Taken | Opened |
|---|---|---|
| Hynynen et al. 2002, Metla Research Papers 835 | Table 23 p. 39; Eqs. 20-23 pp. 30-31; Eqs. 45-48 and Table 32 pp. 50-51; p. 24; Table 5 p. 18; Eq. 50, Table 34 p. 53; pp. 55-58; Eq. 65, Table 38 pp. 59-60; symbols p. 9 | page scans of the copy downloaded 2026-11-11 from Luke's repository |
| Martiník et al. 2018, Silva Fennica 52(5) 9985 | Table 1; sections 2.1, 2.2; "no silvicultural treatments" (Discussion) | publisher's page, fetch tool, read twice. Opened before for stocking only |
| Hagemeier & Leuschner 2019, Forests 10(3):265 | Methods 2.1-2.3; Tables 2, 3 with footnote | publisher's page in Chrome (the fetch tool got HTTP 403) |
| Zeltiņš et al. 2018, Forests 9(2):52 | Table 1 | publisher's page in Chrome |
| Gailis et al. 2020, Silva Fennica 54(2) 10220 | Tables 1-3. The page's text and Table 3 disagree on some values; I used the table | publisher's page, fetch tool |
| Dahlgren Lidman et al. 2021, Silva Fennica 55(4) 10485 | Tables 4, 5; mortality sentence | publisher's page, fetch tool |
| Dahlgren Lidman et al., New Forests 55:157 (doi 10.1007/s11056-023-09971-z) | Table 2; Results | publisher's page in Chrome, open access |
| Maleki & Kiviste 2016, iForest 9:643 | Tab. 1, Tab. 3, Results | publisher's page, fetch tool (first 100,000 characters) |
| Metsaranta & Lieffers 2008, Annals of Botany 101:561 | Table 1, Figs. 2-3, text. Jack pine, not birch | PubMed Central, PMC2710195 |
| Bourdier et al. 2016, PLoS ONE 11(3): e0151852 | the usual range of the Gini of basal area. No birch among the species its text names | publisher's page, fetch tool |
| Kolisnyk et al. 2025, Dendrobiology 94:150 | definitions only. Managed silver fir: not comparable | publisher's PDF. The fetch tool kept a copy in its own results folder outside the repository; I read three pages as text and moved nothing |
| Aosaar et al. 2016, Silva Fennica 50(4) 1628 | Results 3.1, Table 3 | text of the copy saved 2026-11-08 |

Not opened: Maleki, Kiviste & Korjus 2015, Forest Systems 24(2) e023 (the fetch tool failed on the site's certificate; not tried in Chrome); Niemistö 1995 (paywall on 2026-11-09, not retried); Weiner 1990, Schwinning & Weiner 1998, Binkley 2004, Pretzsch & Biber 2010 and Forrester 2019 (not tried: paywalls or the CAPTCHA site, so their claims are second-hand here); Hynynen et al. 2010 and Oikarinen 1983 (not tried); Fries 1964 (not re-read).

## 4. The design

Real stands are uneven because they start uneven, small trees fall behind and don't catch up, and they then take years to die while large trees hardly die at all. The model has the first for a few years and none of the rest.

| Part | Mechanism | Formula | Values, and where from | Switch (off by default) | Replaces |
|---|---|---|---|---|---|
| **S. A patchy start** | Seedlings come up where the seedbed lets them, many-fold denser in one place than another a few metres off | Places drawn with density λ(x) = λ0 × exp(σ Z(x) − σ²/2), Z a smooth random field of SD 1 with correlation length ℓ (m); no minimum distance | σ 0.62: TUNED against an SD over mean of about 0.7 for counts on 10 m² at 4-9 years (Martiník 2018, Table 1; my arithmetic). ℓ 3 m: an estimate, no patch size is printed in a source I opened. 16,000/ha stays (TUNED, as today). Arrival years unchanged | `plot.natural_start.pattern: patchy` | the minimum-distance rule in `Plot._natural_start` |
| **H. Height by standing** | A tree thinner than the dominants gains less height, the more so the more of the stand is larger than it, so it can't catch up | step = dominants' step × (d / Ddom)^(1.54405 × RDFL) | sourced: Hynynen et al. 2002 Eq. 33, Table 24 p. 41, self-sown birch | `plot.height_status`, rule `birch_2002`: built and merged (DECISIONS 114) | the draw on a plot tree's height step |
| **M. Death by standing, over years** | Small trees under larger ones die at a chance that builds over years; large trees almost never. The line caps how many stand | yearly hazard h = −ln(1 − p5) / 5, p5 by Eq. 47 with d_s and RDFL as in section 2. Then, if stems exceed N_max = exp(14.1979 − 2.2178 ln(2 + 1.25 Dg)), every h is multiplied by one factor until they don't | sourced: Eq. 47 and Table 32; Eq. 50 and Table 34; Eqs. 3, 21-23, 52. DERIVED: the yearly hazard from the 5-year chance. Mine, not the report's: raising the odds where the report takes the excess evenly (a setting, `over_line: by_odds` or `evenly`). Outside the data before 17 years and over 3,051 stems/ha: labelled extrapolated | `mortality.rule: birch_2002` | the crowding, suppressed and background hazards of `treegen/thinning.py`. Old age, snow and wind stay |
| **V. Vigour of a measured size** | Trees differ in what they make of the same light | the draw's SD in ln(carbon gain), as today | 0.09: DERIVED from the genotypic 9.5 ± 1.5 % of DBH (Zeltiņš 2018, Table 1; clones, 40 years, 400/ha) over the model's own DBH spread per unit of carbon draw (0.061-0.068 for 0.06 in N and BIRCH) | a value, `plot.vigour_sd`; no code | 0.06 (VERIFY) |

- **Why these four and not the others.** The pine rule lets thin trees catch up and is stopped. A new carbon-sharing rule has nothing to act on: the pool covers the leader, the limbs and the sapwood in 99.85 % of tree-years (T2), and wood already goes with carbon. A leader-light rule has nothing to act on while trees are within a metre of each other in height. A lasting place effect (soil) would be a second draw; its measured size exists (about 0.18 of DBH in the clonal stand), and I leave it to the owner.
- **H was tested alone and stopped** (`reports/design/2026-11-12_e_screens.md`): its late trees fell 2-5 m behind and were then removed by today's death rule (25.8 % a year for the smallest fifth at 20-25). H and M come from one report and one data set, and are meant to act together.
- **Tuned values that would go with M on:** `mortality.rate_at_max`, `shape`, `rate_cap`, `sdi_max`, `neighbourhood_sigma_m`, the four `mortality.vigour` values and `relative_size_from` (ten TUNED values), with the digitised size weights and the background rate. In their place: eight printed coefficients.
- **What that puts at risk.** Stems: the forest would sit on the published line, about 1,000-1,800 at 45 where the tuned row has 880 (one stand). Basal area: a stand on the line carries 29.0 m²/ha at an SD over mean of 0.15, 26.3 at 0.25 and 23.9 at 0.32 (my arithmetic), so an even forest would pass the 28.5 guard. Leaf area index at 60 has 0.21 of room under 4.5, and at 50 none. The crowding rule would no longer tell a gap from a thicket, since Eq. 47 reads the whole plot. Top height, as approved, moves with the shape of the stand (E: +0.3-0.9 m).

## 5. Expectation, written before anything is run (SUSPECTED throughout)

Each cell: 30 / 45 / 50 / 60. Today's row is K on 20 seeds (leaf area index and light at 45 on seeds 1-5). H alone is what E measured on 5 seeds (its stem tops at 45-60 are E's own rebuild, SUSPECTED). The rest are forecasts.

| Arm | Height SD on stem tops, m | on reported height | DBH SD over mean | Stems/ha (share of the line) | Basal area | Leaf area index | Light, % |
|---|---|---|---|---|---|---|---|
| Today | 0.85 / 0.97 / 1.04 / 1.09 | 0.85 / 1.04 / 1.06 / 1.09 | 0.13 / 0.14 / 0.15 / 0.15 | 2,640 / 846 / 667 / 474 (0.65 / 0.83 / 0.86 / 0.95) | 18.9 / 24.0 / 24.7 / 26.8 | 5.44 / 4.79 / 4.51 / 4.29 | 16.0 / 17.5 / 18.2 / 19.5 |
| H alone (measured) | 0.98 / 1.04 / 0.98 / 0.94 | 0.98 / 1.09 / 1.01 / 0.94 | 0.11 / 0.11 / 0.11 / 0.10 | 1,682 / 702 / 560 / 426 (0.70 / 0.85 / 0.85 / 0.92) | 20.8 / 25.2 / 24.9 / 26.7 | 5.15 / 4.69 / 4.34 / 4.09 | 17.1 / 17.1 / 19.9 / 20.3 |
| M alone | 0.8-0.9 / 0.8-1.0 / 0.8-1.0 / 0.8-1.1 | the same, +0.05-0.10 at 45 | 0.11-0.14 at every age | 4,000-5,500 / 1,000-1,800 / 800-1,400 / 500-950 (0.9-1.0, then 1.0) | 24-28 / 28-30 / 28-30 / 28-30 | +0.0 to +0.3 | −0.5 to −2 points |
| H + M | 1.6-2.3 / 1.2-1.7 / 1.1-1.6 / 1.0-1.4 | +0.05-0.10 at 45 | 0.18-0.25 / 0.14-0.18 / 0.13-0.17 / 0.12-0.16 | as M alone | 23-27 / 27-29 / 27-29 / 27-29 | +0.0 to +0.3 | −0.5 to −2 |
| H + M + S | 1.8-2.6 / 1.4-2.0 / 1.3-1.9 / 1.1-1.6 | +0.05-0.10 at 45 | 0.20-0.28 / 0.16-0.22 / 0.15-0.20 / 0.13-0.18 | 3,500-5,000 at 30, then as M | 22-26 / 26-29 / 26-29 / 26-29 | −0.2 to +0.2 | −1 to +1 |

- **M alone.** Under the line Eq. 47 takes 4.3 % a year at 20-25 and 1.4 % at 30-35 from a stand as even as K, against today's 11.5 % and 9.3 %. Stems rise to the line by about 30 and stay on it. The small go first and the draw's leaders stay, so spread holds or falls a little: selection from below narrows an even stand (BIRCH: 0.10-0.11).
- **H + M.** Late trees fall behind as under BIRCH, but the 0.6 class dies at 6-16 % a year at 20-35 by Eq. 47, not at 22-61 %, so more of it is still standing at 20-30. The gain is largest there. By 45-60 the fast-growing stand presses on the line and the smallest are taken, as the desk projection by odds shows (0.21 / 0.20 / 0.18 from a start of 0.36).
- **S** adds trees that are small because their patch was dense. Today density moves diameter by 0.03; a start several times more uneven should double that, and H then turns thin into short.
- **V** adds 0.09 in place of 0.06-0.07 in carbon only: about 0.01 on the row above, with all four on.
- **Top height** is expected not to fall: in every arm of E the thickest trees stood on the curve or above it. **What I do not expect:** 0.32 and 3 m at 45. The sharper test is the young measured stands: 0.46 at 17-18 and 0.36 at 22-23, where I expect 0.25-0.33 with all four.

**Falsifying tests inside one run of H + M (and S).** If the mechanism is right, all of these hold; any one failing says the spread, if it came, came from something else.

| Test | Must be true | Today |
|---|---|---|
| Lingering | Of trees that grew under half the plot mean, at least half are alive 4 years later at 20-35 | half are gone in 2.1 years |
| Large trees are safe | The thickest fifth dies at under 1 % a year at 30-60, storms apart | 6.9 / 2.4 / 1.5 % a year at 30-35 / 45-50 / 50-60 |
| No catching up | The year-2 and year-3 trees' mean diameter over the first-year trees' does not rise from 15 to 30 | 0.49 to 0.79 for year 3 |
| Standing carries, not the draw | Rank at 20 against rank at 45, 50 and 60 with the draw and year taken out is over 0.3 | 0.03 / 0.00 / −0.05 |
| Spread falls with age | DBH spread at 20 is over that at 30, and 30 over 45, 50 and 60 | 0.16 / 0.13 / 0.14 / 0.15 / 0.15: it rises after 30 |
| On the line | 0.9-1.1 of the line's stems from 25 to 60 | 0.64 at 30; 0.82 / 0.85 / 0.94 at 45 / 50 / 60 |
| With S: spread goes with crowding | Density now explains at least 0.15 of DBH at 30, 45 and 50; counts on 10 m² start at an SD over mean near 0.7 and fall under the random value by 23 | 0.04 / 0.06 / 0.06; 0.17 at 11 |

## 6. The targets themselves (CONFIRMED at the publisher's page today; no target changed)

| Question | What the paper says |
|---|---|
| Self-sown or planted; thinned or not | Not stated. "Mature stands" in two forests of Helmstedt county, Lower Saxony, with a closed canopy (over 0.9) |
| Where in the stand | Two circular plots of 1,000 m² a stand, put in sections with high canopy closure; gaps over about 25 m² were avoided. That picks the fullest parts |
| Pure or mixed | Site 1 (45 years): 85 % of stems birch, with black alder. Site 2 (67 years): 98 %, with Scots pine. Whether the mean and ± include the other species is not stated |
| How stems were counted | DBH of all trees in the plots, no lower limit stated; about 176 and 84 trees. Height measured on 32-46 trees a plot, the rest from a curve, so the height ± is partly a curve's |
| What ± is | Not said for the table. For figures the paper gives means and SD |
| Do the figures square | No (Q32). Site 1's stems, mean and SD give 27.4 m²/ha against the printed 25.2; the printed figure fits a mean of 18.5 cm with an SD of 4.7 (0.25). Site 2's give 20.9 against 28.5, which would need an SD of 15 cm |

- **0.32 at 45** is plausible for an unthinned stand. It rests on one stand of unknown history with 15 % alder, and it reads 0.25-0.32 once rounding is allowed for. **Height SD 3 m** comes from the same two stands.
- **0.12 at 67** does not describe a stand like the model's (SUSPECTED): 420 stems/ha at 0.68 of the line with so narrow a spread looks like a stand thinned from below, and its basal area doesn't fit. The model already reads above it.

Candidates for the owner, none entered: Martiník's four stands (spread at 4-23 years; how patchy the start is; like the model's in being self-sown, untreated and pure, but one stand per age, Czech sites, and taller for their age than the model); Zeltiņš's planted stand at 40 (a floor: what trees differ by with no self-thinning); Dahlgren Lidman's 1.83 at 42; Maleki & Kiviste's and Hynynen's 5-year death rates.

## 7. The smallest version worth building first, and the owner's questions

**Build M, and run it with H.** One function beside today's in `treegen/thinning.py`, one call in `Plot._self_thin`, about six setting names, off by default, with hand-worked trees for Eq. 47 as step E had for Eq. 33. Then two arms on the control's seeds 1-5: H + M, and M alone. K and BIRCH exist. Read first: the lingering, safe-large-tree and no-catching-up tests, then spread at 20, 23, 30, 45, 50 and 60. S is the second build; V needs no code. Recording each tree's stem top in the tree lists (T2's proposal; it changes no growth) is needed to read height spread on stems.

Questions only the owner can answer:

1. **Which row decides.** H + M is expected to hold diameter spread about level at 45 and 50, and lift it at 20-30. The plan's do-no-harm rows at 45 and 50 protect spread the draw makes (E's question 4). May the young measured stands (0.46 at 17-18, 0.36 at 22-23) be the rows that must improve, with 45, 50 and 60 kept as do-no-harm?
2. **Stems.** M puts the forest on the published line: 1,000-1,800 stems at 45 where the tuned row has 880, and a basal area near 29 if the forest stays even (guard 28.5). Three measured unthinned stands sit on the line; the 880 is one stand of unknown history. Which holds?
3. **Outside the data.** Eq. 47 was fitted on stands of 17-50 years with up to 3,051 stems/ha. May it run from year 12, labelled extrapolated, or should today's rule hold until top height 12.3 m?
4. **Who the line takes.** The report takes the excess evenly; I propose raising each tree's own odds, which is mine. Agree, or run both?
5. **New measured stands.** May Martiník's four stands be entered as guide rows, and Zeltiņš's planted stand held back for a release test? Should Hagemeier's 67-year spread be marked doubtful?
6. **The turnover.** The forest makes 585 m³/ha of stem wood by 60 and loses 339 of it. Do you want that checked against a yield table at the model's site index before M is judged?
7. **A lasting place effect.** A second draw, standing for soil, of measured size. I recommend not now. Agree?
8. **Arrival years.** The one table I opened suggests few seedlings come in the first year and most by the second or third. Leave the four years as they are for now?

## Limits, and how I checked

- Shares of variance are least-squares fits per plot; at 60 a plot has 47 (3) trees. Density now is partly a result, not only a cause. The 0.6 class is a few dozen trees. N has 4 plots and BIRCH 5.
- The published models were applied outside their calibration, with assumed site index and temperature sum; the projection has no crowns, light or carbon, and the uneven start's heights are my guess.
- Every source figure was read once by me, Martiník's table twice. Six sources came through a fetch tool that summarises pages; Martiník's numbers check against the printed basal areas, the others were not cross-checked. Not done: any run; this budget for arms A, A-early and D-BIRCH; stem tops (not in the lists); a primary source on size-asymmetric competition.
- Checks: my K rows equal T2's twice-checked figures (height SD, DBH spread, stems, the share explained by draw and year within 0.01, the line's share within 0.01). The published coefficients were read on the page scans; the text layer is poor and was used only to find pages.
