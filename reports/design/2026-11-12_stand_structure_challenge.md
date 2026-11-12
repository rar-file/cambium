# Stand structure: the challenge

2026-11-12. Model: Opus 5.5 (ID `claude-opus-5-5`). A challenge to `reports/design/2026-11-12_stand_structure.md` (called "the design"). Read only: no model run, no test, no server job, no model code. This is the only file I wrote in the repository. On the PC I read the fetched tree lists in `out/bench/ensemble/` (K: `node_t2_k`, 20 plots; N: `node_t2_n`, 4; BIRCH: `node_e_s5_birch_6c0ebb6`, 5) and did arithmetic with new scripts of my own in the session's scratch folder, outside the repository. CONFIRMED = I computed it from those files, or read it myself at the source named. SUSPECTED = inferred. Cells are means over plots, SD over plots in brackets.

## Verdict in six lines

1. **The variance budget holds.** I rebuilt it with my own code: every share the design prints for K, N and BIRCH comes back within 0.01-0.02. The order of terms moves no share by more than 0.04.
2. **Hynynen et al. 2002 is quoted correctly**, with two things missing. The survival data come mostly from thinned plots. And Eq. 47 flips for trees thicker than 16.7 cm: past that size, more larger neighbours make death *less* likely. 78 % of K's trees are past it at 45 and 93 % at 60.
3. **The biggest gap: once the stand reaches the line, the line decides who dies, not Eq. 47.** With the model's own diameter growth, a stand on the line must lose 10.4 / 4.9 / 3.8 % of its stems a year at 30-35 / 45-50 / 50-60. Eq. 47 alone takes 0.04-4 %. So from about 25 years on, "death by standing" is the design's own sharing rule ("by odds"), which no source gives. The report's own rule ("evenly") is a lottery again.
4. **Tests 1 and 2 cannot both pass on the line**, whatever the mechanism. By odds, the thickest fifth dies at 1.6 / 2.4 / 3.1 % a year and the smallest at 31 % (30-35). Evenly, the thickest dies at 7.0 / 4.8 / 3.8 %. Neither threshold has a measured source.
5. **One target reading is one-sided.** Hagemeier's Table 3 prints whole numbers (19 ± 6; 25 ± 3), so 0.32 reads 0.28-0.35. Stems, mean and basal area fail to square in most rows of that table, other species included, so the basal area cannot be used to shrink the SD to 0.25.
6. **Verdict: pass.** Build M with H as the smallest version, but run both ways of sharing deaths over the line, restate tests 1-3, and put four questions to the owner first.

## 1. The variance budget, recomputed (CONFIRMED)

My own scripts: shares of variance among living trees per plot, adjusted R², in three ways. The design's order (draw, then germination year, then density now). The order swapped (year first). And Shapley shares (the mean over all six orders of draw, year and density). The draw is entered as ln(vigour) and its square; germination year as three dummies; density now as the count of living stems within 3, 5 and 8 m (the plot wraps at its edges), basal area within 5 m and nearest stem. I left out the crowding at the start and damage, which are 0.00-0.04 in the design.

