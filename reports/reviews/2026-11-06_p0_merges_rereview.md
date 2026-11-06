The same reviewer's re-review of its FIX items and of P0's close, saved as it stands.

# Re-review: P0 merges step, the 13 FIX items and P0's close

**Basis:** master at `f45928e`, then `2ce1e29`, which moved while I read. Read-only scripts over saved outputs, `tools/gate.py` on the saved ensembles, and `tools/proof_lean.py` on saved folders. No growth runs and no test suite; test counts come from the saved merge outputs.

**Result:** 8 OK, 5 small FIX. The close of P0 needs a FIX and a question for the maintainer: stopping is within their rule for trees, but it isn't shown for plots.

| # | Item | Verdict |
|---|---|---|
| 1 | Re-baseline on preview targets | OK |
| 2 | M2 draft | FIX, small |
| 3 | Gate | FIX, small |
| 4 | Top height | OK |
| 5 | PC against node | OK |
| 6 | Slowdown | OK |
| 7 | Target edits | OK, pending checker A |
| 8 | Merges and gain table | FIX, small |
| 9 | Merge rule | OK |
| 10 | Lean proof and golden gaps | FIX, small |
| 11 | CAMPAIGN.md | **FIX** |
| 12 | `tools/plot.py --resume` | OK |
| 13 | Example tree and wording | OK |

## Evidence by item

**1. OK.**
- Every band, verdict and share in `reports/rebaseline_M1.md` agrees with `verdicts_two_refs.txt`, including height PASS at 40 and 50 at the tag.
- Row 39 is marked provisional and cites row 35. The light gaps from the median are right (+15.3, +12.7, +7.5).
- Two small wording points:
  - Row 39 says "Every row", but the page omits the Baltic LAI rows at 20-40 and the INFO crown-ratio rows, which are only in the verdicts file.
  - Its `scorecard_base_*` also catches the old `scorecard_base_plots.txt`, which still has the simple top height (27.923). Name `_master` and `_tag`.

**2. FIX, small.**
- Sections 1, 3 and 5 now do what was asked: a leaf-area row in the fit table, no cut on height alone, light kept as a reported row.
- **The fix left a contradiction:** section 4, step 3 still says "those whose seed average isn't clearly failing continue to 30", while section 5 says "Stage 15 cuts nothing".
- Stage 30's leaf-area test is "isn't above the baseline by more than 2 standard errors". With few seeds that nearly always holds, so the cut drifts back towards height alone, and seeds per candidate is still "not set". Set it before the cut rule goes in DECISIONS.md.
- Stale: line 3 ("on the `p0-perf` branch") and line 80 (the second PC, skipped by row 37).

**3. FIX, small.** I checked these and they hold:
- `band_move` now tests the change in distance. My three cases (distance 0.05 to 0, 0.5 to 0.4, 0.4 to 0.5) all give "no change", and a real move still counts.
- A target scored on one side only stops the gate.
- On the saved ensembles, `base_trees` against `base_plots`-style self-comparisons run cleanly. The node against the PC is refused ("not one known machine"), and a null commit on an option is refused.
- `--ref` is required, verdicts come from `evaluate_ensemble`, and n and the caveat are printed. Q8 and Q9 are in the code and in PROTOCOL.md.

Two things remain:
- **A hole in the fix:** `--base-code` overwrites a real commit, not only a null one. Base `abc` against option `def` with `--base-code def` passes (`gate.py`, `check_like_for_like`). Accept the flag only when the manifest's commit is null, and add a test.
- **Q9 can't be run yet:** `tools/ensemble.py:45,55` always uses seeds 1 to N. Add a first-seed option before the first rerun on fresh seeds.

**4. OK.**
- `naslund_top_height` reproduces the cross-check: 28.878 at 50 and 30.587 at 60, against the mean of the per-plot figures in `top_height_check.txt`.
- It fits on all live trees with height over 1.3 m. Too few trees gives not applicable. The target and test are in, and the tag waits on checker A.
- Small: `tools/top_height_check.py:5` still says the scorecard uses the mean height.

