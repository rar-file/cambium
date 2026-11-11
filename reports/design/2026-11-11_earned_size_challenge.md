# Challenge: earned height and size inside a forest

2026-11-11. Challenger: Opus 5.5 (ID `claude-opus-5-5`). Design challenged: `reports/design/2026-11-11_earned_size.md` (Fable 5.2).

Read only. No model runs, no tests, no git. Small Python reads of the saved plots (`node_cd2_C`, `node_cd2_C2`) with the project's venv. Scripts are in my scratchpad, not the repository.

**Verdict: sound_with_changes.** The diagnosis holds: I reproduced it. The proposal leans on a Scots pine regression well outside its data, has a jump at breast height, defines IH one way and tabulates it another, and is expected by its own preview to break the owner's top-height rule. Fix those before anyone writes code.

## 1. What I confirmed

| Claim | How | Result |
|---|---|---|
| Height rule: curve step × light × water × alpha ÷ reference_alpha, running total, clip to 1.25 steps | Read `growth.py:2521-2531` | CONFIRMED |
| Leader paid before the solve; cut only if it costs more than the pool | `growth.py:1860-1861`, `1909-1931` | CONFIRMED. `c0 = parts(0.0)` includes the leader and the frame limbs |
| Draw exp(N(0, 0.06)) multiplies alpha; alpha multiplies carbon | `plot.py:131-132`, `growth.py:907` | CONFIRMED |
| Reference = 4.8 × mean draw of the 100 thickest/ha, set before the trees grow | `plot.py:214-228`, `388-389` | CONFIRMED |
| Draws can be rebuilt from the seed | Redrew all 20 plots in `plot.py`'s order | CONFIRMED: positions within 0.0005 m and every tree's age matches |
| Height = the rule to 0.01 m at 30 | Summed curve steps × draw ÷ that year's saved `dominant_vigour` | CONFIRMED: RMS misfit 0.008 / 0.364 / 0.279 / 0.106 m at 30 / 45 / 50 / 60 (design 0.01 / 0.35 / 0.27 / 0.10) |
| DBH spread 0.13 / 0.14 / 0.15 / 0.15; height SD 0.85 / 1.04 / 1.06 / 1.09 m; 10th-90th 2.17 / 2.58 / 2.62 / 2.73 m | Recomputed | CONFIRMED (0.128 / 0.142 / 0.147 / 0.146; 0.85 / 1.03 / 1.06 / 1.08; same ranges) |
| R² of height on draw + germination year 1.00 / 0.89 / 0.92 / 0.99 | Recomputed (log draw, germination year) | CONFIRMED (1.00 / 0.89 / 0.92 / 0.99) |
| Survival by draw quarter to 45 / 50 / 60 | Recomputed over all 32,000 trees | CONFIRMED: lowest 0.96 / 0.65 / 0.29 %, highest 10.55 / 8.89 / 7.03 % |
| Dominants' mean draw 1.13 / 1.12 / 1.12 | Recomputed | CONFIRMED |
| `node_cd2_C` gives the fresh run's numbers | Plot 1 stats against `node_f5_plots` at 30-60 | CONFIRMED for plot 1: identical stems, LAI, light, top height, DBH SD |
| Hynynen 1995 eq. 5 and Table 6 | Opened the publisher's PDF (silvafennica.fi/pdf/5559) and read the scanned pages | CONFIRMED: p. 235, i_h5 = IH_dom·(d/D_dom)^(a1·IH_dom + a2·(d/D_dom)^a3), a1 0.2445, a2 −0.4710, a3 0.8045; D_dom = mean of the 100 thickest/ha; Fig. 5 spans d/D_dom 0.4-1.1 and IH_dom 0.6-3.6 m |

Light never slowed a survivor: also supported. At 45, 234 of 1,692 trees miss the rule by more than 0.1 m, and 231 of them are taller than it, none much shorter (5th percentile residual 0.0 m). 154 of the 234 had a snow event. The design's guess (damage and catch-up) can't be the whole story: catch-up can't lift a tree past its own running total (`growth.py:2530`). SUSPECTED: bent stems straightening. Out of scope; it doesn't change the diagnosis.

## 2. Sources

