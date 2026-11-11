Model: Fable 5.2 (claude-fable-5-2)

# Challenge to the branch wood design (2026-11-11_branch_wood.md)

Read only: no model runs, no tests, no commits. I recomputed from `node_f5_trees`, `node_f5_plots`, `node_cd2_C`, `node_cd2_base`, read the cited code, and opened Repola 2008 at the publisher (silvafennica.fi/pdf/236, pp. 607-623). CONFIRMED = I checked it in code, data or the PDF. SUSPECTED = my reasoning, not checked by a run.

## Verdict: sound with changes

- The core finding holds. Stand-tree branch wood is over Repola, more so against Eq. A3, and the row was tuned, not independent.
- Step 1 (restate and relabel the row) can go ahead once the bark error in problem 1 is fixed.
- Step 2 isn't ready. The cause isn't isolated on today's setup, the test plan leaves the freed carbon nowhere to go, and arm A probably does nothing.

## What I confirmed

| Claim | Result |
|---|---|
| Repola Eq. 9 and Eq. 7 coefficients and variances (Table 4, p. 613) | CONFIRMED, match `tools/m3_wood.py:36-40` |
| A3: -5.067, 14.614 on dS/(dS+12), -5.074 on h/(h+12), 0.092 per m of crown; variances 0.01508, 0.05663 (p. 621, Table A1 p. 623) | CONFIRMED |
| Branches include bark (p. 608); sample range (Table 2 p. 608); A3 recommended (p. 618); crown length cuts between-stand variance 44 % (p. 612); Marklund lowest (p. 615) | CONFIRMED |
| Sample fits: 24 stands, most temporary plots naturally regenerated, 34 % B. pubescens (pp. 607-608) | CONFIRMED |
| The row is tuned: yaml:652-654, :1701; `independent_checks.py:77-78` says independent | CONFIRMED |
| Two-SE bands x/÷ 1.42 (Eq. 9) and x/÷ 1.31 (A3) for 20 trees in one stand | CONFIRMED, my arithmetic gives 1.423 and 1.307 |
| Mechanism lines: `growth.py:2457-2469`, :1773, :2868-2869, `fast.py:220-222` | CONFIRMED as described |
| Branch rings 38 / 41 % and stem rings 56 / 54 % of the pool at 50 / 60 | CONFIRMED (38.2 / 41.2 and 55.7 / 54.0) |
| Stress-floor wood 0.00 kg mean, 0.02 kg max, over 60 years | CONFIRMED |
| Stem chain reaches the top | CONFIRMED to within 0.37 m (worst seed at 60) |
| Plot tree lists save no wood (`tools/tree_list.py:41,62`) | CONFIRMED |

## What I recomputed

| Measure | Age 30 | Age 50 | Age 60 | Design | Status |
|---|---|---|---|---|---|
| Stand branch wood / Eq. 9 (geometric mean, 20 trees) | 1.37 | 1.23 | 1.29 | same | CONFIRMED |
| Stand branch wood / A3 at own crown length | 1.12 | 1.47 | 1.76 | same | CONFIRMED |
| Stand branch wood / A3 at Repola's mean crown ratio 0.58 | - | 1.30 | 1.35 | not given | mine |
| Stem + branch / (Eq. 7 + A3) | 0.81 | 1.03 | 1.13 | 0.84 / 1.00 / 1.08 | design used Eq. 9 here |
| Branch wood per m² of leaf, kg | 0.25 | 0.61 | 0.87 | same | CONFIRMED |
| Plots, Repola Eq. 9, t/ha | 5.6 | 16.9 | 21.9 | 7.6 / 22.9 / 29.2 | **design wrong** |
| Plots, Repola A3, t/ha | 6.6 | 14.0 | 15.5 | 8.7 / 18.0 / 19.5 | **design wrong** |
| Plot trees outside Repola's range | 0 | 0 | 3 (DBH to 40.1 cm) | 23 measures, to 44.0 cm | **design wrong** |
| Seed-years in the decade to this age where the wind adds no ring at all | 60 of 200 | 200 of 200 | 200 of 200 | "not measured" | settled, problem 3 |
| Branch ring wood laid in the decade to this age, kg per tree | - | 67.9 | 71.8 | not given | mine |
| Net change in standing branch wood over that decade, kg | - | +19.3 | +24.5 | not given | mine |

