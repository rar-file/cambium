# Branch wood against Repola: design

2026-11-11. Track: branch wood 26-33 % over Repola. Written by Claude Opus 5.5 (claude-opus-5-5). This is a design only: no model runs, no tests and no code changes. CONFIRMED means I checked it in code, saved data or the publisher's PDF. SUSPECTED means I have not.

## In short

1. **The row is not an untuned test.** `pipe_model.branch_sapwood_senescence: 0.30` is labelled "TUNED, against Repola's branch wood" (species/betula_pendula.yaml:652-654 and :1701). `tools/independent_checks.py:77-78` and the review call the row independent. CONFIRMED. The row should be relabelled "tuned against".
2. **The comparison uses the less suitable Repola equation.** It uses Eq. 9 (DBH and height only). Repola himself recommends Eq. A3, which adds crown length, for crown parts (p. 618). The model's crowns at 50-60 are shorter than his sample's mean (stand trees 0.52 / 0.46, plots 0.47 / 0.42, against his 0.58). So Eq. 9 gives these trees too much branch wood, and the gap is bigger than reported: **1.47 at 50 and 1.76 at 60** against A3, not 1.23 / 1.29. Bark makes it larger still. CONFIRMED.
3. **The gap is real.** Total stem plus branch wood is right at 50 (1.00) and 8 % high at 60. What is wrong is the split: branches take 21 % of the wood against A3's 13-15 %. Each year branch rings take 38-41 % of the shoot carbon at 50-60, against 54-56 % for stem rings. CONFIRMED from the run logs.
4. **The cause is one tuned rate.** Each year 30 % of every limb's conducting sapwood must be replaced by a new ring (`growth.py:2457-2469`, used at :1773, ring = Huber value x leaf area beyond - kept sapwood at `fast.py:220-222`). The ring is paid from the tree's shared pool, not from the limb's own carbon. So a limb's wood grows with its age even when its leaf area doesn't: branch wood per m2 of leaf goes 0.25, 0.61, 0.87 kg at 30, 50, 60. CONFIRMED.
5. **The fix.** Restate the row first (A3, relabelled). Then compare on the server a retune of the 0.30 (TUNED, against A3 at 50 and 60) with a number-free rule: a limb's rings come out of its own carbon (branch autonomy, already in the code for shedding). Mechanics shouldn't stop it: the bending-stress floor added 0.00-0.02 kg of wood in 60 years, so limbs sit far above what their load needs.

## 1. Is the comparison fair?

| Check | What the code does | Repola 2008 (publisher PDF, silvafennica.fi/pdf/236) | Verdict |
|---|---|---|---|
| Equation | Eq. 9: ln y = -4.152 + 15.874 dS/(dS+16) - 4.407 h/(h+10), bias exp((0.02733+0.07662)/2) (`tools/m3_wood.py:36-40`) | Table 4 p. 613: same coefficients and variances | Coded right, CONFIRMED |
| Better equation | not used | A3 adds living crown length: b0 -5.067, b1 14.614 on dS/(dS+12), b2 -5.074 on h/(h+12), b3 0.092 per m of crown; u 0.01508, e 0.05663 (Table A1 p. 623). "most applicable and stable" for crown parts (p. 618) | Use A3 as the main row |
| dS | 2 + 1.25 d | p. 611; checked against his Table 8 (round41 pack) | Right |
| DBH | model wood DBH, then over bark (tools/bark.py) | Field DBH, over bark | Right |
| What "branches" holds | every living non-stem internode: limbs, forks, twigs, short shoots; dead ones left out (`tools/tree_table.py:63-67,104`) | Living branches, foliage weighed apart, dead branches apart: "The branch biomass included both branch wood and bark" (p. 608) | Same parts except bark |
| Bark | none in the model | included | Reference too high for wood only. No birch branch-bark share opened: UNVERIFIED |
| Density | branches at 530 kg/m3, the stem's basic density (Aosaar 2016) | branches dried and weighed (p. 608) | No birch branch density opened: UNVERIFIED, direction unknown |
| Stem and branch split | stem = leader chain; it reaches the tree top in 60 of 60 tree-ages checked | stem to the top; forks count as branches | Fair, CONFIRMED |
| Range | stand trees DBH ob 15.7 / 28.0 / 31.3 cm, H 15.8 / 21.9 / 23.7 m, crown ratio 0.72 / 0.52 / 0.46 at 30 / 50 / 60 | Table 2 p. 608: DBH 2.5-38.0, H 3.9-29.0, crown ratio 0.29-0.96 | Stand trees are inside. In plots at 60, 23 tree-measures are outside (DBH over 38 cm, up to 44.0) |
| Origin | Swedish site curve | Finnish, about a third of the trees B. pubescens. Marklund 1988 (Sweden) gives the lowest living branches of the functions compared (p. 615, Fig. 3) | A Swedish reference would make the gap bigger, not smaller |

