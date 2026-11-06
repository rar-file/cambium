Fresh reviewer's report, saved as it stands.

# Review: node disk step (plots with no save files)

**What I did:** read the listed files and ran no model, no test suite and no SSH. I ran one small stub (real `spill_history` and `restore_history` on fake arrays) and read local `plot.json` files. The stub is `<scratchpad>\spill_check.py`.

**Things moved during the review:**
- The maintainer answered Q1 and Q2 (`87d0b6a`, 03:38).
- `tools/plot.py` changed at 03:44:31.
- `tools/proof_checkpoint.py` was restarted. At 03:47 it was still running, with no result.

Line numbers are for the files as of 03:47. Node-side logs and readings are taken as the report states them, because I couldn't check them.

| # | Point | Verdict |
|---|---|---|
| 1 | Did what was approved | **ASK MAINTAINER** |
| 2 | One seed, one run, noise | **FIX** |
| 3 | Two failures really one | **OK**, one warning |
| 4 | Wrong knob | **FIX** |
| 5 | Like for like | **FIX** |
| 6 | Idle machines | **OK** |
| 7 | Shared machines | **FIX** |
| 8 | Sources | Not applicable |
| 9 | Claims more than shown | **FIX** |
| 10 | Guesses labelled | **FIX** (wording) |

## 1. ASK MAINTAINER

**Handled by the rule:**
- The disk floor and deleting went to QUESTIONS.md.
- Nothing was deleted before the answer (report:44, row 34).
- The watcher only restricts the builder's own runs.

**Past the rule:**
- PROTOCOL.md:42 says "A killed run may be restarted once, after finding and fixing the cause; log it."
- Plots 3, 4, 5 were stopped, resumed, crashed, and started from 0. That is two restarts.
- At the second one the cause was known, but the code change was "Not yet run" (report:45) and isn't on the node. The new runs avoid the path; they don't repair it.
- report:49 softens this to "a second start, in fresh folders" and says "Row 33 logs it". Row 33 says only "they run again from the start". Neither says the rule was exceeded.
- The screen's in-flight runs were also stopped and restarted twice (report:27, :55). The report doesn't count them.

**Why it can't be settled here:**
- Line 42 sits in the PC paragraph of section 6, so its reach on the node is unclear. The builder treated it as binding (report:49), then passed it alone.
- The maintainer's answer (no limit on disk use) answered Q1 and Q2 only. The text they answered (`74355d0:QUESTIONS.md`) doesn't mention the crash or the restart, so it isn't approval.
- `tools/ensemble.py:16`, "A plot stopped partway starts again", turns unlimited restarts into standing policy.
- QUESTIONS.md now says "None right now".

**Question for QUESTIONS.md:** does "restarted once" bind on the node, and does it count stops the builder chose?
- (a) PC memory kills only.
- (b) Binds on the node; each extra restart asks the maintainer.
- (c) A restart from year 0 with the same code and seeds is allowed any number of times, logged.

My recommendation is (c). Meanwhile the plots carry on, since stopping them would be another restart.

## 2. FIX

The proof is one run: seed 1, 25 trees, to age 20, 0 deaths (`ckpt_proof.log:1`). The real plots have 100 trees and run to 60. It passed, then 3 of 5 plots crashed, so it has already failed to carry once.

Deaths are the main uncovered path. The figures below are for scale only, from older code on the PC (`plot.json`, `died_total`):