Scripts: `<scratchpad>\chal\` (trees.py, plots.py, plots2.py, plots3.py, rings.py, cum.py, cap.py).

## Problems, most serious first

**1. The plot figures have bark added twice. CONFIRMED.**
- The plot tree lists already hold DBH over bark (`tools/tree_list.py:33,80`). Their mean DBH (21.5 / 26.6 cm) and basal area (24.7 / 26.8) match the fresh report's over-bark figures.
- Converting them to over bark again reproduces the design's numbers exactly: 22.9 / 29.2 and 18.0 / 19.5 t/ha, 23 measures outside, 44.0 cm.
- The right figures are in the table above. If the new plot row repeats this, plot branch wood will read about 1.3 times better than it is.

**2. "The cause is one tuned rate" is marked CONFIRMED but isn't. SUSPECTED at best.**
- No run on today's setup changes the rate. The only dose-response is an older setup on 8 PC seeds (`reports/tree_handover.md:104`).
- The same 0.30 gave 38.5 / 52.6 kg in test A and gives 64.4 / 88.9 kg now. Something else added 67 %, and the design doesn't say what.
- Test A had about 96 limbs at 60 (`tree_handover.md:45`). Today has 45. Wood per limb went from about 0.55 to 1.96 kg. So "limb number is ruled out" holds against Lintunen but not against the state the rate was tuned in.
- Standing branch wood is a small net of large flows. At 50-60 a tree lays 71.8 kg of branch rings and gains 24.5 kg: 66 % goes with axes that die. Which axes die matters as much as the rate.

**3. The wind question is already answered by the saved logs. CONFIRMED.**
- The ring cap only limits the wind's part (`growth.py:1891-1901`, `fast.py:253-273`). Once sapwood rings alone pass half the pool, the wind's ring is scaled to zero.
- That is so in 600 of 600 seed-years from age 31 to 60 (rings are 0.92-1.07 of the pool). Stand trees get no stem surplus either (`growth.py:2233`).
- So from 31 on, every ring on limbs and stem is the sapwood rule. That supports the design's mechanism and makes the wind-off diagnostic pointless at those ages.
- Before 31 the cap is filled by wind in 291 of 400 seed-years. A lower branch rate there frees room that the wind refills. So T may do little before 30 (SUSPECTED).
- `ring_share_max` is labelled "the most of the pool the year's rings may take". It doesn't do that.

**4. The test plan forbids every place the freed carbon can go. SUSPECTED, strongly.**
- Branch rings are 38-41 % of the pool at 50-60. Reaching A3 means about a third to two fifths less branch wood, so roughly 12-18 % of the pool is freed.
- Stand trees turn down 0 % now and can't put surplus on the stem. So the solver grows more twigs and leaf, and with them more stem ring.
- The guards are plot LAI within +1 paired SE, basal area within ±1 paired SE, and under 5 % turned down. The spacing switch, a small change, already moved basal area by 6 SE at 60 (fresh report, section 5).
- Likely outcome: no arm passes, or the guards get relaxed after the results are seen.
- Stem / Eq. 7 can't catch a fatter stem. It is read at the tree's own DBH, so it measures stem form, not size.
- Stage 1 doesn't read the approved stand-tree targets (LAI 4.73 / 4.60, light 16.6 / 17.1 at 50 / 60). An arm could break them and still be picked.

**5. Arm A probably doesn't bite, and it breaks the pipe rule. SUSPECTED.**
- At 50 the pool is 36,872 units and branch rings 13,620. The pool is already net of upkeep. So an average limb earns about 2.7 times its ring.
- The cap would bind only on limbs near the shedding line, which the same sums already remove (`growth.py:1099-1120`).
- A capped limb keeps its leaves with less sapwood than Huber value x leaf area. The design doesn't say what happens to those leaves.
- `shedding.log_limbs` (yaml:489) already logs each limb's carbon and upkeep. A can be screened from one control run before any code is written.
- Sprugel et al. 1991 was not opened. It is cited from a code comment: UNVERIFIED.

**6. The clash with the Nordic scans isn't faced.**
- The design's 0.27-0.29 is thickest limb over DBH. The scans' 0.67 is limb over stem at the attachment (`KNOWN_ISSUES.md:1201`). Not like for like. CONFIRMED.
- The scans said the model had too few limbs over 2 cm and a tenth of the branch length over 1 cm. T thins every limb, which moves both further off (SUSPECTED).
- The plan lists these as "stay as checks" with no rule and no control value.

**7. A3 folds two faults into one number.**
- At Repola's mean crown ratio the gap is 1.30 / 1.35 at 50 / 60. The rise to 1.47 / 1.76 is the model's short crowns (0.52 / 0.46).
- A tree tuned to A3 = 1.00 will read 0.84 / 0.73 against Eq. 9 at 50 / 60. The owner should see that before agreeing.
- The crown track (2026-11-11_crown_light.md, P1, P3, P4) changes crown length and limb reach. Tuning now repeats test A: tuned once, then the crown moved.

**8. Sourcing and labels.**
- 0.30 means branch sapwood conducts for about 3 years; 0.15 about 7; 0.10 about 10. The stem's is 72 rings. No source for any branch figure (yaml:653 says so).
- `branch_sapwood_thick_m` 0.02 is the other half of the same rule, TUNED, and is held fixed with no reason given. It slows thick limbs most.
- Neither value has an entry in `reference/betula_pendula/labels.yaml`. CONFIRMED by search.
- D0 (rate null) is barred from adoption with no reason. If it lands inside the band it removes a tuned value, which should beat any retune.
- T aims wood-only branches at wood plus bark. The target is a known over-read until a bark share is opened.

**9. Smaller errors.**
- "Plots before crown fix C (node_cd2_C)" is wrong. `node_cd2_C` is with fix C and equals `node_f5_plots`. Before fix C is `node_cd2_base`: Eq. 9 14.6 / 19.3 and A3 13.5 / 14.4 t/ha at 50 / 60. CONFIRMED. The v1 report line (29 % and 23 % over) still supports the claim for stand trees.
- "4.5 limbs per 10 % of crown" at 50 is per metre. Per 10 % it is 5.1 at 50 and 4.5 at 60, and 5.2 is an input, so this is by construction.
- At 60 the trees sit at the top of Repola's sample (mean DBH 31.3 cm, up to 35.7; his mean 16.5, SD 7.0, top 38.0). The pick rule weights 60 the same as 50.
- "Branch wood at 30 and 40" after a tune at 50 and 60 is the same trees, rule and equation. Call it "partly", not independent.

## Changes required before anyone implements it

1. Fix the plot arithmetic: no bark conversion on tree-list DBH. Correct the plot table, the range count and the `node_cd2_C` label.
2. Mark diagnosis 4 SUSPECTED. Drop item 6 for ages 31-60 and cite the logs.
3. Run diagnostics before choosing arms: control with `shedding.log_limbs` and the new split logs, then D0. Name candidates only after reading them.
4. Add to the tooling: branch wood shed per year, wood per limb, and leaf area per limb.
5. Say where the freed carbon is expected to go, with a rough size. Add stand-tree DBH, LAI and light at 50 and 60 to stage 1.
6. Restate the guards against published figures with a tolerance fixed now, not control ± 1 SE: basal area (Hagemeier, Q32 open), the approved LAI and light bands. Keep "no approved target gets worse".
7. Screen arm A from the limb log first. Build it only if capped limbs hold a stated share of branch ring carbon, and say what a capped limb's leaves do. Mark Sprugel UNVERIFIED until opened.
8. Let D0 be adopted if it passes. Put `branch_sapwood_thick_m` in play or justify fixing it.
9. Compute the scan measures on the control, like for like, and add "must not get worse" or state the trade for the owner.
10. Show three rows side by side at 30, 50 and 60: Eq. 9, A3 at own crown, A3 at crown ratio 0.58. State the Eq. 9 reading of any A3-tuned arm.
11. Tune last, after the crown track's changes are adopted or rejected.
12. Add both branch sapwood values to `labels.yaml` as TUNED with what they were tuned against. Correct the `ring_share_max` wording.
13. Try to open a birch branch-bark share and a branch litterfall figure at the publisher. The model sheds about 4.7 kg of branch wood per tree per year at 50-60. That is a check nobody has tuned against.
