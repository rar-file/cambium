Fresh reviewer's report, saved as it stands.

# Review: P0 merges, the PC's diagnosis, PC against node, and the maintainer's items

**Basis:** the step report and `d6680de`. Master moved to `460602d` while I read it, adding `d205edd` with its golden runs and tests. Where that changes a finding, I say so.

**What I ran:** read-only scripts over saved outputs, `tools/scorecard.py` on saved ensembles, and `gate`/`paired` on made-up numbers. I ran no growth runs and no test suite, and I left the node's disk and the plots' save files aside.

**Overall:** the merges are sound, and no default-path model result changed. The problems are in what was reported and in what the next steps will rely on.

## The ten points

### 1. Did it do what was approved? FIX
- **Merge rule:** The instruction was that each merge is checked against the golden hashes, and P0 step 6 says "after every change". The builder narrowed that to commits touching `treegen/`, `cli.py` or `tools/plot.py`, with no DECISIONS.md row.
  - The risk was small. None of the 12 touches those paths, `treegen/` and `cli.py` don't import from `tools/`, and each was merged just before a checked commit, so that commit's run covered it.
  - The last two (`5ffb4b6`, `5ed82a7`) were only covered later, by `d205edd`'s golden runs and tests.
- **Re-baseline command:** CAMPAIGN.md:33 gives `scorecard.py --ensemble` with no `--ref`, which scores at the approved tag. The builder used `--ref master`. See point 5 for what that changes.
- **Instruction 6 ("the largest output difference"):** answered for a few headline metrics only. See point 9.
- **Instruction 8 (M2):** the draft follows it in section 1 and contradicts it in sections 3 and 5. See point 4.
- **Renders:** "from the same runs" became a regrowth checked against the scored run. That was needed, because lean runs keep no history, and it is disclosed. OK.
- **Item 3:** no new golden runs were needed. OK.

### 2. One seed, one run, or within the noise? FIX
- **Top height, Q7:** Q7 suggests the gap may be small-plot noise, but it looks systematic.
  - 22 of 25 rows are positive. At age 60 it is +1.18 m with a standard error of 0.13 m across the five plots (`top_height_check.txt`).
- **Pinning:** see point 5.
- **"Tops out at 141 at 3":** this rests on one group per level, and the report itself says a group can move about 25 %.
  - 141 against 128 (4 at once) and 126 (2 at once) is inside that. Only 5 and 6 at once are clearly slower.
  - The screen's table (130 against 126) also shows a flat top rather than a fall at 4.
- **Height FAILs on the tree ensemble:** several sit close to the band's top.

| Age | Node, m over band top | Node, in SE | PC, in SE |
|---|---|---|---|
| 40 | 0.28 | 1.66 | 0.98 |
| 50 | 0.17 | 1.20 | 0.72 |
| 60 | 0.34 | 2.05 | 1.07 |

  - Row 39 gives means only. PROTOCOL.md section 2 asks for the spread and the share of seeds inside next to them; here the shares are 35 %, 30 % and 30 %.
- **Plots:** 5 seeds is the protocol's number, and the top-height FAILs are 1.77-2.80 m over the band. The 5.56 trees per plot don't threaten those verdicts. OK.
- **See-saw "mostly not":** seed 1 only. `research_notes.md` says so, but the daily report drops it.

### 3. Are two failures really one? OK for trees, FIX for plots
- **Trees:** linked at the level of means. The gap is at most 2.54 points, and fitted k is 0.367-0.393.
  - The report quotes the pooled correlation of 0.87. Within an age it is 0.705-0.892, so at age 50 leaf area explains only half of the seed-to-seed spread. The largest single-seed gap is -22 points. Quote the per-age figures.
  - The caveat that 0.37 is a model input (`species/betula_pendula.yaml:360`) is clear enough.