| Source | Status | Comment |
|---|---|---|
| Hynynen 1995 | Opened by me, pp. 228-229, 234-235 | **Scots pine.** Table 1 and section 2.1: 11 stands, **ages 29-56** at the start, mean height 10.0-15.2 m, **thinned to about 2,355/ha as seedlings**, studied for 15 years. Sample trees were picked with **probability proportional to diameter** ("Two thirds of the sample trees were thicker than the stand's average diameter", p. 229). Suppressed trees are under-sampled. The model is "Sourced, for Scots pine" only, as the design says. For birch it is a borrowed value and should be labelled that way, not as sourced |
| Hynynen et al. 2002 (MELA birch) | UNVERIFIED | Correctly marked. It's the birch source that matters |
| Elfving 2010, Fahlvik 2014 | Not re-opened by me | The curve values match `species/betula_pendula.yaml:839-841` |
| Hagemeier & Leuschner 2019a Table 3 | Not re-opened by me | That ± is an SD is SUSPECTED, as the design says. Heights off a height-on-diameter curve make the 3 m partly a function of DBH spread |
| Gailis 2020 | Read only through a fetch tool's summary | Weaker than "opened". Mark it so |
| Weiner 1990, Schwinning & Weiner 1998, Pretzsch & Biber 2010, Mäkelä 1986 | UNVERIFIED | No numbers depend on them. OK |

## 3. Problems

**P1. Most of the effect comes from outside the source's data (major).** The only guards are d/D_dom 0.4-1.1 and IH 0.6-3.6. Age, height and density are unguarded. The data start at stand age 29 and mean height 10 m, in stands pre-thinned to about 2,355/ha. The design applies the modifier as soon as a tree has a DBH, in a natural start at 16,000/ha. At 11, 44 % of living trees have d/D_dom under 0.4 (8.6 % at 15), so the clamp sets their status, not the equation. Inside the data's range, the modifier is 0.89-1.06 for d/D_dom ≥ 0.6 (my table below). The preview's biggest separation (height SD 1.41 m at 30) is built in the extrapolated years 11-29. Nothing in the test plan tells in-range effect from extrapolation.

**P2. Jump at breast height (major).** "A tree with no DBH yet has status 1." The year a small tree passes 1.3 m, its status falls from 1 to about 0.56 (IH ≈ 3.5, clamped d/D_dom 0.4). Until then, a late or suppressed seedling gets the dominants' full step. That rewards being short.

**P3. IH defined one way, tabulated another (major for the unit tests).** The text says IH = 5 × the curve's step this year. Hynynen defines IH_dom as the "Five-year increment in dominant height" over the growth period (p. 235). The design's table is reproduced by the forward 5-year increment, curve(A+5) − curve(A), at 15-50; its age-60 row matches the backward one. With the text's definition I get these values:

| d/D_dom | 15 | 30 | 45 | 50 | 60 |
|---|---|---|---|---|---|
| 0.4 | 0.557 | 0.750 | 0.925 | 0.967 | 1.033 |
| 0.6 | 0.755 | 0.891 | 1.001 | 1.026 | 1.064 |
| 0.8 | 0.901 | 0.968 | 1.019 | 1.030 | 1.046 |
| 1.1 | 1.034 | 1.003 | 0.981 | 0.977 | 0.970 |

The design's table gives 0.59 and 0.79 at 0.4. The planned unit test "the modifier's table values" would lock in one of two numbers. It's also not stated whether IH and the curve step use the stand's age or the tree's own age, which differs by 0-3 years.

**P4. Wrong direction at the ages that are scored (major).** From about 45 the exponent turns negative for d/D_dom 0.5-0.9. Small trees then outgrow the dominants: 1.03 at 50 and 1.06 at 60 for d/D_dom 0.6. The targets are at 45 and 67, and the design's own preview has height SD falling 1.41 → 1.16 m from 30 to 60. That may be true of pine thinned from below. For a light-demanding birch it is SUSPECTED wrong, and it works against the 3 m target. The design lists it as a risk, but its decision rule adopts A without looking at spread.