**Honest answer.** The comparison wasn't unfair to the model. If anything it was kind: it used Eq. 9, and a wood-only model was held against wood plus bark. The restatement makes the gap bigger.

## 2. Recomputed from the saved runs

Stand trees, `node_f5_trees`, 20 seeds. Means, kg dry mass. Ratios are geometric means over trees. Model DBH is converted to over bark with the Hansen bark equation, as in the tools.

| Age | Branch wood | Eq. 9 | A3 at own crown length | Model / Eq. 9 | Model / A3 | Trees over A3 +1 SD | Stem / Eq. 7 | Stem+branch / Repola | Branch share: model, A3 |
|---|---|---|---|---|---|---|---|---|---|
| 30 | 14.1 | 10.5 | 12.8 | 1.37 | 1.12 | 3 of 20 | 0.75 | 0.84 | 0.23, 0.17 |
| 50 | 64.4 | 53.2 | 43.8 | 1.23 | **1.47** | 17 of 20 | 0.96 | 1.00 | 0.21, 0.15 |
| 60 | 88.9 | 69.9 | 50.6 | 1.29 | **1.76** | 20 of 20 | 1.03 | 1.08 | 0.21, 0.13 |

- The fresh-run report gives arithmetic means: 1.41 / 1.26 / 1.33.
- **How sure is the gap?** I treat the 20 trees as one stand and use Repola's own variances (my arithmetic). Two standard errors are x/÷ 1.42 for Eq. 9 and x/÷ 1.31 for A3. So Eq. 9's 1.23 / 1.29 fall inside the scatter, as the v1 report said. A3's 1.47 / 1.76 fall outside it.
- Crown base: the model's two crown-base measures agree within 0.2 m at 50-60 (10.50 against 10.33 m at 50), so A3 doesn't depend on which one is used.

Plots, `node_f5_plots`, 20 plots. Their tree lists save no wood (`tools/tree_list.py:41,62`), so model branch wood can't be recomputed for plots. CONFIRMED. Only Repola's side can be computed:

| Age | Stems/ha | Crown ratio (range) | Repola Eq. 9, t/ha | Repola A3, t/ha |
|---|---|---|---|---|
| 30 | 2,640 | 0.60 (0.44-0.77) | 7.6 | 8.7 |
| 50 | 667 | 0.47 (0.33-0.74) | 22.9 | 18.0 |
| 60 | 474 | 0.42 (0.31-0.61) | 29.2 | 19.5 |

Plots before crown fix C (`node_cd2_C`, 18 plots) give the same Repola figures to within 0.1 t/ha. The v1 report already had branches 29 % and 23 % over at 50 and 60, so crown fix C didn't cause the gap.

## 3. Where the extra wood comes from

How a limb gets its radius (lignum mode, the default, `species/betula_pendula.yaml:641`):
- Each year every living internode needs sapwood = Huber value (1.24e-4 m2 per m2 of leaf, yaml:1367, from current-year shoots) x the leaf area beyond it.
- The ring it lays is that need minus the sapwood kept from last year (`fast.py:220-222`).
- The kept sapwood is (1 - loss) x last year's. The loss is 0.014 on the stem and **0.30 on side axes**, scaled down by 0.02 m / radius on limbs thicker than 2 cm (`growth.py:2457-2469`; yaml:651-656).
- Wood never goes away while the internode lives (`growth.py:2868-2869`). So a limb whose leaf area stays level still adds about 0.3 x Huber value x leaf area every year, and its wood grows with its age.
- At stem-theory stage 2, Huber value doesn't rise with radius or path (`growth.py:1724-1726`).
- Below the crown base, surplus sapwood is retired (`growth.py:1743-1770`). That trims sapwood, not wood.

Evidence that this rate sets the level:

| Evidence | Source | Status |
|---|---|---|
| Branch wood at 50 was 15.3, 24.6, 33.5 and 50.1 kg at rates 0, 0.1, 0.2 and 0.4 (an older setup, 8 PC seeds) | reports/tree_handover.md:104 | recorded, not rerun |
| It was tuned in test A to 38.5 / 52.6 kg against Eq. 9's 46 / 59 at 50 / 60. The crown changes since (frame "earned", crown fix C) were never retuned | yaml:653; tree_handover.md:172 | CONFIRMED |
| Branch rings take 14, 23, 32, 38, 41 % of the shoot pool at 20, 30, 40, 50, 60 (stem rings 25, 51, 53, 56, 54 %) | `driver.use` in node_f5_trees tree.json | CONFIRMED |
| Branch wood per m2 of leaf: 0.25, 0.61, 0.87 kg at 30, 50, 60; leaf area flat at about 105 m2 | snapshots and stats | CONFIRMED |
| The bending-stress floor isn't what thickens limbs: 0.00 kg mean (0.02 max) of uncharged floor wood over 60 years | `driver.wood_free_m3` summed | CONFIRMED |
| The wind envelope runs on every living node, limbs too (`fast.py:235-252`). How much limb wood it adds isn't logged | code | SUSPECTED: a share of the excess |
| Limb number and length aren't the cause: 51 limbs over an 11.4 m crown at 50 is 4.5 per 10 % of crown (Lintunen 5.2); mean limb 2.1 m | snapshots | CONFIRMED |

**Split by order or by height.** The saved runs can't do it: they keep the total, the ten thickest limb diameters, the median diameter and limb lengths only. CONFIRMED. A rough estimate treats each limb as a paraboloid (my sum, SUSPECTED). On it, the main axes of first-order limbs hold about 60 % of branch wood at 30 and 70-80 % at 50-60, with the rest in forks and finer wood. That suggests the excess sits in old, long-lived limbs: the age-driven ring above. The test plan adds the real split.

The largest limb's diameter is only 0.27-0.29 of the stem's, against 0.67 (90th percentile) in the 6 Nordic scans recorded in KNOWN_ISSUES.md (lines 1203-1214, an older model phase). So the model has too much wood spread along modest limbs, not too many thick limbs.

## 4. Published measurements

| Claim | Source | Status |
|---|---|---|
| Living branches include bark; branches dried and weighed by four equal crown sections | Repola 2008, p. 608 | CONFIRMED, publisher PDF |
| Sample range DBH 2.5-38.0 cm, H 3.9-29.0 m, crown ratio 0.58 ± 0.14 (0.29-0.96) | Repola 2008, Table 2 p. 608 | CONFIRMED |
| A3 and A6 recommended for crown parts; crown length cuts between-stand variance 44 % | Repola 2008, pp. 612, 618 | CONFIRMED |
| Marklund 1988 gives the lowest living-branch mass of the functions compared | Repola 2008, p. 615 and Fig. 3 | CONFIRMED (as Repola reports it). Marklund's own report not found in SLU's repository: UNVERIFIED |
| Birch Huber value rises from the top of the crown to its base, falls with branch order, and depends on branch position and diameter | Sellin & Kupper 2006, Trees 20:311 (abstract as quoted in yaml:703-704) | Full text behind a login: numbers UNVERIFIED |
| Huber value at the base of current-year birch shoots 1.24e-4 | [OP22] Table 1, as yaml:1359-1367 | Not reopened today |
| Branch bark share, branch wood density, branch share of above-ground mass by size for birch | none opened | UNVERIFIED. Leads: Hakkila 1991, Petersson 2006 (both compared in Repola, Fig. 3), Johansson 1999 (Elsevier, not opened) |

## 5. Proposal

**Step 1: restate the row (tooling only, no growth change).**
- In `tools/independent_checks.py`, make A3 at each tree's own crown length the main branch row and keep Eq. 9 beside it.
- Set its kind to "tuned against" and add a note: "branch_sapwood_senescence 0.30 was tuned against Eq. 9 in test A".
- State plainly: "Repola's branches include bark; the model's are wood only".
- Add the A3 scatter (x/÷ 1.31 at 2 SE for a 20-tree mean).

**Step 2: candidates for the server.**
- **T (TUNED):** `branch_sapwood_senescence` 0.20, 0.15 or 0.10, keeping branch_sapwood_thick_m 0.02. Label: "TUNED, against Repola 2008 Eq. A3 (Table A1, p. 623) at the stand trees' own DBH, height and crown length, ages 50 and 60". Expected weakness (SUSPECTED): the gap grows with age (1.12, 1.47, 1.76), so one constant rate that fits 60 may leave 30 under.
- **A (number-free):** a switch, off by default. An established limb's ring is paid only from its own carbon net of upkeep, the same per-limb sums already used for shedding (`growth.py:1099-1120`, Sprugel, Hinckley & Schaap 1991 as cited there). The ring is cut back evenly along the limb when its own carbon falls short. Rate stays 0.30. Shaded, old, low limbs then stop thickening, which goes at the age trend.
- **A+T:** if A alone is still over, A with the best T.
- Neither arm adds a sourced number. T is plainly TUNED. A swaps a tuned level for a rule with a published basis; it still keeps the 0.30.