- **Plots:** LAI passes (3.76) and light fails (22.3 %), so "one failure" doesn't describe them, yet the daily report states it just below a table showing this.
  - At k = 0.37, LAI 3.6 gives 26.4 % light and 19.8 % needs 4.38. At the plots' own k of 0.399, it needs 4.06.
  - So the LAI band's lower part can't pass the light band. M2 draft line 17, "Light isn't counted as a third failure", would hide exactly this case.
- **Not stated anywhere:** the height rows at five ages and in two scenarios are also one "too tall" failure.

### 4. Wrong knob? FIX (M2 draft only; no knob was turned in this step)
- Section 1 says "never height alone", but the fit table in section 3 has no leaf-area row.
- Line 58: "at stage 15 only height counts for cutting". That removes candidates on height alone, before any leaf-area band applies. The stand-tree LAI band only applies at ages 45-65.
- The cut also uses a band at age 15, which the draft admits isn't an approved target.
- The row "M2 design | Written into the draft" overstates what was done.

### 5. Like for like? FIX
**The re-baseline rests on unapproved targets, with consequences nobody has stated.** Same saved runs, scored at the tag:

| Tree height | Mean (m) | Band top at tag | At tag | Band top at master | At master |
|---|---|---|---|---|---|
| Age 40 | 23.068 | 23.07 | **PASS** | 22.79 | FAIL |
| Age 50 | 25.286 | 25.31 | **PASS** | 25.12 | FAIL |
| Age 60 | 27.069 | 26.87 | FAIL | 26.73 | FAIL |

- Plot top height is NOT APPLICABLE at the tag, because its definition there is "unconfirmed".
- Row 39 and the daily report say "preview" but not this, and row 39's status is "confirmed". Its list of changed verdicts holds only once checker A confirms `8ecfca3` and `cddc9eb` and the tag moves.

**Pinned against free to move wasn't like for like.** P0_performance.md:143 says "little else running". `scale_pinned.json` shows otherwise, and lean runs write only about 0.1 MB/s themselves:
- At 1, 2 and 3 at once: disk writes of 56, 73 and 134 MB/s, with reads to match.
- At 4 at once: CPU busy 51.9 % against 29.6 % free to move, and 64 hard faults a second against 0.7. That is the 161 s against 113 s behind "worse at 3 and 4".
- At 5 at once: 95 hard faults a second.
- The first diagnosis's 1.15x also had a contaminated denominator: pinned alone at 51.7 s with 322 MB/s of writes.
- Only the 6-at-once row looks clean. "No better at any level" isn't shown, and 3 at once is the level the recommendation uses.

**Lean "44 s against 47 s" (your question): no.**
- Different sessions: lean took 42.9, 44.2 and 45.4 s across three tests, and full tree60 took 43.1-47.5 s on an unloaded PC.
- There is no time gain beyond the noise. The memory gain (440 MB against 581 MB) stands.

**Sound:**
- Row 39's "code `68782d9`" despite null commits: row 35's file hashes match `git show` for the five files I sampled. Seed 1's lean run also equals the node's golden tree60 on every scored key.
- "Same code" for PC against node: `after_0b98044` and `node_a` have the same `code_version`, and library versions are equal.

### 6. Idle machines? OK
- The PC's sequential runs follow the one-heavy-run rule, and profiling had started by 05:07.
- CAMPAIGN.md has the node at its limit of 14.
- **Limit of this check:** `usage.log` holds no run counts, so I can't confirm the node had no gaps.

### 7. Shared machines? OK
- Nothing here used admin rights or went beyond `~/origin`, and I saw no change to the server's other services.
- The saved screen log shows 9 at once, which fits 14 minus the five plots.
- The 17-at-once slip is logged in row 42 and in the daily report, though not in this step's report.
- The `node_run.sh` pid note is already open in the disk re-review, so I don't repeat it.

