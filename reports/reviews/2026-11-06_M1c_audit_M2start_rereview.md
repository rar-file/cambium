Fresh reviewer's re-review, saved as it stands.

# Re-review: fixes after the M1c, audit and M2-start review

**Bottom line**
- **Numbers hold:** controls, plot verdicts, alpha and diagnosis tables all recompute. "None of the alphas run fits" stands.
- **Readings don't all hold:** apical "LAI level" is a stem-density effect; the lag test is overstated and doesn't single out the lag; "bud density doesn't move the pattern" fails the 2 SE rule.
- **FIX 3 is still open,** so `fccd283`'s "fix list closed" claims too much.

Read-only scripts on saved files; tools rerun to the scratchpad. No growth, SSH or repo edits (`tools/m3_wood.py`, untracked, isn't mine). Node not seen live.

## The seven claims

| Claim | Result | Evidence |
|---|---|---|
| 1 Controls | OK | 55,544 values, 0 differences, 20 seeds. 6.0: 240 of 240, only 4 fields at 30, 50, 60 |
| 2 Plots, row 52 | OK | Rule `48159fd`, 09:54:22, unchanged since. Plots still held memory at 09:55 (`usage.log`); fetched 09:59, 10:00. Verdicts follow |
| 3 None fits | OK | All 11 tree alphas fail at 50 or 60; plots 3.5, 4.0, 4.8 fail; 3.0, 4.4 not back |
| 4 Diagnosis table | OK | Numbers and bold agree; rerun has no diff. Reading: N1 |
| 5 Wood shade | OK, small FIX | K is transmitted PAR against litter LAI (reading:25-26), so "may be" is fair. "Already holds" is inference via a summarising fetch; species:356-359 is a VERIFY calling it open, and the daily quotes only :351-354 |
| 6 Lag | FIX | N2 |
| 7 Bud density | FIX | N3 |

## Checklist

| Point | Verdict | Evidence |
|---|---|---|
| 1 As approved | FIX | Row 52's height at 20-40 missing (N6) |
| 2 Noise | FIX | Mechanism on one seed (N2); noise unreported (N4) |
| 3 Linked | FIX | Apical LAI tied to height through stems/ha (N1) |
| 4 Wrong knob | ASK MAINTAINER | Q16 stays, corrected for N1 |
| 5 Like for like | FIX | Node -0.73 beside PC -0.79 (N3); no plot control (N6). `pc_off_check` OK: seeds 1-3, 0 differences |
| 6 Idle | OK | `pc_nowood` running 11:11, queue behind; node queues chained |
| 7 Shared machines | OK to 10:02 | Lowest 56.3 GB free, 26 GB disk; reserve 9 implies limit 14; `--no-saves`. Later queues: scripts only |
| 8 Sources | OK | 0.15 and both switches labelled unsourced; nothing adopted |
| 9 Claims | FIX | N1-N5. No restricted words |
| 10 Guesses | FIX | "points to" (`daily:14`, `:27`), "Mechanism" (`:147`) |

## Earlier FIX items

| FIX | State |
|---|---|
| 1 | Closed; consequence unreported (N4) |
| 2 | Closed, now stale: row 51 ("8 values", "3.5-4.4"), `CAMPAIGN.md:53` ("queued") |
| 3 | **Open:** apical run can't separate light from sharing; no file:line (`PROTOCOL.md:82`); cap's young ages unreported (N5) |
| 4 | Closed; N6 |
| 5 | Closed; where the step falls unstated (N4) |
| 6 | Closed |
| 7 | Closed; saved `m2_alpha_table.txt`, `m2_shape.txt` lack 4.6, 5.0 |
| 8 | Closed; draft:35 conflicts with row 52 (N6) |
| 9 | Closed: audit regenerates byte for byte; counts recount. `CAMPAIGN.md:202` keeps "none has a page" |
| 10 | Closed for the plots |

## New, by importance

**N1. Apical "LAI level" isn't like for like (`daily:137`, Q16).** LAI over leaf area gives 1,040 and 1,000 stems/ha at 50, 60, against 450. The tree's leaf area falls 39.4 and 41.9 m2 (-57 %, -58 %). Add leaf area to the table, correct Q16, and run a step small enough to stay at 450/ha. Only that can separate light from sharing.

**N2. The lag (`daily:146-148`, Q16).** The code description is right (species:410, 413; `growth.py:239-242`, `:1551-1556`, `:1566-1571`). The claims aren't:

| Ages 5-19, 20 seeds | Lag-1 | Under 2 cm | Mean yearly swing (m) |
|---|---|---|---|
| PC `pc_base` | -0.70 | 26 % | 0.90 |
| PC `pc_payahead` | -0.45 | 2 % | 0.57 |
| Node `base_trees` | -0.73 | 26 % | 0.92 |
| Node `m2_diag_maxshoot` | -0.28 | 3 % | 0.36 |
| Node `m2_diag_apical` | +0.73 | 0 % | 0.05 |

- Pay-ahead damps the flips; 19 of 20 seeds stay negative. The daily omits this lag-1, though it gives density's. "All but removes" holds only for years under 2 cm.
- The cap and apical control stop it too, unreported, so the test doesn't single out the lag. They may act through the same jump; untested.
- "All seeds and every alpha": the sign holds, 20 of 20 at all 11 alphas (my arithmetic). -0.73 is 4.8's; the range is -0.49 to -0.88, so `a7e4c06`'s "about -0.7" is wrong.
- One seed: of seed 1's 5 off years, only 2 have rings over half the pool. Years 13 and 25 flush 37 and 31 m, with over 99 % of tips growing (`cycle_s1.json`). Across 20 seeds, 83 % of 78 off years lose internodes, so it fits most (my arithmetic). Call it a hypothesis until `m3_leaves_flat` reports.
- Unreported, paired, at 50 and 60: DBH +1.8, +2.7 cm. Share inside the band at 30-60: 55, 65, 100, 90 %. Age 20 stays over (14.25 against 13.61).

**N3. Bud density (`daily:149`, `fccd283`).** Paired with `pc_base`: lag-1 -0.089 +- 0.030 (3.0 SE), stronger; under 2 cm -3.7 +- 1.9 points. The report's -0.79 sits beside the node's -0.73; its own baseline, -0.70, is missing.

The test can't reject the hypothesis, and the report doesn't say so:
- One pair of bounds, crown-layer densities applied to 0.5 m cells.
- The grid holds this year's leaves, before shoots grow (`m3-explore` `growth.py:1095`). A node in an empty cell keeps its bud (`:261`). So flush nodes, which make next year's jump, are barely limited.
- Eq. 11 has fN and a cone (`research_notes.md`); this has neither, so "form" overstates it.
- Buds removed weren't counted. It isn't inert: internodes +4,880 +- 912 at 30, +2,443 +- 598 at 60; mean height inside the band at 30-60 (24.92 at 50, 26.58 at 60). The daily credits that only to pay-ahead.

**N4. Noise isn't in the daily.** 4.79 and 4.81 sit together, off the baseline: LAI at 50 3.21, 3.21 against 3.09; height at 60 26.82, 26.87 against 27.07. Within 2 SE, but 4.79's 25.08 at 50 passes where the baseline fails. Step 4.8 to 5.0 (2.3, 2.2 SE) is 1.8, 2.6 against the three-run mean. 6.0 at 30 stays unexplained: height -0.97 +- 0.17 from 5.8, +1.54 +- 0.21 to 6.8. With identical controls that's the model; the earlier review said it matters for the gate.

**N5. Status lines.** `daily:27` drops sharing and contradicts Q16's "not settled". `daily:141` "lower alphas with it off": `pc_m3c.sh` runs wood-off alone only at 4.8; 4.4 also has the unsourced switch on. "Reaches 3.69, 3.79" omits height, over by 0.38, 0.55. The cap row shows only age 60; its answer is -1.26 at 5, -0.68 at 10; alpha moves those ages too.

**N6. Plots.** Row 52 promised height at 20-40 (all FAIL at 3.5, 4.0). Draft:35 still gives plots Baltic only. No plot `--set` control, though `base_plots` is other code and the shade plots pair with it. Add 5 plots at 4.8.

**N7. Records.** Stale: `daily:156-158`, `CAMPAIGN.md:29`, `:37-39`, `:76`. Not in DECISIONS: `m2_shade15_*` trees, `pc_m3c.sh`, `pc_wood.sh`. Fine roots: "doesn't make a ladder" holds only for the range tried.

**N8. A lead, read, not run.** `_leaf_costs` waives next spring's build for fresh laterals (`growth.py:1275-1277`), but `:1551-1552` charged one late leaf per node and `early` once per shoot. So laterals' 2.5 leaves seem never paid. Seed 1, year 13: build 742 against 1,904 if all were charged (`base_trees`; my arithmetic; tips are part of the gap). It bears on Q16's "carbon isn't short".

**Scripts:** `rr1.py` to `rr8.py` in the session's scratchpad.