**P5. A is expected to break the owner's fixed rule (major).** The preview puts the 100 thickest 0.6-0.7 m lower at 45-60. The must-not-break allows 0.3 m. So A is expected to fail, and B is really the proposal. B is under-specified:
- which top height it steers to (the approved Näslund one, or the plot's 100-thickest mean, which differ by 0.1-0.3 m);
- whether every tree gets the plot's step or its own-age step;
- B is planned for seeds 1-5 only, while adoption needs 20.

B also passes top height by construction, so in B that row stops being a check. The 0.3 m tolerance itself is a new number with no source; the design asks the owner about it (its Q4), and that question must be answered before any run.

**P6. "Earned" isn't measured (moderate).** Status is a function of DBH, and DBH is still R² 0.84 draw plus germination year (design figure; I did not recompute it). A carries the draw into height through the stem. Height SD can grow while height stays drawn. Arm D (no draw) is the only arm that measures what is earned, and it isn't in the decision rule.

**P7. The decision rule can adopt a change that makes things worse (moderate).** "The spread isn't used to pick an arm." So A can be adopted if it narrows height SD at 50-60, or moves DBH spread away from 0.32. A do-no-harm check is not loosening a target, and choosing by real numbers needs it.

**P8. Change 2 probably never acts (minor).** `stopped_share` is 0.000 at every listed age, and the leader costs 0.008 % of the pool. "Adopt G if harmless" would add code nobody has seen act. It also doesn't say what happens to the frame limbs, which sit inside `c0` (`growth.py:1856-1859`, `1909`).

**P9. Implementation trap (minor).** All plot trees share one `height_driver` object (`plot.py:126`, `210-211`). A per-tree status can't live there; it must sit on each `GrowthModel`, or every tree gets the last tree's status.

**P10. Simpler explanations not ruled out (moderate, SUSPECTED).** Two things already in the code may cause most of the evenness:
- Light per unit of leaf is the same for all trees (0.94-1.05 of the dominants'), and `light_full` 0.6 is TUNED "so a stand tree's leader isn't limited". The existing light rule may never bind, by tuning rather than by biology.
- Every tree shares one cap on limb reach (`plot.py:401`).

The design saves leader light in the new run, which is right, but it proposes the regression before seeing it. An arm with leader light saved and no other change (arm N already does this) should be read first.

## 4. Changes required before implementation

1. **Fix IH.** One definition, the forward five-year increment of the curve at the stand's (dominants') age, as in Hynynen eq. 5. Say which age the yearly curve step uses. Regenerate the table, and write the unit test from it.
2. **Bound the use to the source's range or label it.** Either apply status only once the stand is inside Hynynen's data (dominant height ≥ 10 m or stand age ≥ 29), with status 1 before, or keep the early use and label it "borrowed from Scots pine, extrapolated outside the data (ages 29-56, pre-thinned to 2,355/ha)". The second is a guess and cannot be called sourced. Add an arm "A, in range only" so the two can be told apart.
3. **Remove the jump at breast height.** For a tree without a DBH, use the status at the clamped minimum, or a height-based ratio. Never 1.
4. **Make B a complete arm.** Name its top-height measure (the approved Näslund one). Say whether it changes each tree's own-age step or replaces it. Run it on 20 seeds if it might be adopted. Keep a check it can't pass by construction: the dominants' own steps, and the Näslund top height against the plot's 100-thickest mean.
5. **Get the owner's answer on the 0.3 m tolerance (design Q4) before running.** It is not a sourced number.
6. **Add do-no-harm to the decision rule.** Adopt nothing that makes height SD, its 10th-90th range or DBH spread worse at 45, 50 or 60 beyond 2 standard errors (paired, against control). This picks nothing by taste and loosens no target.
7. **Report what is earned.** For A and D, give the share of height and DBH variance explained by draw plus germination year at 30, 45, 50 and 60, and run D on the same seeds as A.
8. **Adopt G only if it acts.** Report how many tree-years it bound, and drop it if none. State how the frame limbs are cut.
9. **Store status per tree,** not on the shared `height_driver` (`plot.py:126`, `210-211`).
10. **Label borrowed values.** In section 5 and `labels.yaml`, mark a1-a3 as "borrowed: Scots pine (Hynynen 1995 Table 6), not birch". Mark the clamp limits as "read off Fig. 5 by eye". Keep both VERIFY until Hynynen 2002's birch values are read.
11. **Read leader light first.** Read arm N's saved leader light before running A. If the leader-light rule never binds because of the tuned 0.6, write that in the report as a cause beside the draw.

## 5. What I did not check

- DBH R² 0.84 / 0.82 / 0.84 / 0.85, crown width spread, rank tables: I did not recompute them.
- The arithmetic preview (height SD 1.41 / 1.26 / 1.23 / 1.16 m).
- The stand-tree numbers (leader cost 0.008 %, 1,020 of 1,020 seed-years).
- Hagemeier, Elfving, Fahlvik and Gailis: not re-opened by me.
- Whether Hynynen 2002 holds birch values of this form: UNVERIFIED.