### 8. Sources? FIX
- **`target_mean` 4.5 to 4.6 isn't a rule-a correction.** Rule a means matching "its source's exact definition".
  - The item's source and DOI are still Forests 10:265, whose stands average 4.5. The 4.6 comes from another paper (10:925, Table 5), reached through a summarising fetch.
  - It is unscored, and row 38 names it. But commit `4df1c63` doesn't mention it ("Bands unchanged"), and the step report calls the edits "moved text".
  - `reports/milestone_M1.md:258` still says 4.5.
- **The other edits are sound:** dropping "at 1.0-2.0 m" follows the reading, the 14.8 and 6.4-19.8 quote is carried over, and the model's sampling height stays in the scorecard's note (`treegen/light.py:241`).
- **Pages:** the HTML has none, so rule a's "quote and page" stays open until checker A or the PDF. Row 38 says so.
- **`age_years: [45, 65]` (your question): yes, change it.**
  - The stands are 45 and 67, and `source_stands` already says 67. Use [45, 67] in both items under rule a.
  - No scored age falls between 65 and 67, so no verdict moves.
- **Third-party copies:** none. No parameter was tuned.
- **Q7 leaves out the source's own sentence.**
  - It says the curve-or-average question isn't settled from pp. 55-58. But `targets.yaml:151-153` and `tools/top_height_check.py:3-4` quote p. 58: "Top height is defined as the height according to the height curve at the mean diameter of the 100 by diameter largest trees per hectare."
  - The maintainer should see that before choosing, because it favours option (b) in kind, though the curve itself stays unnamed.

### 9. Claims beyond the work? FIX

| Claim | Where | What the outputs show |
|---|---|---|
| "every one of the 225 files differs" | P0:109, report:27, daily | 216 differ. 9 are identical: `regen10` `timeline.json` for trees 005, 010, 011, 018, 023, 024, 034 and `timeline.npz` for 010, 011 |
| "Largest difference in any year": leaf area, +142 % | P0:121 | True only for headline metrics of one seed's stats. `hanging_twigs` +203 % (142 against 430), `carbon.leaf_build` +149 %, `carbon.late_shoot_net` 1.11 against 1411. Plot and mesh files weren't examined |
| "the ensemble's verdict doesn't depend on which of these two ran it" | P0:137, `d6680de` | True today for nine tree rows, three of them within about 1 SE of the band on the PC. Plots weren't compared |
| "4,590-4,610 MHz in every case" | P0:162, daily | 4,516-4,675 across the scale runs. It rises with load, so "clock: no" still stands |
| "102 pass at the tip" | P0:185 | 102 was at `95233fc`. `5ffb4b6` then added 5 tests. `d205edd.tests.txt` has 107 passing, and the table doesn't list `d205edd` |
| "tree60 43-47 s" | P0:187 | Drops the two loaded merges at 77 s (plot25 at 89 s) without saying so |
| "the node does 280-380 an hour" | P0:170 | I found no source for 280. The table has 262 at 8 and 380 at 14 |
| "reused 30 cases" | P0:194 | The saved log copy shows "58 already done" for its restart, and no 30 |

**Your hash-table question:** it doesn't overclaim. I recomputed all seven `after_*` against `pc_base`: 225 identical, 0 differ, 0 in one only. Each manifest lists exactly that commit's files as uncommitted, and the merge outputs show no conflicts.

The earlier "now fixed" on the seed label is now reworded, and `d205edd` is on master.

### 10. Guesses labelled? FIX
- **Unlabelled guess:** "the chips round differently" (P0:55, P0:109, daily). It was never separated from the other differences between the builds: Windows against Linux, OpenBLAS kernels, the C maths library. Say "most likely, not tested".
- **Second stick:** labelled as a guess, and the range is reasonable, but no calculation is shown (PROTOCOL.md section 5). One that works: assume doubled bandwidth makes n runs behave like n/2 on the free-to-move table.
  - 3 at once: 211 runs an hour.
  - 4 at once: 251.
  - 6 at once: 281, which assumes no cache limit.
- **"Shared cache limits from about 4 copies":** probably comes from the benchmark. 4 x 8 MB is 32 MB, which is the 5800X's L3 (from memory of the spec, not from the repo). It says little about a 440 MB run.
- **"Most likely" memory bandwidth:** properly labelled.

