# Earned height and size differences: design

2026-11-11. Model: Fable 5.2 (ID `claude-fable-5-2`). Track: the review's findings 1 and 2.

Design only. Nothing was run, committed or changed except this file. "Saved plots" means small reads of the 20 saved plots on today's defaults (`node_cd2_C`, `node_cd2_C2`; they give the fresh run's numbers).

## Summary

1. **A forest tree's height is the curve times its draw, to the centimetre.** At 30, every saved height equals "the curve's yearly steps × the tree's drawn vigour ÷ the dominants' drawn vigour", with a misfit of 0.01 m. Light, water and carbon slowed no surviving tree. CONFIRMED on 5,280 trees.
2. **Who survives is mostly the draw too.** Of the top quarter by drawn vigour, 10.6 % live to 45. Of the bottom quarter, 1.0 %.
3. **Carbon can't hold a leader back.** The leader's shoot is paid first and costs 0.008 % of a stand tree's yearly carbon at 50.
4. **Crowns are capped alike.** Every tree in a plot gets the same limit on limb reach, so crown widths differ by 4-7 %. Diameters can't spread while that holds. The crown track covers it (its P1).
5. **Proposal.** Replace the draw on height with a published rule: the dominants' step from the curve, times a modifier of the tree's own diameter relative to the dominants (Hynynen 1995). Keep the draw in carbon only. Make a tree that can't pay for its sapwood cut its leader by the same share. No new tuned value.
6. **What to expect.** Height spread grows, probably not to the measured 3 m: arithmetic on the saved diameters gives 1.04 to about 1.3 m at 45, before any feedback. Diameter spread should move little until crowns may differ.

## 1. The rule today

Each year, for every tree (`treegen/growth.py`):

| Step | Rule | Where |
|---|---|---|
| Curve step | curve(age) − curve(age − 1), Eriksson SI 23 | `growth.py:2525`; curve `2475-2498`, `reference.py:15-18` |
| Light | min(1, light at the leader ÷ 0.6) | `growth.py:2521`; 0.6 is TUNED so a stand tree is never limited |
| Water | min(1, stomatal opening ÷ 0.8) | `growth.py:2522` |
| Vigour | the tree's `resource.alpha` ÷ `reference_alpha` | `growth.py:2523-2524` |
| Allowed height | a running total grows by step × light × water × vigour; the leader may grow up to it, at most 1.25 steps a year | `growth.py:2529-2531` |
| Carbon | the leader's shoot skips the carbon solve and is paid first; it is cut only if that one shoot costs more than the whole pool | `growth.py:1860`, `1913-1925` |

A single tree has alpha 4.8 over reference 4.8, so its vigour is 1 and its height is the curve.

In a plot (`treegen/plot.py`):
- Each tree draws a vigour, exp(normal(0, 0.06)), which multiplies its alpha: `plot.py:131-132`. Alpha multiplies the carbon it fixes: `growth.py:907`.
- Every year before the trees grow, the plot sets `reference_alpha` to 4.8 × the mean draw of the 100 thickest per hectare: `plot.py:388-389`, `214-228`.
- So a plot tree's step = curve step at its own age × light × water × (its draw ÷ the dominants' mean draw).

## 2. What the saved plots show

Spread, mean of 20 plots:

| Measure | 30 | 45 | 50 | 60 | Measured stands |
|---|---|---|---|---|---|
| Living stems per plot | 264 | 85 | 67 | 47 | |
| DBH spread, SD ÷ mean | 0.13 | 0.14 | 0.15 | 0.15 | 0.32 at 45, 0.12 at 67 |
| Height SD, m | 0.85 | 1.04 | 1.06 | 1.09 | 3 at 45, 3 at 67 |
| Height, 10th to 90th percentile, m | 2.17 | 2.58 | 2.62 | 2.73 | about 7.7 if the SD is 3 (my arithmetic) |
| Mean height, m | 13.77 | 18.93 | 20.04 | 21.89 | 20 at 45, 25 at 67 |
| Height of the 100 thickest/ha, m (curve) | 15.56 (15.84) | 20.48 (20.80) | 21.58 (21.95) | 23.27 (23.75) | |
| Height on diameter, correlation | 0.91 | 0.85 | 0.87 | 0.90 | no source in hand |
| Height on diameter, slope, m per cm | 0.64 | 0.33 | 0.29 | 0.25 | at most 0.5 at 45 (3 m ÷ 6 cm) |
| Crown width spread, SD ÷ mean | 0.04 | 0.06 | 0.07 | 0.07 | |
| Leaf area per tree, SD ÷ mean | 0.24 | 0.26 | 0.27 | 0.28 | |