| Row | 20 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| K: DBH SD over mean | 0.161 (0.005) | 0.129 (0.008) | 0.143 (0.013) | 0.148 (0.015) | 0.148 (0.016) |
| K: DBH draw / year / density / left, design's order | 0.40 / 0.58 / 0.00 / 0.01 | 0.55 / 0.29 / 0.04 / 0.12 | 0.71 / 0.11 / 0.06 / 0.11 | 0.75 / 0.08 / 0.06 / 0.10 | 0.78 / 0.06 / 0.05 / 0.11 |
| K: DBH draw / year, year first | 0.39 / 0.59 | 0.57 / 0.27 | 0.75 / 0.07 | 0.78 / 0.06 | 0.81 / 0.03 |
| K: DBH draw / year / density, Shapley | 0.40 / 0.59 / 0.00 | 0.56 / 0.28 / 0.04 | 0.72 / 0.09 / 0.08 | 0.76 / 0.07 / 0.07 | 0.77 / 0.04 / 0.08 |
| K: height SD, m | 0.78 (0.02) | 0.85 (0.05) | 1.04 (0.07) | 1.06 (0.09) | 1.09 (0.13) |
| K: height draw / year, design's order | 0.44 / 0.54 | 0.79 / 0.21 | 0.84 / 0.05 | 0.90 / 0.02 | 0.97 / 0.02 |
| N: DBH SD over mean; draw / year / density, Shapley | 0.149; 0.05 / 0.84 / 0.03 | 0.109; 0.16 / 0.55 / 0.08 | 0.102; 0.37 / 0.26 / 0.14 | 0.099; 0.44 / 0.19 / 0.12 | 0.096; 0.42 / 0.17 / 0.18 |
| BIRCH: DBH SD over mean; draw / year / density, Shapley | 0.183; 0.02 / 0.93 / 0.01 | 0.114; 0.14 / 0.61 / 0.07 | 0.111; 0.30 / 0.38 / 0.09 | 0.106; 0.39 / 0.28 / 0.08 | 0.103; 0.45 / 0.21 / 0.07 |
| Correlation of ln(draw) with germination year among the living, K | −0.01 | 0.03 | 0.05 | 0.04 | 0.06 |

- **Does the order matter?** Barely. Among survivors the draw and germination year are almost uncorrelated (r 0.01-0.08 in every arm), so no order moves a share by more than 0.04. Density now gains 0.01-0.03 under Shapley at 45-60, because it partly restates the draw's and year's sizes. That is the design's own caveat ("partly a result").
- **Does the draw also sit in germination or crowding?** No. Draws and years are independent when trees come up, and selection has hardly linked them by 60. That itself says deaths barely pick on the draw (section 3).
- **Survivors only?** That is the right population, because measured stands are survivors too. But it makes test 3 in the design unsafe (section 4).
- **Ranks.** I reproduced the rank at 20 against 45 / 50 / 60 (K 0.74 / 0.72 / 0.68; BIRCH 0.72 / 0.69 / 0.65). With the draw and year taken out of ln(DBH) at both ages, I get K −0.03 / −0.05 / −0.06 and BIRCH 0.35 / 0.35 / 0.26, against the design's 0.03 / 0.00 / −0.05 and 0.35 / 0.35 / 0.24.
- **Deaths by fifth, alive at 60 by fifth at 20, and the dying tree.** All reproduced. K, yearly deaths by fifth: 15.7 / 12.8 / 11.0 / 10.0 / 8.5 at 20-25, 7.3 / 6.0 / 4.6 / 3.6 / 2.3 at 45-50, 6.7 / 3.9 / 3.3 / 2.3 / 1.5 at 50-60. Alive at 60 by fifth at 20: 1.3 / 2.8 / 4.2 / 5.7 / 11.6 %. The 7,668 trees that die at 24-30 have 0.964 of the plot's mean diameter: 12 % are under 0.8, 48 % at 0.8-1.0, 40 % at or over the mean. A tree that grew under half the mean dies at 28.3 % a year.
- **Catch-up is growth, not selection (CONFIRMED, new).** A year-3 tree's mean DBH over a year-0 tree's is 0.15 / 0.49 / 0.67 / 0.79 / 0.88 / 0.92 at 11 / 15 / 20 / 30 / 45 / 60 among survivors. It is the same within one draw band (0.97-1.03: 0.15 / 0.49 / 0.68 / 0.78 / 0.83 / 0.83) and on the trees alive at 45 traced back (0.16 / 0.50 / 0.69 / 0.82 / 0.88). The design's "late trees catch up because every tree gets the curve's step at its own age" holds.
- **One summary line is misleading.** "A tree in the thickest fifth at 20 has an 88 % chance of being dead by 60." Only 474 of 9,324 stems per hectare live from 20 to 60 (5.1 %). So even if every survivor came from the top fifth, 75 % of that fifth would have to die. The fair figure is the ratio: top fifth 11.6 % alive against bottom fifth 1.3 %, nine to one. Deaths do pick on size, mildly, and the dying tree's 0.96 of the mean is the real evidence of a near-lottery.