## The specific checks

### `git diff bc723ee HEAD -- treegen cli.py tools/plot.py`
**Default straight runs: nothing changes a number.** Non-lean branches keep their order and draw no random numbers.

Three smaller changes:
- `spill_history` now skips only an empty write.
- `threads.py` changes results on Linux only, intentionally (one thread); that came before the node's golden runs.
- `tools/golden.py` changed in four commits without weakening the check: it only added `state_*` and `states` to the exclusions.

**What the four golden runs can't see:**

| Blind spot | Covered elsewhere? |
|---|---|
| Lean mode, used by every tree baseline and the screen | The repo's test covers only 8 years. I checked three 61-year pairs (PC seed 1, node seeds 1 and 5) on all 23 scored keys: 0 differences. P0 A1 asks for a proof, and none is saved |
| Seeds other than 1 | No. The `plot_seed` bug shows this is a real gap |
| Resume, branch, `--save-at`, `--set` | `proof_checkpoint`, one seed per case |
| `--checkpoint-every 0` | The proof and the route check |
| Plot meshes (both plot goldens use `--no-mesh`; `history/` isn't hashed) | No; M4 needs this |
| Plots past age 20, managed mode, regeneration | No, but the diff barely touches them |
| Linux code paths | Node golden at `0b98044` only; re-record before the next code copy |

**Behaviour change outside the default path:** `tools/plot.py:64-68` now applies `--mode` and `--set` on a plain `--resume`, where they used to be ignored, and it says nothing when it does.

### `tools/gate.py` and `paired.band_move` against the wording
**Correct:** moves that stay on one side of the band, moves inside the band ("no change"), the paired SE, and skipping INFO rows.

**Wrong or missing** (the first three I reproduced on made-up numbers):
- **Tests the whole move, not the change in distance (`paired.py:64`):**
  - Distance 0.05 to 0, with a move of -0.75 and SE 0.104, gives "closer".
  - Distance 0.5 to 0.4 across the band gives "closer", and 0.4 to 0.5 gives "further".
  - All these distance changes are under 2 SE, so they don't meet "further from its band by more than 2 standard errors". This is live, because heights at 40-60 sit just above the band.
- **Silently drops rows (`gate.py:60-61`):** a target that PASSes on all seeds and is NOT APPLICABLE on the option's vanishes, and the gate says ok. A partial drop shrinks n, and the table (`:102`) shows no n.
- **No seed, machine or code check:** 3 of 20 seeds passed as a correction, and nothing in `gate.py` reads a manifest, despite "on one machine" in its docstring.
- **Its own `verdict()` (`:44`, band from `:63`):** the wording says "the scorecard's ensemble verdicts", and it ignores the option's band. The same arithmetic gives no wrong verdict today, since no band that varies by seed is scored. It should call `evaluate_ensemble`.
- **Default `--ref` is the tag (`:95`):** plot top height would drop out silently until the tag moves.
- **Docstring's "about 1 in 20":** 2 SE is about 1 in 17 at 20 seeds and 1 in 9 at 5 plots. The caveat that a lone improvement isn't a result is never printed, and `decide` passes on one.

### `tools/example_tree.py`
**OK: the check is real.**
- I repeated it from the saved files: 61 years, 23 scored keys, no key missing, 0 differences, same machine. Only the keys lean leaves out differ.
- Seed 5 really is closest to the median by the tool's rule (1.08 against 1.28 for seed 19).
- The GLB headers match `example.json` on vertex counts (110,192 at age 60), and the mesh top is 26.977 m against 26.974 m scored.
- The test has a negative control, using another seed.

**Limits:**
- It compares yearly stats rounded to about four decimals, not geometry. That is strong evidence, because in this model a change of a few parts per million diverges within years, but it isn't a hash.
- `code` is null, and `checked_against` is a path with no hash of what was compared.
- The median rule (four metrics at age 60) is the builder's own and appears only in code.

## FIX list, in priority order
1. **Re-baseline on preview targets (row 39, daily).**
   - Settled by: both verdict sets side by side, with spread and share; the row marked provisional until checker A and the tag move; a cite of row 35.
2. **M2 draft (`reports/M2_design_draft.md`, before the cut rule goes in DECISIONS.md).**
   - Settled by: leaf area in the fit table with its age limits; no cut on height alone; light kept as a reported row, with the LAI 4.06-4.38 arithmetic for plots.
3. **Gate.**
   - Settled by: added tests showing that a scored row turning unscored blocks; that too few seeds, another machine or other code is refused; that crossing a band uses the change in distance; that verdicts come from `evaluate_ensemble`; and that n and the caveat are printed.
4. **Q7's text.**
   - Settled by: quoting p. 58, adding the +1.18 +- 0.13 m at age 60 and 22 of 25 positive, and dropping "small-plot noise" as the reason to wait. The maintainer then decides.
5. **PC against node wording.**
   - Settled by: 216 of 225; the largest difference with its scope stated, or computed across all outputs; verdicts "today, nine tree rows, plots not compared"; the rounding cause labelled a guess.
6. **Slowdown section.**
   - Settled by: rerunning pinned and free to move at 2, 3 and 4, three times each, on a quiet PC with the counters saved. Or by withdrawing "no better at any level", "worse at 3 and 4" and "more than 3 is slower" down to what is shown. Also correct the clock range and show the second-stick calculation.
7. **`target_mean`.**
   - Settled by: reverting to 4.5, or adding 10:925 as a stated source for checker A to rule on; naming the change in the report; updating `milestone_M1.md`. Change `age_years` to [45, 67] in the same batch.
8. **Gain table.**
   - Settled by: dropping the lean time gain or measuring it in one session, and giving the 77 s and 89 s loaded runs, the 107 tests and a row for `d205edd`. Source or remove "280" and "30 cases".
9. **Merge rule.**
   - Settled by: a DECISIONS.md row saying what was run and why, for the maintainer to overrule if they wish.
10. **Saved proofs and golden gaps.**
    - Settled by: a saved lean-against-full output; a CAMPAIGN.md line to re-record the node's golden runs before the next code copy; a golden or proof case at another seed and with plot meshes before M4.
11. **CAMPAIGN.md stale lines.**
    - Line 60 ("steps 1, 2, 4-8 after M1"), lines 117-119 ("Nothing is merged to master yet"), and items 4-6 of "Then, in order". They mislead a "Resume the campaign."
12. **`tools/plot.py:64-68`.**
    - Settled by: limiting `--mode` and `--set` to `--branch-from`, or warning on `--resume`; golden runs after the change.
13. **`example_tree.py` and the report's wording (small).**
    - Add `code`, plus hashes of the compared file and the GLBs. State the median rule, and add per-age correlations and "seed 1" to the see-saw line.

## ASK MAINTAINER
1. **A correction that takes a target from PASS to FAIL.** PROTOCOL.md section 9 says "don't revert" for significantly worse, but item 3 forbids PASS to FAIL. `gate.py` prints both "don't revert it" and "These items: FAIL".
   - I'd follow "don't revert, QUESTIONS.md", since a correction may be exposing a second error.
2. **False blocks.** An option with no effect gets a chance "further" at up to about 24 % on 9 tree rows and 59 % on 15 plot rows if rows were independent; the real figure is lower because they're correlated. Section 9 then says don't adopt and don't tweak.
   - I'd allow one confirming rerun on fresh seeds before parking a sourced option.
3. **Light band's meaning.** The 6.4-19.8 % is "individual values" across 110-241 points, while the verdict uses an ensemble mean. A mean of 19 would PASS against a measured median of 14.8. It's a strong FAIL today, so nothing changes now.
   - I'd keep the band and report the distance from the median next to it.
4. **Q7** stays open, once its text is corrected.