**5. OK.**
- 216 of 225 is right, and the 9 identical are `regen10` timelines of trees removed at year 5-6.
- Among the metrics it names, leaf area's +142 % is the largest (internodes +119 %, light +78 %).
- The scope is stated, the cause is labelled as not tested, and plots are stated as not compared. "Three of the PC's rows within about 1 SE" holds (0.98, 0.72, 1.07).

**6. OK.**
- The table matches `repeat_*.json`, and all repeats share one hash.
- Disk is under 3 MB/s, faults under 2 a second at 1-3, and the clock range 4,561-4,667 MHz is right.
- "Peaks at 3" holds on the undisturbed repeats: 138-140 runs an hour against 127-128 at 4 free to move. Pinned, the ranges are 133-143 and 125-128.
- The disturbed group (13,873 faults a second, CPU 36.7 % against 29.3 %) is disclosed.
- Trivial: the 3-at-once second-stick figure should be 215, not 216. Its working is now shown and it's called an upper limit.

**7. OK, pending checker A.**
- `target_mean` is back to 4.5, and `age_years` is [45, 67] on both items with no scored age between 65 and 67.
- Row 38 and `milestone_M1.md` section 5 say so, and the reversal is named.

**8. FIX, small.**
- Sound:
  - 23 commits, none aborted.
  - Compare outputs are identical for `d205edd`, `63e2491`, `eb9c984` and `e23821f`, with 107, 107, 110 and 110 tests passing.
  - The loaded runs are disclosed.
  - The lean time gain is withdrawn.
  - 737 against 783 is real: same-code runs vary only 782-789.
- Left over:
  - The gain row "141 against 81" is from the first test. The repeats give 139 against 85, and the next row already uses 139.
  - "408 at the last" cites "the session". I found no saved file with it (PROTOCOL.md section 5).
  - The table lumps `63e2491` as 110 (its own run was 107) and says "all pass" for `e23821f` (110).

**9. OK.** Row 45 states the rule, the reason and its blind spots, and that the maintainer may overrule. The 12 commits touch no model path, and the daily report tells the maintainer. Change "reviewer pending" to reviewed.

**10. FIX, small.**
- The proof is valid: 0 values differ on all three pairs. CAMPAIGN.md items 6-7 are in.
- The exit 1 is avoidable. I ran the PC pair against `golden/after_95233fc/tree60/1_stand`, whose outputs hash the same as `pc_base`: "(rar) against (rar)", 0 differ, **exit 0**.
- Rerun with that pair and save the exit status. A proof that fails when a checker reruns it will cost more time than this.

**11. FIX, and the one that matters most.** This is what "Resume the campaign." reads, and it's still wrong:
- CAMPAIGN.md:31, "Exact next action": "a fresh reviewer for the P0 merges batch... On the PC: the rest of P0 in order: profile plot and mesh... lossless memory, lossless speed... When it finishes: top 15 at 20 seeds, then repoint `tools/param_audit.py`". The P0 work and the screen's next steps it lists are done.
- Also stale:
  - The "Current step: M1c" line.
  - The top-height line ("under 0.3 m keeps the simple version"; row 44 replaced it).
  - Line 57 ("the screen is next").
  - Line 59 ("screen, renders and checkers outstanding").
  - Line 117 ("While the screen runs: don't edit...").
- `reports/daily_2026-11-06.md` contradicts itself. "Where things stand" and "What's next" still say memory and speed work next and the screen about 60 % done, while its own table says P0 is done and the screen finished.
- "Then, in order" and lines 60 and 119 are right.

**12. OK.** On a plain `--resume`, `--mode` and `--set` are now ignored with a printed line, and they apply only with `--branch-from`. Golden runs at `eb9c984` are identical.

**13. OK.**
- The tool now records `code`, `checked_stats_sha256` and the GLB hashes.
- The median rule is stated as "my rule" in `tools/ensemble.py` and `milestone_M1.md:430`.
- "Seed 1 only" is in the research notes and the daily report, and per-age correlations are in the re-baseline page and the daily report.
- `example_5` keeping null `code` and no hashes needs no re-export for that alone. The model didn't change, row 35 covers the code, and my earlier recheck of its stats and GLB headers stands.

## P0's close, "What's left, and why P0 stops here"