How much is the draw:

| Saved plots | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Height explained by draw + germination year (R²) | 1.00 | 0.89 | 0.92 | 0.99 |
| Height explained by the draw alone (R²) | 0.79 | 0.84 | 0.90 | 0.97 |
| DBH explained by draw + germination year (R²) | 0.84 | 0.82 | 0.84 | 0.85 |
| Misfit of "curve × draw ÷ dominants' draw" to saved height, SD m | 0.01 | 0.35 | 0.27 | 0.10 |
| Mean draw of the 100 thickest/ha | 1.132 | 1.125 | 1.125 | 1.123 |
| Light per unit of leaf, 10th to 90th percentile tree ÷ dominants | 0.95-1.05 | 0.94-1.04 | 0.94-1.05 | 0.92-1.04 |
| Carbon fixed, 10th percentile tree ÷ dominants | 0.39 | 0.41 | 0.41 | 0.41 |

- The draws aren't saved. I redrew them from each plot's seed in `plot.py`'s order and checked: positions match to 0.0005 m and ages exactly (seeds 1, 7, 20).
- The misfit at 45 and 50 isn't traced. SUSPECTED: damage and catch-up.
- Trees don't differ in light per leaf, only in how much leaf they hold: the short ones shed what is shaded.
- The dominants' alpha is 5.4-5.5, not 4.8, because the high draws win. Stand totals were tuned with that.

Rank among survivors (Spearman, mean of 20 plots, lowest to highest plot):

| From | To 45 | To 50 | To 60 |
|---|---|---|---|
| Height at 15 | 0.60 (0.46-0.70) | 0.57 (0.42-0.72) | 0.52 (0.32-0.70) |
| DBH at 15 | 0.62 (0.47-0.73) | 0.60 (0.47-0.71) | 0.55 (0.33-0.71) |
| Height at 30 | 0.90 | 0.90 | 0.90 |
| DBH at 30 | 0.88 | 0.85 | 0.81 |
| Shortest quarter at 15, % alive | 3.0 | 2.3 | 1.5 |
| Tallest quarter at 15, % alive | 11.0 | 9.0 | 6.9 |
| Lowest quarter by draw, % alive | 1.0 | 0.6 | 0.3 |
| Highest quarter by draw, % alive | 10.6 | 8.9 | 7.0 |

At 15, height is 77 % germination year. From 30 on the order is fixed, because the draw is. No measured rank figure for birch is in hand.