## 2. Hynynen et al. 2002, checked at the source (CONFIRMED)

I read the copy in `birch-data/hynynen_2002/` with a PDF text tool and looked at its page scans as images, pp. 22, 24, 30-31, 40-41, 49-53 and 55-58 (the scan has its own page numbers). I ran nothing from it.

| Model | As printed | The design | Notes |
|---|---|---|---|
| Eq. 47, Table 32 (pp. 50-51) | p_comp5 = 1 / (1 + exp(α0 + α1 d_s + α2 RDFL + α3 d_s RDFL)); "Deciduous SC1-8": 3.014, 0.1015, −9.313, 0.4073; the chance of dying in the coming 5 years | Correct | There is no exponent on the bracket (the text layer shows a stray "5"; the scan shows only the subscript of p_comp5) |
| Its data (p. 24) | five experiments on planted or self-sown stands, silver and downy birch, fertile mineral soils. In the source's words, "Thinning experiments included untreated control plots". One 5-year period per stand, 7,427 trees, 476 dead (6.4 %). Plot mean age 17-50, dominant height 12.3-22.4 m, 370-3,051 stems/ha | The design says "five experiments with untreated controls" | **The data are mostly thinned plots**, with untreated controls among them. No diameter range is printed |
| RDF, RDFL (Eqs. 20-23, pp. 30-31) | ga_i = 1 / N_max at the tree's own stump diameter; RDF sums ga over all trees per hectare; RDFL sums it over the trees larger than the subject tree, all species | Correct | The whole plot is the right analogue of the source's stand |
| Eq. 3 (p. 22), Eq. 52 (p. 55) | d_s = 2.0 + 1.25 d; D_gs = 2.0 + 1.25 D_g, D_g the mean weighted by basal area | Correct | |
| Eq. 50, Table 34 (p. 53) | ln N = α0 + α1 ln D_gs + u + e. Silver birch: 14.1979, −2.2178; std(u) 0.160, std(e) 0.106 | Correct | Between stands the line itself scatters with an SD of 16 % in stems |
| The procedure (pp. 49-50, 55-58) | Eq. 47 first; at the end of the 5-year step, if stems exceed N_max every tree's stem number is multiplied by N_max / N (Eq. 61: evenly). Under D_gs 12 cm the line is its tangent at 12 cm. A step may cut stems by at most 1.5 times what the line's own slope gives | "Evenly" is the report's own rule; "by odds" is the design's | The 1.5-times limit and the yearly (not 5-yearly) cap are not in the design. Say so |
| Eq. 33, Table 24 (pp. 40-41) | i_h5 = i_hdom5 (d / D_dom)^((a1 + a2 PLANT) RDFL); birch 1.54405, −0.81202; RMSE 0.5623 m, 2,572 observations | Correct, built as H | The design's H drops the model's tree-level residual. Nothing in the design replaces it |

**Two problems the design does not state.**

1. **The sign of Eq. 47 flips.** The RDFL term is (−9.313 + 0.4073 d_s) RDFL. It is positive, so crowding raises the chance of death, only for d_s under 22.87 cm, that is d under 16.69 cm. A thicker tree with more larger neighbours dies *less* by the printed equation. In K the share of trees past that size is 0.00 at 20-35, 0.78 at 45 and 0.93 at 50-60 (CONFIRMED). For most of the model's trees at 45-60, "death by standing" runs backwards or not at all. On a stand scaled onto the line and shared by odds, the thickest fifth dies faster than the fourth at 50-60 (3.11 against 2.37 % a year; section 3). The data's thick trees were probably dominants with RDFL near 0, so this corner was likely never fitted (SUSPECTED).
2. **More is outside the data than the design says.** The design labels the time before 17 years and above 3,051 stems/ha. Two more limits apply. Plot age is over 50 at 50-60. Dominant height passes 22.4 m: the approved top height is 21.4 m at 50 and 23.1 m at 60 (plan, section 8), so it crosses at about 52-55.