### Are the estimates labelled well enough? Mostly yes, but four numbers lack their working
The section, the summary row and E11/E12 all say estimate. PROTOCOL.md section 5 also asks for the calculation:
- **"At most about 9 %, if it took no time at all":** carbon solve is 14.2 % in the table just above. It presumably means the Python part only (`parts`, 4.7 s tottime), so say that.
- **"At most about 5 % of the time it owns":** unclear. It reads as 5 % of mechanics, which would be 0.5 % of a run.
- **"About 30 % of layers, on about a quarter of the time":** I found no saved source for the 30 %. `_raw_fft` is 6.9 of 51.2 s, about 13.5 %, not a quarter. Likewise "up to about 8 %" has no working.
- **E11's "about 1.5x":** no working, and no statement that it's for trees. Plots spend more of their time in the Python-heavy parts, so it's likely higher there.

Two related labels:
- **"About 4.9x":** this divides 380 (lean, seed 1) by 77 (full outputs, mixed parameters). As a before-and-after of the campaign that's defensible, but lean against lean is 380/85, about 4.5x. Say which.
- **"3.1-5.0 GB":** I found 3.84 and 5.01 in the saved plots (`p38_nat`, `p33_nat`), and no 3.1.

### Is stopping within the maintainer's rule? For trees yes, on estimates. For plots, not shown and probably not.
- **The gain column is "on a tree" only.** The report's own table gives a plot carbon solve 25 % and mechanics 23 %. Using the tree's Python fractions (9 of 14 and 5 of 11), my arithmetic gives about 16 % and 11 % on a plot, an estimate from one profile. Both are over 10 %.
- **The plot profile is thin:** 25 trees to age 20, one run, with no function listing saved. The 100-tree, 60-year plot hasn't been profiled. The summary's "Done" goes further than this.
- **Splitting keeps the tree figures under 10 %.** The maintainer's brief has compiling hot loops as one item (P0 step 5, B5). As one idea it's 9 + 5 = about 14 % on a tree, and the two light ideas together are about 15 %. The report's own "together 15-25 %" shows this. Whether "idea" means the split or the brief's item is the maintainer's call.
- **Other listed ideas aren't accounted for.** I found no mention by these names:
  - stopping at the last scored age (A2);
  - reusing unchanged results;
  - removing repeated passes;
  - smaller integer types;
  - occupied grid cells only.

  Freeing dead parts and writing meshes part by part don't appear in the close either. "No measured gain yet" for the pickle isn't "under 10 %".
- **No speed idea was tried.** The stop rests entirely on one profile run under cProfile. That's a fair way to choose the order of work, but the maintainer should know it.

The close's honest points stand: the 2 GB miss and the 10x miss are stated plainly, and B8, E11, E12 and the proposals are answered.

**ASK MAINTAINER (add to `QUESTIONS.md` and carry on):** "Your rule stops P0 under 10 % per idea. On a tree each idea is under 10 % as I've split them. On a plot, carbon solve and mechanics look like about 16 % and 11 %, and compiling both is one item in your brief. Stop anyway, or do them first?"
- Options: (a) stop now and reopen them at M4; (b) compile the carbon solve now.
- I'd recommend (a): M2 runs single trees, the node already does 380 an hour, and arithmetic order may not hold. M4's 1,000 m² plots are when this starts to hurt.
- Meanwhile M2 can proceed.

## What's left, in priority order

1. **CAMPAIGN.md "Now" and the daily report's stale tables.** Settled by: line 31 naming the real next action, and the lines listed under item 11 corrected.
2. **P0's close.** Settled by: a plot column in the gain table, the four calculations shown, every brief idea listed with an estimate or "not estimated", the summary row reworded, and the question above in `QUESTIONS.md`.
3. **Gate.** Settled by: `--base-code` accepted only on a null commit, with a test, and a first-seed option in `tools/ensemble.py`.
4. **M2 draft.** Settled by: section 4 step 3 matching section 5, seeds per candidate set before the cut rule is logged, and the stale lines removed.
5. **Lean proof.** Settled by: a rerun against `after_95233fc`, saved with exit 0.
6. **Gain table.** Settled by: 139 against 85, and a saved file for 408 or the figure removed.