| Plot | Age 20 | Age 35 | Age 50 | Age 60 |
|---|---|---|---|---|
| golden plot25 (the proof's plot) | 0 | not run | not run | not run |
| p33_nat | 4 | 7 | 12 | 16 |
| p38_nat | 2 | 9 | 17 | 22 |
| c48m5_nat | 6 | 57 | 60 | 65 |

- **What the proof carries:** with no deaths, spill, trim and no spill leave outputs unchanged to age 20.
- **What it doesn't carry:** deaths after a resume (8 to 13 per plot after age 35 here), ages over 20, or 100 trees.
- **The new dense case:** it does exercise a tree dying again. PC golden `regen10` has `died_total` 2, 9, 14, 20 at years 5, 6, 8, 10. But it is one seed, ages up to 10, on worktree code, not the code plots 1 and 2 run.
- **Margin:** 31 GB against 30.4 GB is a 2 % margin on a guess (see point 10).

## 3. OK

The disk fall and the crash are separate failures, and the report keeps them apart (report:39-47).

I checked that a lost history cannot pass silently. `_encode_radius` tolerates a short list, but `_rings` then does `history[y]` at the final year (`treegen/export.py:303`) and raises IndexError. So report:43's reasoning holds: a plot past the old stop year has no such tree left.

**Warning:** report:43 attributes three crashes to one cause on one cited log (`base_plots_3.log`, with no local copy). A different bug gives the same symptom (see the resume section, items 1 and 2). Don't read a later IndexError as the same failure.

## 4. FIX

The knob works for the node today, but it is too blunt and too wide.
- **Blunt:** at year 30 the pickle is 1.86 of 2.37 GB per plot (report:15), or 78 %, and its temp copy makes the dips. `--checkpoint-every 0` also turns off the history spill and the trim, which hold RAM down (`tools/plot.py:11-13`, `treegen/growth.py:1942-1944`, `treegen/structure.py:107-108`). The report considers no alternative, such as spilling history but skipping the pickle.
- **Wide:** `tools/ensemble.py:50` hard-codes it for every machine, with no flag. The PC has 16 GB and a 4 GB floor, its 100-tree plots already peak at 3.1-5.0 GB with spill on (`peak_mb`), and it has shown no disk problem.
- **Direction:** this runs against P0's "stream history to disk" and the under-2 GB target (CAMPAIGN.md:68, :73).

## 5. FIX

**OK:**
- Same machine: golden plot25 is the node's (`node_a_hashes.json`: the node, 76 files).
- Comparison across commits: golden at `0b98044`, runs at `68782d9`, disclosed at report:31. `git diff --stat 0b98044 68782d9 -- treegen cli.py tools/plot.py` shows no `treegen/` change, only `--set` handling in `cli.py` and `tools/plot.py`.

**Not OK:**
- **Stopped folders would enter the verdict.** `tools/scorecard.py:547-549` takes every folder in the ensemble folder with a `plot.json`.
  - `74355d0:QUESTIONS.md:13` lists the stopped plots under `base_plots/`, and row 34 keeps `plot.json`. I couldn't check the node, so the location is inferred.
  - If they stay there, seeds 3, 4, 5 count twice wherever `stopped_plot_N` has a row, up to about age 35: 8 runs, mean shifted, spread narrowed.
  - At ages 50 and 60 those folders have no row, so 5 runs.
- **One ensemble is not shown.** Plots 1-2 and 3-5 have the same seeds and machine but different routes, and report:47 admits the gap. The re-baseline step (CAMPAIGN.md:33) has no route check, and that baseline anchors every later no-PASS-to-FAIL decision.
- **Timing and memory aren't comparable.** `runtime_s` and `peak_mb` in plots 1-2 cover only the part after the resume (`tools/plot.py:59`, :96). A watcher pause would also inflate `runtime_s`. Keep them out of P0's tables.
- **"Same commit" is a statement, not a record.**
  - `git_commit` is null, and the change doesn't backfill (report:53).
  - `tools/noise_cycle.py` first appears in `7ce8118`, not `68782d9`, yet `out/bench/node/noise_cycle.md` exists. So the node appears to hold at least one file outside `68782d9`.
  - Model files are unchanged between those two commits (empty diff stat), so the outputs shouldn't change.
- **Launch commands aren't saved.** I can't check `--trees`, `--mode`, `--no-mesh` or nice 19 on the resumed and fresh runs, or whether they went through `--mark-done`. Without `done.txt`, `tools/batch.py:106` would treat them as pending.

## 6. OK

- The PC is running the builder's proof now.
- The node is stated at 5 + 9 = 14, its limit (report:55). I couldn't check that.
- The stops and the 3-at-once period lasted minutes.
- One risk: a watcher trip idles the node until someone reads a log (see point 7).

## 7. FIX

**Pattern and floor: OK.**
- `pkill -u origin` matches only that user, and origin can't signal the server's other services anyway (`reports/P0_performance.md:36`).
- `tools/node_run.sh` launches with the full path, so the pattern catches those runs. No saved `pgrep` listing shows what it catches today.
- The floor is the builder's own choice after the maintainer's answer.

**Memory: not accounted for.** The report gives no memory figure for no save files; its only memory line is about `golden.py` (report:54).
- My estimate, not a measurement: history 2.3 GB (report:23) plus state of 2.5-3.5 GB, up to double with no trim, gives about 6-10 GB a plot.
- That is 30-50 GB for five, plus 9 screen runs at about 0.6 GB each, against 94 GB total with others at about 3 GB (`reports/P0_performance.md:7`).
- So it is probably inside the 8 GB floor on the node, but nobody has shown that.
- `PLOT_PEAK_GB = 6.0` (`tools/ensemble.py:33`) predates this and may be low.
- Nothing watches memory while a plot grows. `tools/batch.py:140-142` checks only at launch, and the watcher reads only disk.
- `peak_mb` for `plain` and `none` already sits in `ckpt_proof/*/plot.json` on the node.

**Watcher weak points (`tools/node_disk_guard.sh`):**
- It exits after one trip (:11), and its resume note (:4) doesn't say to restart it.
- It fails open: if `df` gives nothing, the test at :8 errors, counts as false, and the loop carries on blind.
- It has no heartbeat, so an empty log looks the same as a dead watcher, and CAMPAIGN.md:31 only looks for a line.
- Nobody is told on a trip, and paused runs keep their RAM.
- It is untracked but running on the node, against "Copy code at a fixed commit" (PROTOCOL.md:46).

**Live risks on plots 1 and 2:**
- Their histories to year 35 are the only copy, read at every death and at final export (`tools/plot.py:113`). Row 34's "once no run needs them" covers this; hold deletions to it.
- They also have no usable resume. The node's code deletes dead trees' histories, so `--resume` there would hit the same crash.

## 8. Not applicable

No literature values are used.

## 9. FIX

The three proof rows (report:33-35) agree with the log, and the commit messages are fine.

**Overclaims:**
- report:29, "**Proved no save files is lossless**". report:41 and :47 contradict this.
- `tools/ensemble.py:14-16`, "five of them would fill the node's shared disk, and without them the output is the same". A guess is stated as fact, and the proof's limits are dropped.
- `74355d0:QUESTIONS.md:27`, "a test showed that changes none of their output", with no word of the crash. **This is the text the maintainer answered.**
- Row 33, "Tested first ... 76 of 76". It doesn't say one 25-tree plot with no deaths, or that the test missed the crash.
- `74355d0:QUESTIONS.md:23`, "steady ... because plots no longer write save files", rests on two readings 8 minutes apart (report:18-19). The direction is plausible: finished PC plots' timelines are about 0.3 GB each.
- The same version's `QUESTIONS.md:13` and :21 say "finished plots" and "frees about 12 GB". All five plots were still running, and the 12 GB includes histories plots 1-2 still need. The answer supersedes this, so it is low priority.

**Missing:**
- The report doesn't record the proof's first attempt, or the restart cost in hours.
- **No saved path for** the free-disk table, 11.86 GB, 1.86 GB, 96 GB, 90 %, 84 % and the CPU readings. This breaks PROTOCOL.md:34.
- **The script behind `ckpt_proof.log`** isn't in either repo (no match for "only here" in `tools/`). So how long after year 10 the "stopped" run was killed can't be told.

## 10. FIX (wording)

The decision doesn't depend on this. A measured 10.7 GB free at year 35, with dips deepening (14 at year 25, 10.7 at year 35), is reason enough to act.

report:23 labels the estimate as a guess, and its arithmetic checks: 5 x (2.6 + 2.3) = 24.5; 0.5 x (55/30)^2.5 = 2.28; 18.6 + 11.86 = 30.46. The problems are around it:
- The 6.5 GB temp figure has no calculation (PROTOCOL.md:36), and it is below the 7.9 GB dip already seen at year 35 (18.6 to 10.7, which includes five years' growth).
- "The PC's finished plots: 2.3-3.5 GB" includes p24_nat (2.29 GB, last saved at year 52). It leaves out four finished 100-tree plots at 1.82-1.91 GB (`fr_nat`, `lc68_nat`, `p25_nat`, `p26_nat`).
- Those are older code, and the node's 1.86 GB at year 30 makes the low end unlikely. But the report's own method over 1.82-3.52 GB gives about 25-38 GB against 30.4 GB. So "might have been lower" is one-sided, and row 33's "probably" isn't earned.
- A measured point could replace the assumed curve: `p22_nat` has 1.25 GB of history at year 56 with 40 trees alive, about 31 MB a tree. That is about 2.4 GB at 78 trees, close to the guess.
- `tools/ensemble.py:14-15` carries no label at all. The forecast also gives only age 55, with nothing at 50 or 60.

## The resume fix in `tools/plot.py`

**`stale_history` does what report:45 says on these paths:**
- **Death, then a stop before the next checkpoint:** the history stays (:121) and the tree's second death restores it (:113).
- **Clearing:** it runs only after the atomic replace (`treegen/plot.py:323`, then `tools/plot.py:138`), so the newest pickle no longer counts that tree.
- **`--save-at`:** the clear runs before `copytree`, so a state folder holds only living trees' histories. The clear never touches `state_*`.
- **End of run:** final exports and the "no trees left" break (:127) both reach the clear at :146. A kill during final export can now be resumed.
- **`--resume --checkpoint-every 0`:** dead histories stay until the end. That is intended, and bounded by what is already on disk.

**Bugs and gaps:**
1. **Two checkpoints in one year (changed at 03:44:31; the report doesn't mention it).**
   - `--save-at Y`, with Y a multiple of `--checkpoint-every`, checkpointed twice. The second `spill_history` had nothing to write, and `np.savez` replaced `history_Y.npz` with an empty archive (`treegen/growth.py:1949-1953`).
   - My stub went from 11 arrays to 0.
   - The first proof attempt showed it: `plot_first/state_010/tree_000/history/history_010.npz` was 22 bytes with 0 arrays, `plot_first` had no tree exports, and nothing ran after it. The re-run has since wiped that folder (`tools/proof_checkpoint.py:73`).
   - The documented example at `tools/plot.py:8` (`--save-at 30`) would have hit this.
   - `tools/plot.py` now checkpoints once a year. `spill_history` itself still overwrites on a second call, and `tests/` has no `--save-at` case.
2. **A kill inside a checkpoint (still open).**
   - Trees spill before the pickle is replaced (`treegen/plot.py:311-323`), and `restore_history` reads every file (`treegen/growth.py:1965`).
   - So `history_035.npz` can sit beside a year-30 pickle. My stub gave 39 entries where 34 are needed, which raises IndexError at `treegen/export.py:265`.
   - With `--resume --checkpoint-every 0` the file is never overwritten, so every affected tree crashes at export, not only early deaths.
   - A half-written `.npz` also fails on load, and a `checkpoint.pkl.tmp` is left behind.
   - A full disk lands exactly here. "Safe moments" (report:37) is never defined.
3. **Orphaned histories.** A kill between the replace and the clear leaves a dead tree's history forever, because the next process's list starts empty and nothing sweeps it. This only leaks disk.
4. **Order at the end (:146-147).** The clear runs before the final `write_plot_json`. A kill in that gap leaves a folder that looks unfinished with its histories gone, so `--resume` would crash. The window is narrow.

**Proof gaps:**
- No dense `--checkpoint-every 0` case, which is the route plots 3-5 took.
- No kill inside a checkpoint.
- No unit test for the stale path.
- It prints "DIFFERENT" when no tree died. That fails safe but is the wrong word.

## FIX items, in priority order

1. **Stopped folders in the ensemble.** Settled by `ls` on `base_plots/`, moving `stopped_plot_*` outside it (a rename, no scorecard edit), and the scorecard header saying 5 runs. Do this before any re-baseline.
2. **Plots 1-2 route.** Settled by rerunning seeds 1 and 2 straight with no save files, then hashing against the resumed runs. If identical, the ensemble counts as one, and "no save files" has its first full-size evidence with deaths. If different, report the largest difference and use the straight runs. Add this to CAMPAIGN.md:33. It should cost about an hour a plot (my estimate).
3. **Memory.** Settled by reading `peak_mb` for `plain` and `none`, logging `free` and each plot's memory to age 60, stating the margin to the 8 GB floor, and resetting `PLOT_PEAK_GB`.
4. **Corrections.** Settled by rewording report:29, `tools/ensemble.py:14-16` and row 33 to state the proof's limits. Add the first proof failure, the restart cost and the second restart as an exception. Tell the maintainer in the next daily report that their answer was given without the crash in front of them.
5. **`tools/ensemble.py:50`.** Settled by making no-save a flag, with the node passing it, so PC plots keep their spill until their memory is measured.
6. **Proof and `restore_history`.** Settled by a finished `out/bench/p0/checkpoint_proof.txt` reading IDENTICAL on all cases, plus two new ones: dense with `--checkpoint-every 0`, and a kill inside a checkpoint. Also a small test in `tests/test_checkpoint.py`.
7. **Watcher.** Settled by committing it, failing closed on a bad `df`, adding a heartbeat line, adding the restart step to its resume note, and saving a `pgrep` listing.
8. **Raw data.** Settled by copying to `out/bench/node/`: the `df` readings, `base_plots_1..5.log`, the launch commands, the proof script and the CPU readings.
9. **Commit record.** Settled by `repo/COMMIT` plus SHA-256 of `treegen/`, `cli.py` and `tools/plot.py` on the node against `git show 68782d9:`, noted in DECISIONS.md for the null-commit results, including the 20-seed baseline.
10. **Small code order.** Settled by writing `plot.json` before the clear, sweeping orphaned histories at the end, and making `spill_history` refuse to overwrite with nothing.

**ASK MAINTAINER (separate from the FIX list):** whether the restart-once rule binds on the node (point 1).