**What stays an independent test after adoption.**
- Branch wood at 30 and 40 against A3: tuning is at 50 and 60 only.
- Plot trees' branch wood against A3: tuning is on stand trees only. Partly independent.
- Limb counts over 2 cm and branch wood ≥ 1 cm against the Nordic scans (KNOWN_ISSUES.md:1203-1211).
- Limb length against Lintunen. His count is an input (crown_frame.limbs_per_10pct_crown), so it isn't a test.
- Marklund 1988, once opened at SLU.
- The A3 row itself becomes "tuned against" and is never called independent again.

## 6. Server test plan

**Tooling first (no growth change).** The control arm must reproduce node_f5_trees and node_f5_plots bit for bit (golden check, 0 differences).
1. `tools/tree_table.py` snapshot: branch wood by order (1, 2, 3+), by crown quarter (Repola's four equal sections), and by limb age (under 10, 10-20, over 20 years); wood in parts ≥ 1 cm; count of limbs over 2 cm; branch / A3 and branch / Eq. 9.
2. The run log: ring carbon split into stem and branch, and on branches into sapwood replacement, new leaf area and wind extra.
3. `tools/tree_list.py`: add stem_kg and branch_kg per tree, so plots can be compared.

**Stage 1, stand trees.** Paired seeds 1-20, to 60, snapshots every 5 years.
- Arms: C (control), D0 (diagnostic: rate null, the pipe model alone), T20, T15, T10, and A (built behind its switch).
- D0 and a wind-off-on-limbs diagnostic only explain; neither can be adopted.

**Stage 2, plots.** Seeds 1-20 of node_f5_plots, 1000 m2, to 60, tree lists at 30, 45, 50, 60.
- Arms: C and at most the two best from stage 1.

**Read at 30, 50 and 60, paired by seed (mean difference ± SE):**

| Measure | C at 50 / 60 | Rule |
|---|---|---|
| Stand branch / A3 (geometric mean) | 1.47 / 1.76 | Pick: smallest mean of absolute log-ratios at 50 and 60, inside x/÷ 1.31 |
| Stand branch / A3 at 30 | 1.12 | Reported, not tuned against |
| Plot branch / A3 | not saved yet | Reported; must move the same way as on stand trees |
| Stem wood / Eq. 7 | 0.96 / 1.03 | Must stay within 0.95-1.05. Freed carbon could go to the stem; total wood at 60 is already 1.08 |
| Top height (plots) and stand height | on the curve | Unchanged in every seed-year |
| Plot LAI | 4.51 / 4.29 | No rise beyond control + 1 paired SE; the Baltic top 4.5 is not loosened |
| Light under canopy | 18.2 / 19.5 % | Stays at or under the 19.8 top |
| Stems/ha, basal area | 667 / 474; 24.7 / 26.8 | Within control ± 1 paired SE |
| Carbon turned down (sink-limited) | about 0 % | Reported; above 5 % fails |
| Uncharged stress-floor wood | 0.00 kg | Must stay under 1 % of branch wood. If the floor starts to bind, charge it before adopting |
| Limb angles (low/mid/up), hanging p90, crown width | as C | Angles within ± 5°, hanging p90 within + 10 %, width within the current band |
| Damage-log limb and stem breakage (plots) | as C | No rise beyond paired SE |
| Fresh vs bark-free view | - | Report branch / (A3 x 0.8) as a what-if only: the 0.8 has no source |

**Choosing.** Real numbers first: all must-not-break rows pass, then the smallest A3 misfit at 50 and 60. Arms within one paired SE of each other count as tied, and the smaller change from today wins (A before T, larger rate before smaller). Then photos of limbs at 50 and 60 against real stand birch, never taste.

## 7. For the owner

1. Restate the branch row against A3 and relabel it "tuned against"? It is tuned today, and the review was wrong to call it untuned.
2. May `branch_sapwood_senescence` be retuned against A3 at 50 and 60, as TUNED, knowing the Repola row then stops being a test?
3. Should arm A (limb rings from the limb's own carbon, a code change behind an off switch) be built for the comparison?
4. Bark: keep comparing model wood with Repola's wood plus bark until a birch branch-bark share is opened? That reads the model as lighter than it is.

Sources opened today: Repola 2008, Silva Fennica 42(4):605-624, PDF from silvafennica.fi (publisher), pp. 607-615, 618, 621-623. Springer (Sellin & Kupper 2006) redirected to a login, so I stopped there. Marklund 1988 was not found in the SLU repository.