**The comparison, recomputed for one stand at 30 and at 50 (CONFIRMED arithmetic).** I applied Eq. 47 to every living tree in K's 20 plots, with RDFL over the whole plot. Yearly deaths by fifth of DBH, smallest first:

| Period | K's RDF | Model today | Eq. 47 alone, K's stand as it is | Stand scaled onto the line: Eq. 47 alone | On the line, excess by odds | On the line, excess evenly (the source's Eq. 61) | Deaths the line needs, % a year |
|---|---|---|---|---|---|---|---|
| 30-35 | 0.62 | 14.3 / 10.4 / 8.4 / 7.5 / 6.9 | 3.9 / 1.8 / 0.9 / 0.5 / 0.3 | 13.4 / 5.2 / 2.1 / 0.8 / 0.3 | 31.1 / 17.7 / 9.0 / 4.0 / 1.6 | 19.3 / 11.6 / 8.7 / 7.5 / 7.0 | 10.4 |
| 45-50 | 0.78 | 7.3 / 6.0 / 4.6 / 3.6 / 2.4 | 0.25 / 0.08 / 0.05 / 0.04 / 0.03 | 0.33 / 0.07 / 0.04 / 0.03 / 0.03 | 12.7 / 5.0 / 3.1 / 2.4 / 2.4 | 5.1 / 4.8 / 4.8 / 4.8 / 4.8 | 4.9 |
| 50-60 | 0.81 | 6.7 / 3.9 / 3.4 / 2.3 / 1.5 | 0.11 / 0.03 / 0.02 / 0.02 / 0.02 | 0.12 / 0.02 / 0.01 / 0.01 / 0.02 | 8.7 / 3.5 / 2.5 / 2.4 / 3.1 | 3.9 / 3.8 / 3.8 / 3.8 / 3.8 | 3.8 |

"Deaths the line needs" is 1 − (D_gs at the end / D_gs at the start)^−2.2178, with D_gs grown as K's survivors' quadratic mean grew. "By odds" multiplies every tree's odds by one factor until the line is met: 6 at 30-35, 87 at 45-50, 246 at 50-60. RDF is the source's sum of growing spaces. K's stems against the line, as T2 and the design measure it (D_gs weighted by basal area, the tangent under 12 cm), are 0.64 / 0.82 / 0.85 / 0.94 at 30 / 45 / 50 / 60, and I reproduce them. At 20 RDF is 0.53, but stems against the tangent line read 0.86. The tangent matters there, and the design's formula for M leaves it out.

**What the numbers say.**
- "Too equal in who dies" is right *for the stand as it is*. K's stand sits under the line, and there Eq. 47 alone takes 0.04-0.09 % a year at 45-60, against the model's 4.6 % and 3.4 %. The design's "50 to 150 times" holds.
- **But the published system does not run Eq. 47 alone on a stand at the line.** Under M, stems rise to the line by about 25-30 (the design's own forecast). From then on the line dictates 4-10 % a year of deaths. Eq. 47 supplies under 1 % of them at 45-60 and about 40 % at 30-35. So at 45-60 who dies is about 98 % the sharing rule. With the report's own rule (evenly) the large trees die at 4-5 % a year, much as they do today. The phrase "the published birch model all but spares large trees" is true of Eq. 47, not of the published model at the line.
- **The model's diameter growth sets the line's death rate.** Deaths on the line are 2.2178 times the relative growth of D_gs. The design reads survivors' growth as 2.3-2.7 times Model 31 and calls the turnover fast. But Model 31's level rests on an assumed site index, temperature sum and no back-transform. Hagemeier's own two stands give quadratic means of 19.1 cm at 45 (880/ha, 25.2 m²/ha) and 29.4 cm at 67 (420/ha, 28.5 m²/ha). That is 2.3 cm in 5 years and 3.3 % of stems a year between them, against K's 2.40 cm and 3.8 % (my arithmetic from the printed table; two different stands, so SUSPECTED). So the measured pair to hand sides with the model's growth and turnover, not with Model 31's level. The "fast turnover" finding should stay SUSPECTED and not be built on.
- "Growth by size, hidden by the draw" holds as a pattern, since the power of relative diameter does not depend on site index or temperature sum.

## 3. The literature (opened at the publisher today)

| Source | What the design takes | What I read | Holds? |
|---|---|---|---|
| Martiník et al. 2018, Silva Fennica 52(5) 9985, Table 1 (fetch tool) | DBH SD over mean 0.79 / 0.68 / 0.62 / 0.63 / 0.46 / 0.47 / 0.36 / 0.36; plot ranges; "no treatments" | Table 1 as quoted (mean, then SD in brackets: 0.72 (0.57), 0.97 (0.66), 1.89 (1.18), 2.24 (1.40), 7.00 (3.23), 7.18 (3.40), 10.20 (3.66), 10.33 (3.74)). Tipecek was **sown** in 2010; the other three were self-sown after windthrow or felling. 10 m² plots at Tipecek and Breziny, 25 m² at Dubska and Skrchov; ten plots each; all live trees over 1.3 m. No silvicultural treatments | Yes. Three caveats: (a) **S's σ is tuned partly on the sown stand** (the label says "4-9 years", which takes in Tipecek); Breziny alone gives about the same 0.7, so tune on Breziny and say so. (b) The upper heights in Table 1 jump 7 → 9 m, 15 → 18 m and 17 → 23 m in one year, so "taller for their age than the model" rests on an unreliable column. (c) Stems are printed the same in both years, so the two rows per stand are not independent. Dubska and Skrchov rest on about 120 and 70 trees |
| Hagemeier & Leuschner 2019, Forests 10(3):265, Table 3, Methods 2.1-2.3 (Chrome; the fetch tool got HTTP 403) | the targets and their reading | Birch site 1: 45 years, 25.2 m²/ha, 880/ha, 85 % birch, height 20 ± 3 m, DBH 19 ± 6 cm; site 2: 67 years, 28.5, 420, 98 %, 25 ± 3, 25 ± 3. Footnote: "arithmetic mean". Two 1,000 m² plots per stand in sections of high canopy closure, gaps over about 25 m² avoided; Betula "somewhat younger" than the 80-120-year norm; for measurements, trees of the target species with conspecific neighbours were chosen where others were admixed | Read fairly except the 0.25. **All four figures are whole numbers**, so 0.32 = 6/19 covers 0.28-0.35, and 0.12 = 3/25 covers 0.10-0.14. **The basal-area mismatch is general in that table**, not a clue to the SD. My arithmetic on the printed stems, mean and ±: Fagus site 9, 52.2 against 30.8 printed; site 10, 43.6 against 24.2; Quercus site 4, 29.4 against 23.8; Carpinus site 5, 22.8 against 31.5 (with ± 1 on 29 cm, which can't be an SD of 345 trees). Mismatches go both ways, so they can't shrink birch's SD to 4.7 |
| Zeltiņš et al. 2018, Forests 9(2):52, Table 1 (Chrome) | genotypic CV 9.5 ± 1.5 % for DBH; V = 0.09 | 22 **grafted plus-tree clones**, 40 years, 400/ha, former farmland. DBH 27.7 cm, SD 5.6, H² 0.21 ± 0.06, CVg 9.5 ± 1.5 %; height 26.2 m, SD 2.2, H² 0.14, CVg 3.2 %; survival 84.4 % | Numbers right. The design says "clones" but not "plus-tree" or "grafted". Plus trees are selected, so their spread is narrower than a self-sown stand's genotypes. Grafts carry rootstock effects. And growth at 400/ha has little competition. So 0.09 is a floor estimate; label it so |
| Hynynen et al. 2002 | see section 2 | | Yes, with the two gaps above |
| Dahlgren Lidman et al. 2021 | the 300 thickest are 1.83 times the quadratic mean | Not re-opened by me | The comparison is not like for like: about 4,430 birch/ha under spruce against the model's 846/ha. The ratio depends strongly on stem number. Drop it or label it as such |
| Gailis 2020, Maleki & Kiviste 2016, New Forests 55:157, Metsaranta & Lieffers 2008, Aosaar 2016 | as listed | Not re-opened by me | Gailis 2020 is planted progeny and is labelled. Metsaranta & Lieffers is jack pine and is labelled. Nothing else is carried from another species unlabelled |

No figure from a planted trial or another species enters a model value unlabelled. The one carried value (V from Zeltiņš) needs "grafted plus-tree clones, low density" added to its label.

## 4. The design, part by part

**A small case by hand (CONFIRMED arithmetic on K's own trees).** A is the mean tree that came up in year 0 with a draw of 0.97-1.03; B is the same but a year late. Inputs per year are K's means over 20 plots. Under H, a tree's height step is the dominants' step times (d / D_dom)^(1.54405 RDFL). Its hazard is Eq. 47 at K's density, with no line. Diameters are held at K's, so the carbon feedback that would widen the gap further is left out.

| Age | A: d, h, RDFL | B: d, h, RDFL | Today's height gap, m | Under H: the step factor for A, B | Under H: the gap, m | Eq. 47 hazard, A / B, % a year | Alive since 20 under Eq. 47, A / B |
|---|---|---|---|---|---|---|---|
| 20 | 4.70, 9.23, 0.18 | 4.17, 8.67, 0.34 | 0.56 | 0.93, 0.82 | 0.56 | 1.3 / 3.8 | 1.00 / 1.00 |
| 25 | 6.64, 11.71, 0.24 | 6.12, 11.24, 0.38 | 0.47 | 0.92, 0.84 | 0.83 | 1.2 / 2.9 | 0.94 / 0.84 |
| 30 | 9.69, 13.81, 0.33 | 9.04, 13.42, 0.45 | 0.39 | 0.90, 0.83 | 1.01 | 0.8 / 1.6 | 0.89 / 0.76 |

- **H works as stated, but slowly.** B falls further behind, by about 6 cm a year more than today, which is 7 % of its height by 30.
- **M works as stated only below the line.** Under Eq. 47, B lives with 0.76 odds over ten years where today it would have about 0.3. But K's stand loses 9,324 to 2,640 stems/ha between 20 and 30. Once stems reach the line (about 25 by the design), the line's 10 % a year is shared by the cap. By odds, B, being small and overtopped, carries most of it. Evenly, it is a lottery.
- So the lingering the design relies on lasts only from about 12 to 25 years. **The spread gained there is what M can deliver.** At 45-60 it runs on the sharing rule.

**Each part, for its stated reason.**

| Part | Makes trees differ for the stated reason? | By the stated amount? | A draw under another name? | Free numbers |
|---|---|---|---|---|
| S, a patchy start | Yes, if local density slows growth. Today density now explains 0.03-0.06 of DBH variance, and under M deaths no longer read local density | Unknown. σ and ℓ are confounded: a 10 m² cell (3.2 m square) averages a field with ℓ = 3 m, so σ 0.62 does not give a count CV of 0.7 without that averaging worked out. The 0.7 is itself an SD guessed from the range of ten plots | A random field of place: physical, but new randomness | σ TUNED on a SUSPECTED figure; ℓ unsourced |
| H, height by standing | Yes (E, and the hand case) | E: height SD on stems is level, and DBH spread falls to 0.11 | No | None new (sourced, built) |
| M, death by standing | Yes, below the line and for trees under 16.7 cm. At the line, only through the sharing rule | The forecast 0.14-0.18 at 45 and 0.13-0.17 at 50 contains today's 0.143 and 0.148. The design's own desk projection of K's stand under the printed rules gives 0.139 / 0.142 / 0.150 | No | The sharing rule (unsourced); yearly conversion (derived); 8 coefficients (sourced, applied outside their data). It removes 10 TUNED values |
| V, vigour 0.09 | It *is* the draw, made larger | about 0.01 with all four on (design) | Yes, the draw itself | 1, DERIVED, a floor (above) |

Net: M removes ten tuned numbers and adds one unsourced rule. S adds two, one of them unsourced. V re-sizes one.

**The falsifying tests.**

| Test | Problem | Fix |
|---|---|---|
| 1. Lingering, at least half alive 4 years later at 20-35 | Once the stand is on the line (about 25-35), the smallest fifth dies at 31 % a year by odds and 19 % evenly (section 2). Half survive 4 years in neither case. The threshold comes from Eq. 47 without the line and has no measured source | Read it only before the line binds (12 years until stems reach 0.9 of the line), or as a ratio against today. Or take the threshold from measured odds by relative growth (Maleki & Kiviste 2016, Tab. 3), labelled |
| 2. Thickest fifth under 1 % a year at 30-60 | On the line with the model's growth, the thickest fifth dies at 1.6 / 2.4 / 3.1 % by odds and 7.0 / 4.8 / 3.8 % evenly. **Tests 2 and 6 contradict each other** unless diameter growth falls. Nothing measured says 1 % | Make it relative: the thickest fifth's rate at most a stated fraction of the smallest's, and the dying tree's mean relative diameter under 0.8 (today 0.96). Label both thresholds as estimates |
| 3. No catching up, 15 to 30 | Survivors only. Under BIRCH, where H does hold late trees back, the year-2 and year-3 ratio still rises 0.48 → 0.53 → 0.58 at 15 / 20 / 30, because small late trees die | Read it on every tree that came up, the dead at their last size, or as relative diameter growth at equal size |
| 4. Rank with draw and year out, over 0.3 | BIRCH already gives 0.35 / 0.35 / 0.26 at 45 / 50 / 60 with today's death rule, so it says little about M | Keep it, but don't count it as evidence for M |
| 5, 6, 7 | 6: the line's own between-stand SD is 16 %, so 0.9-1.1 is a mean-level test; fine | Keep |

## 5. What it breaks

| Row | Today at 45 / 50 / 60 | Room (plan, section 8) | With M (SUSPECTED unless marked) |
|---|---|---|---|
| Stems against the line | 0.82 / 0.85 / 0.94 (CONFIRMED) | none set | Up to about 1.0 by design: more stems at 45-60 than the tuned 880 at 45 (one stand) |
| Basal area, guard 28.5 | 24.0 / 24.7 / 26.8 | 4.5 / 3.8 / 1.7 | Design: 27-30 at 45-60 for M alone; a stand on the line at spread 0.15 carries about 29. **Likely fail** |
| LAI, Baltic top 4.5 | 4.79 / 4.51 / 4.29 | 50 fails by 0.01 already; 60 has 0.21 | Design: +0.0 to +0.3. **Likely fail at 60; 50 worse** |
| Light, % | 17.5 / 18.2 / 19.5 | at most 19.8 for stand trees (B) | Design: −0.5 to −2 points |
| Top height, approved | 21.39 at 50, 23.14 at 60 | no lower beyond noise (DECISIONS 111) | Depends on which trees are the 100 thickest in a denser stand; E saw +0.3-0.9 m under H. Must be printed |
| DBH spread, do-no-harm at 45 and 50 | 0.143 / 0.148 | not lower by more than 2 paired SE | H alone gives 0.11. H + M's forecast reaches down to 0.14 / 0.13. **Could fail** |
| Branch wood | not forecast | | More, smaller trees: unknown. Print the whole-stand branch share |
| Run time and memory | 35,235 tree-years a plot at 1-60 (CONFIRMED, stand logs) | | With stems on the line from 20, about 3,500 more tree-years at 20-60 (+10 % in all; +39 % at 20-60), plus a sort per year for RDFL. Modest |

**Is the forecast a real one?** For 30 years, yes. 0.18-0.25 against today's 0.13 can be shown wrong. At 45-50 it barely is, since its range contains today's value. The stems and basal-area rows are real forecasts, and they forecast fails.

## 6. The targets

- The design changes no target. Its reading of the 67-year stand as "probably thinned from below" is labelled SUSPECTED. Asking whether to mark it doubtful is the owner's call. It sits in a held-back row already (plan, question 7).
- **One reading leans one way:** "0.32 reads 0.25-0.32". The table's rounding gives 0.28-0.35. Its basal-area mismatch is general, so it says nothing about the SD. This should read "0.28-0.35, rounding; the table's basal areas do not square in most of its rows, so they cannot correct it".
- **The owner's question 1 would in effect demote the 45-year target.** It asks that the young Martiník stands become the rows that must improve, with 45-60 kept as do-no-harm. In the plan, spread at 45 is already a guide row with do-no-harm (section 8, row 77; decisions 1 and 7), so nothing is loosened as long as 0.32 stays printed and a miss is still called a miss. Adding Martiník rows is adding targets, not loosening. But the question must say plainly that the 0.32 row stays, and that a release cannot claim it until it is met.

## 7. The smallest build, what to cut, and what to ask first

**Build first:** M with H, as the design says, with these changes:
1. Two over-line settings, two arms: H + M (evenly), the report's own rule, and H + M (by odds), the design's, labelled as an estimate. Drop "M alone" from the first round (E and the desk projection already say what it does to spread), or run it as a third arm if the budget allows. Seeds 1-5.
2. The cap as printed: D_gs weighted by basal area, the tangent under 12 cm (at 20 it moves stems against the line from 0.55 to 0.86), and a note that the source applies it every five years with a 1.5-times limit.
3. Hand-worked trees for Eq. 47 that include one past 16.7 cm with RDFL above 0, so the reversed sign is on record. The label gives every limit of the data: age 17-50, dominant height 12.3-22.4 m, 370-3,051 stems/ha, mostly thinned plots.
4. Restated tests 1-3 as in section 4. Print each test both before the line binds and after.
5. Print basal area, LAI at 50 and 60, top height and stems against the line beside spread, so the likely fails are read in the same table.

**Cut or defer:** S, until its σ and ℓ have been worked out on 10 m² cells by arithmetic and tuned on the self-sown stand only. V, until H + M has run: it is a value and changes nothing structural. The "fast turnover" verdict, which the measured pair to hand contradicts.

**Ask the owner before any build:**
1. Basal area at 45-60 will likely pass the 28.5 guard, and LAI at 60 its 4.5 top, if the stand sits on the published line. Does a fail there stop adoption, or is it read against the line's own measured stands?
2. Which over-line rule is the default if both arms work: the published one (evenly) or the design's (by odds, not sourced)?
3. May Eq. 47 run outside its data (before 17, past 50 years and 22.4 m, and past 16.7 cm where its crowding term flips), labelled extrapolated? Or should today's rule hold outside it?
4. The design's question 1, restated: the 0.32 row at 45 stays printed and is a miss until met. Do the young measured stands become guide rows?

## How I checked, and limits

- Scripts are my own, written today, and do not reuse the design's. Data come from the fetched tree lists and stand logs only. Death rates use the tree lists at the period ends, with a year's chance compounded (1 − alive^(1/years)).
- "On the line" scales each plot's RDFL so its RDF is 1 and keeps its size distribution; it is a desk case, not a run. Required deaths use K's survivors' diameter growth, which a denser stand would slow. Eq. 47's hazard per year is −ln(1 − p5) / 5, as in the design.
- The hand case holds diameters at K's means, so it shows the height and survival mechanisms only, not their feedback on carbon.
- Sources: Hynynen et al. 2002 read by me from page scans and text. Martiník et al. 2018 Table 1 and text through the fetch tool (a summarised page; its numbers match the design's division). Hagemeier & Leuschner 2019 Table 3 and Methods, and Zeltiņš et al. 2018 Table 1 and abstract, at the publisher's pages in Chrome. I opened no other source and closed my own browser tab.