**Where 0.32 and 3 m come from.** Hagemeier & Leuschner 2019a, Table 3: stand 1, age 45, dbh 19 ± 6 cm, height 20 ± 3 m. 6 ÷ 19 = 0.32. The arithmetic is right. Checked today at the publisher (Methods 2.2; the table itself was read by the sources job on 2026-11-09):
- Two round plots of 1,000 m² per stand. DBH on every tree.
- Height was measured on 32-46 trees a plot. The rest were read off a height-on-diameter curve, so the printed height spread is partly a curve's.
- The text I could read doesn't say whether the table's ± is an SD (the figures' is), or whether it covers the 15 % of stems that aren't birch. SUSPECTED SD.
- By rounding, the spread is 0.28-0.35 and 2.5-3.5 m.
- The second stand (67 years, 98 % birch) has 0.12. The model's 0.15 at 60 is near that. So the diameter fault is clear at 45 and younger, not at 60. The height fault (a third of measured) holds at both ages.
- Young planted trials give DBH spread 0.25-0.30 at 15-19 (Jones 2021 Table 2, Jones 2023 Table 1, read 2026-11-09). The model gives 0.16 at 20, from a natural start, so not like for like.

## 3. Published basis

| Source | What it gives | Opened? |
|---|---|---|
| Elfving 2010, Heureka report, p. 2 and Appendix 9 p. 58 | The site curve as a difference equation: height in 5 years from a tree's own height and age. It is applied to single trees. Top height is read at the 100 thickest per hectare. Birch values 7, 394, −1.387 match the species file | Yes, SLU's own copy |
| Fahlvik, Elfving & Wikström 2014, Silva Fennica 48(2) 1013, section 2.2.2 | In Heureka that step is then adjusted for each tree by the basal area of larger trees. I found the adjustment's numbers neither there nor in Elfving's report | Yes, publisher |
| Hynynen 1995, Silva Fennica 29(3): 225-246, pp. 234-235, eq. 5, Table 6 | Tree height growth as "potential height growth times a modifier function". Potential = the dominants' step. Modifier = (d/Ddom) to the power (0.2445·IHdom − 0.4710·(d/Ddom)^0.8045). Ddom = mean of the 100 thickest per hectare. Crown ratio and basal area added nothing. Scots pine, 11 thinning trials, 3,406 observations | Yes, publisher's scan |
| Hynynen et al. 2002, Metla 835 (MELA) | Believed to hold the same kind of model with silver birch values | **No.** Record opened at Luke's Jukuri. The text is a 16.5 MB PDF, which is a download. UNVERIFIED |
| Gailis et al. 2020, Silva Fennica 54(2) 10220, Tables 2-3 | Heritable spread of height 5.5-11.4 % at 10-14 years; heritability 0.30-0.64. Context for `plot.vigour_sd` | Yes, through the fetch tool's summary |
| Weiner 1990; Schwinning & Weiner 1998; Pretzsch & Biber 2010 | One-sided competition for light: the tall take more than their share | **No** (paywall or login). UNVERIFIED, named from memory |
| Perttunen et al. 1996 (LIGNUM) | Every shoot's length, the leader's too, comes from one carbon solve. Cambium takes the leader out of it (`growth.py:1860`) | Paper not opened; the code is CONFIRMED |

## 4. The design

**Change 1. Status in place of the draw** (`height_driver.status`, off until approved).
- Where the plot sets its reference now (`plot.py:388`), it gives each tree a status instead:
  - Ddom = mean DBH of the 100 thickest per hectare (already found at `plot.py:222-225`).
  - IH = 5 × the curve's step this year (m per 5 years).
  - m = (d/Ddom)^(0.2445·IH − 0.4710·(d/Ddom)^0.8045).
  - d/Ddom is held inside 0.4-1.1 and IH inside 0.6-3.6, the range of Hynynen's data (his Fig. 5).
  - status = m ÷ the mean m of the 100 thickest. A tree with no DBH yet has status 1.
- In `growth.py:2529` the step becomes curve step × light × water × status. Alpha no longer appears there.
- A single tree has status 1, so it is unchanged.

The modifier, at the curve's step for each stand age:

| d ÷ Ddom | Age 15 | Age 30 | Age 45 | Age 50 | Age 60 |
|---|---|---|---|---|---|
| 0.4 | 0.59 | 0.79 | 0.95 | 0.99 | 1.02 |
| 0.6 | 0.78 | 0.92 | 1.02 | 1.04 | 1.06 |
| 0.8 | 0.91 | 0.98 | 1.03 | 1.04 | 1.04 |
| 1.0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 1.1 | 1.03 | 1.00 | 0.98 | 0.97 | 0.97 |

It separates trees while the stand is young and growing fast, and lets small trees keep up later. Today's rule does the reverse: thin trees grow 0.90-0.93 of the dominants' step at 30-50.

**Change 2. Pay first** (`height_driver.sapwood_before_leader`, off until approved).
- Today the leader is paid before the sapwood the standing leaves need. A tree that can't pay that sapwood still gets its full height.
- Proposed: when the pool can't cover the year's must-haves (leader, limbs, that sapwood: `c0` at `growth.py:1909`), the leader is cut by pool ÷ c0, as the rings already are at `growth.py:1931`.
- No value. Basis: in a pipe model a taller stem is more pipe. The project's reading of Mäkelä 1986; not re-opened by me.

**What stops a suppressed tree.**
1. Its status falls as its stem falls behind. This is strong when young and weak after 45.
2. If it can't pay its sapwood, its leader is cut by the same share.
3. Light at the leader under 0.6 (unchanged).
4. The mortality rules (unchanged).

**The random vigour.** It stays in carbon only, at 0.06, labelled VERIFY as now. It is not retuned. Dropping it would cut the dominants' carbon by about an eighth and move LAI, light and stems. Arm D tests it at zero.

**Not changed:** the curve, 0.6, 0.8, 1.25, mortality, crowns.

**Arithmetic preview, not a run.** Saved diameters, the modifier applied from 11 on, no feedback of height on light:

| | 30 | 45 | 50 | 60 |
|---|---|---|---|---|
| Height SD today, m | 0.85 | 1.04 | 1.06 | 1.09 |
| Height SD, preview, m | 1.41 | 1.26 | 1.23 | 1.16 |
| 10th to 90th percentile today, m | 2.17 | 2.58 | 2.62 | 2.73 |
| 10th to 90th percentile, preview, m | 3.72 | 3.28 | 3.20 | 2.93 |
| Height of the 100 thickest today, m | 15.56 | 20.48 | 21.58 | 23.27 |
| Height of the 100 thickest, preview, m | 15.38 | 19.92 | 20.99 | 22.60 |

The preview's dominants sit 0.6-0.7 m lower at 45-60, because the trees thickest at 45 weren't the thickest at 15. A real run may differ. Arm B is the answer if it doesn't.

**Change 3, only if needed (arm B).** The plot's step = curve(next year) − the plot's present top height, kept between 0 and 1.25 curve steps. The stand's top height then follows the curve whoever the dominants are.

## 5. Sourced, tuned, by design, independent

| Value | Kind |
|---|---|
| Curve (7, 394, −1.387), top height at the 100 thickest | Sourced: Elfving 2010 p. 58, opened |
| Modifier form and 0.2445, −0.4710, 0.8045 | Sourced, for Scots pine: Hynynen 1995 Table 6. VERIFY for birch until Hynynen 2002 is read. Never tuned |
| Limits 0.4-1.1 and 0.6-3.6 | Read off Hynynen 1995 Fig. 5 by eye. VERIFY |
| `plot.vigour_sd` 0.06 | VERIFY, unchanged. Gailis's 5.5-11.4 % is a spread of height, not of carbon gain |
| `light_full` 0.6, `water_full` 0.8, `catch_up` 1.25 | TUNED against the model, unchanged |
| Pay first; status ÷ the dominants' mean | By design. No value |
| Top height on the curve | By design. Not a test |
| **Independent tests** | DBH spread, height spread and its 10th-90th range, height-on-diameter slope, rank from 15 and 30, stems/ha at 14 and 32 (Varik 2009: 1,350 and 3,208). Nothing is tuned against them and no arm is picked by them |
| Tuned against already | Stems/ha at 45 (880), LAI and light at 50 and 60 |

## 6. Test plan for the server

Same command as the fresh run: 1,000 m² plots, natural start, mortality on, to 60. Tree lists at 11, 15, 20, 22, 25, 30, 35, 40, 45, 50, 60.

| Arm | Setting | Seeds | Why |
|---|---|---|---|
| 0 | Today | 1-20, saved (`node_f5_plots`), once seeds 1-2 rerun bit-identical with the switches off | Control |
| N | `height_driver.reference_alpha=null`. No code change | 1-5 | The draw off height, nothing in its place. I expect height SD at 45 near 0.3 m |
| A | Change 1 | 1-5, then 1-20 | The proposal |
| A+G | Changes 1 and 2 | 1-5 | Does pay-first bind, and is it harmless |
| B | A + change 3 | 1-5, only if A's top height falls | The owner's rule |
| D | A with `plot.vigour_sd=0` | 1-5 | What is earned with no draw at all |
| A×P1 | A with the crown track's own-neighbour limb stop | 1-5, when it exists | Diameters need both |

- Pairs share positions, germination years and draws. They part after the first difference in damage (review, point 12), so read pairs by mean difference against 2 standard errors. Also grow 20 stand-grown single trees with A+G.
- Save per tree: draw, germination year, status, leader light, light and carbon factors. Per plot-year: the dominants' mean modifier, and top height by the approved definition.

**Must not break** (control values shown):

| Check | 30 | 45 | 50 | 60 | Rule |
|---|---|---|---|---|---|
| Light under the canopy, % | 16.0 | 17.7 | 18.2 | 19.5 | At 50 and 60 at most 19.8 |
| LAI | 5.44 | 4.72 | 4.51 | 4.29 | At 50 and 60 inside 3.6-5.4 |
| Top height, approved definition, m | 15.21 | not read | 21.39 | 23.14 | Inside SI 20-26, and no more than 0.3 m under the control |
| Stems/ha | 2,640 | 846 | 667 | 474 | At 45 inside the control's plot range, 760-980. Hagemeier's 880 stays INFO |
| Basal area, m²/ha | 18.9 | 24.0 | 24.7 | 26.8 | Reported |
| Stand trees: LAI / light % | 5.61 / 13.6 | not read | 4.73 / 16.6 | 4.60 / 17.1 | Still PASS at 50 and 60. Gate off: bit-identical |

Tests: as before (410 passed, the 4 known ones) plus new unit tests:
- the modifier's table values;
- two plot trees that differ only in alpha get the same height step;
- a tree thinner than the dominants gets a smaller step when young;
- a single tree is unchanged;
- a tree short of carbon has its leader cut by pool ÷ c0.

**Better** means, at 45, a paired difference over 2 standard errors toward the measured value and not past it:

| Independent row | 30 | 45 | 50 | 60 | Measured |
|---|---|---|---|---|---|
| DBH spread today | 0.13 | 0.14 | 0.15 | 0.15 | 0.32 at 45 (0.28-0.35); 0.12 at 67 |
| Height SD today, m | 0.85 | 1.04 | 1.06 | 1.09 | 3 at 45 and 67 (2.5-3.5) |

Also reported: the other independent rows of section 5, R² of height on the draw, LAI at 20-22.

**Decision rule, written before any result.**
- Adopt A (with G if harmless) if every must-not-break holds on 20 seeds.
- Use B only if A fails on top height alone.
- The spread isn't used to pick an arm, and nothing is retuned to move it. If it doesn't move, the report says so and the maintainer decides.
- If a must-not-break fails, adopt nothing and patch nothing in the same round.

## 7. Risks

- **Light at 60 has 0.3 points of room.** Shorter suppressed trees may hold less leaf. This is the likeliest failure.
- **Top height may sink** as the dominants change (preview: 0.6-0.7 m). Arm B exists for that.
- **Pine numbers on birch.** Birch is less shade-tolerant, so its real modifier may be steeper.
- **Diameters may not spread** while crowns share one cap. Then DBH spread stays near 0.14 and only height improves.
- **Stems/ha will shift.** Self-thinning counts diameters, and 74 % of deaths are that rule (22,969 of 31,052).
- **Pay-first may never bind.** No living tree had stopped laying wood at any listed age (`stopped_share` 0.000).
- **The modifier is a regression, not a mechanism.** It ties height to the tree's own stem, which its own leaves paid for. A direct light rule needs each tree's leader light, which was never saved. This run saves it.
- **Size is still partly drawn,** through carbon. Arm D shows how much.

## 8. Owner decisions

1. Use Scots pine's published numbers for birch until the birch ones are read, or wait?
2. May I open the 16.5 MB PDF of Hynynen et al. 2002 at Luke's Jukuri? It is a download.
3. Keep the draw in carbon at 0.06 (my advice), or drop it if arm D spreads without it?
4. Is "no more than 0.3 m under today's top height" the right meaning of "the dominants stay on the curve"?
5. Out of scope, not touched: `labels.yaml` gives `plot.height_follows_dominants` as false; the species file has true.

## 9. What I checked

- **CONFIRMED in code:** every file:line in sections 1 and 4.
- **CONFIRMED in saved runs:** every number in section 2. From the 20 saved stand trees: the leader's light is 0.99 at 50 and 0.97 at 60, its cost 0.008 % and 0.007 % of the pool, and the curve held it in 1,020 of 1,020 seed-years from 10 to 60.
- **CONFIRMED at source today:** Elfving 2010, Fahlvik 2014, Hynynen 1995, Hagemeier 2019a's methods. Gailis 2020 only through a summarising fetch.
- **SUSPECTED:** everything in "what to expect" and section 7. The preview is arithmetic.
- **UNVERIFIED:** Hynynen 2002's birch values; the three competition papers; Mäkelä 1986.
- **Downloads and browser.** The fetch tool saved three open PDFs (Elfving 1.9 MB from SLU; Fahlvik 1.6 MB and Hynynen 1995 7.9 MB from Silva Fennica) in the session's tool folder. I read them from my scratchpad; nothing went into the repository. Chrome opened two pages, Jukuri's record and MDPI's article; both tabs are closed, and no form, banner or login was touched.
