The same reviewer's re-review of its FIX items, saved as it stands.

# Re-review: node disk step, my 10 FIX items

**Result: 6 OK, 4 FIX, nothing for the maintainer.** None of the four open items changes a model number or a verdict, and no fix made an output wrong.

**What I did:** read files and ran small read-only commands, plus one stub on fake arrays using the real `sweep_after_stop`, `spill_history` and `restore_history`: `<scratchpad>\sweep_check.py`. No SSH, no growth runs, no test suite. Node results are taken as stated.

**Three things in the brief have moved:**
- **The daily report exists:** `reports/daily_2026-11-06.md`, commit `1e61244`, 04:57.
- **The proof rerun finished at 05:02:** all five cases IDENTICAL, with the dense plot on seed 2. Master's `out/bench/p0/checkpoint_proof.txt` is still the seed-1 version from before the rerun.
- **`d205edd` is being merged:** at 05:03:58 it was staged on master with `.git/MERGE_HEAD` present, but not committed. HEAD was `1e61244`.

| # | Item | Verdict |
|---|---|---|
| 1 | Stopped folders in the ensemble | **OK** |
| 2 | Plots 1-2 route | **OK** |
| 3 | Memory | **FIX** (one step left) |
| 4 | Corrections | **FIX** (small) |
| 5 | No save files as a flag | **OK** |
| 6 | Proof and `restore_history` | **FIX** (narrow) |
| 7 | Watcher | **OK** |
| 8 | Raw data | **FIX** |
| 9 | Commit record | **OK** |
| 10 | Small code order | **OK** |

## 1. OK
- `out/bench/ensemble/base_plots/` holds only `plot_1` to `plot_5`.
- `scorecard_base_plots.txt:1` says "5 runs", and `top_height_check.txt` lists five plots.
- I can't see the stopped folders' new place on the node (report:73).

## 2. OK, on the results as stated
Everything I could check locally agrees with them:
- **Seed 2 is the straight run:** `plot_2` has `resumed` false, `plot_seed` 2 in all 100 `stats.json`, and `peak_mb` 6,128.
- **The counts add up:** 6 trees were removed by age 35, which leaves 94 exported after the resume, and 94 x 2 = 188. 302 is 100 x 3 plus `plot.json` and `done.txt`. Local folders hold stats only, so I couldn't rehash them.
- **The check did go through deaths:** `died_total` at ages 35, 50, 60 is 8, 18, 20 in `plot_1` (12 after the resume) and 6, 12, 16 in `plot_2`.
- **Plots 3, 4, 5:** the stated 4, 5, 11 dead trees agree with the logs at years 30, 35, 35.
- **The label change now has a test:** seed 1 couldn't show the bug, because `--seed` defaults to 1. The proof's dense case now uses seed 2, and at 05:02 it reads IDENTICAL.

**Same class, not a blocker:** on resume, `environment` and `overrides` still come from the command line (`tools/plot.py:84-89`). No current run is affected, since the local manifests show `overrides` empty. The hash strips `run_manifest`, so the proof wouldn't catch a wrong `overrides`.

## 3. FIX: commit the merge
- `git show HEAD:tools/ensemble.py` line 36 still reads 6.0, below the measured 6.1-6.7 GB. Committing the staged merge settles this.
- The rest is done. Local `peak_mb` is 6,124-6,470 MB for plots 2-5. The stated lowest free memory of 64,816 MB leaves about 56.6 GB above the 8 GB floor.
- **Side effect of the reset:** 7.0 is a no-saves figure, but it applies in every mode. A PC plot with save files peaks at 3.1-5.0 GB, yet would now need 11 GB free to launch instead of 10. That is the safe direction, and it matters only if a plot is launched on the PC.

## 4. FIX: refresh the report
**Done:**
- report:31, row 33 and the `tools/ensemble.py` docstring are reworded.
- The first proof failure, the restart cost and the second restart are all recorded.
- **The maintainer has been told.** The daily report says the earlier answer on disk use didn't cover that, because those questions didn't mention the crash, and that Q3 then settled it.

**Left:**
- "After the review" rows 2, 3 and 6 are still in the future tense (report:74-75, :78). The results aren't in the report.
- Three lines are out of date:
  - report:51 "**Not yet run.**" contradicts report:43.
  - report:30 "Q1 asks the maintainer" has been answered.
  - report:53 "all routes give the same files" has been overtaken by the route check.
- report:45 estimates the route check at "about 25 minutes each". Same-sized plots took 2,515-2,680 s, or 42-45 minutes.
- "Fixed" is a restricted word (PROTOCOL.md:38), and it appears at report:43, `reports/P0_performance.md:204` ("now fixed") and the daily report ("Both are fixed"). The last two also run ahead of master until the merge is committed.

**Settled by** updating those lines and rewording those three places.

## 5. OK
- `tools/ensemble.py:49-53`: `no_saves` defaults to off, and only then adds `--checkpoint-every 0`.
- `:94`, `:100`: the flag reaches `run_plots`.
- The docstring states the limits of what has been tested.

## 6. FIX: the sweep uses the wrong clock
**What I asked for is done:** five cases IDENTICAL at 04:00 (seed 1) and 05:02 (seed 2), including the dense plot with no checkpoints and a stop inside a checkpoint. Two new tests are in `tests/test_checkpoint.py`.

**The hole:**
- `sweep_after_stop` compares a file's number with the plot's year (`treegen/plot.py:80`, `:353`).
- Files are named by the tree's own year (`treegen/growth.py:1955`), and a tree with germination g runs g years behind (`treegen/plot.py:216`).
- Real names in `p22_nat` at plot year 56: `history_056` (g=0), `history_055` (g=1), `history_054` (g=2).

Stub results, stopping inside a checkpoint:

| Case | File left behind | History length, needed | Result |
|---|---|---|---|
| Every 5 years, g=3 (the base plots' setting) | none | 30, 30 | ok |
| Every 3 years, g=3 (the proof's own setting) | `history_003` | 6, 3 | IndexError at export |
| Every 5 years, recruit germinated at year 20 | `history_015` | 18, 13 | IndexError at export |

- **Why the proof passes anyway:** it stops at the first g=0 tree (id 2 in seed 2), before the first g=3 tree (id 19). A later kill would fail it.
- **Exposure:** the crash is loud, not silent, and no current plot is exposed. Plots with `--regeneration` and save files would be.
- **Overclaim:** the merge title "a plot can resume after any hard stop" (`334d663`) claims more than this.

**Settled by** comparing each file with that tree's own year in the pickle, adding a test with g>0 and with a recruit, and making the proof's inside case stop after a g=3 tree has spilled.

## 7. OK
- It is tracked in git.
- It pauses if it can't read a figure (`tools/node_disk_guard.sh:21-22`).
- It writes a line a minute (`:32-34`), and its note gives the restart step (`:8-11`).
- CAMPAIGN.md:31 uses the new file names.
- **The listing is enough:** the brief lists this as not done, but I'd accept `running_listing.txt`. All 20 lines carry `~/origin/venv/bin/python` and nice 19: wrappers, plots, route check, and the screen's parent and 9 workers. That was the point of the listing. It also shows 14 runs at once at 03:49.
- **Minor, not blocking:** the listing doesn't record the command that made it, and the restart line at `:11` only works from `~/origin/repo`.

## 8. FIX: four evidence gaps
The readings file, scripts, listing, `deleted.log` and code hashes are saved. Missing or miscited:
- **The crash log is gone.** `node_plots_fresh.sh` redirects `>` into the same `base_plots_N.log`, so the saved logs for plots 3, 4, 5 are the fresh runs. No file under `out/bench/node` contains `IndexError`, and report:49 still cites that log. If the traceback survives in session output, save it; otherwise say it's lost.
- **Route-check output isn't saved.** "302 of 302", "188" and the plots 3-5 lines exist only in reports. Row 42's evidence is the tool, not its output. `node_diff_plot2.py` sits in a temp folder, and its output isn't saved.
- **`usage.log` isn't copied.**
  - `reports/P0_performance.md:205` cites the node path only.
  - 6.7 GB appears in no local output (highest local `peak_mb` is 6,470).
  - P0's 2,678 s also disagrees with `plot_3`'s `runtime_s` of 2,680.
- **Wrong citation.** The readings file cites `out/bench/node/ckpt_proof.log` for 988, 990 and 962 MB. That file has 12 lines and no memory figures. They probably come from `plain.log`, `none.log` and `resumed_part2.log` on the node.

**Settled by** copying these into `out/bench/node/disk_step/` and correcting the two citations.

## 9. OK
- I recomputed the hashes: 24 of 24 in `code_hashes.txt` agree with `git show 68782d9:<file>`. That is 20 `treegen/` files plus 4 others.
- The species and environment hashes in `plot_1`'s manifest (`3d876a3d...`, `1dfe6c5b...`) agree with that commit.
- Row 35 names the extra files, which accounts for `noise_cycle.py`.
- **Wording note:** row 35's "Runs from now on" holds only for code with `treegen/params.py:120`, which `68782d9` doesn't have.

## 10. OK
- `tools/plot.py:146-147`: `plot.json` is now written before the clear.
- `treegen/plot.py:80`: orphans are swept at resume, and a test covers it. I asked for this at the end of a run, but resume does the same job, because orphans arise only from a stop.
- `treegen/growth.py:1948-1949`: `spill_history` won't overwrite with nothing, and a test covers it.

## Did a fix make something new wrong?
No output is wrong. Two small things to know:
- The 7.0 side effect under item 3.
- `Plot.resume` now deletes files. Its only callers are `tools/plot.py:61` and a test, but a future tool reading a live run's folder through it would delete that run's in-progress history.

**The row 42 slip (17 at once against the limit of 14, about 2 minutes):** I can't tie it to any of my items. It is logged in row 42 and told to the maintainer in the daily report. Two small gaps:
- No saved file shows the 17.
- CAMPAIGN.md:31 says the pid file isn't reliable, but `tools/node_run.sh:4-5` still says to wait on it. That file hasn't changed since `68782d9`.

## Still open, in priority order
1. **Item 3:** commit the staged merge, and copy the 05:02 `checkpoint_proof.txt` to master.
2. **Item 8:** save the route-check output, the deep-compare script and its output, and `usage.log`; correct the crash-log and proof-memory citations.
3. **Item 6:** compare history files with each tree's own year, add the tests, and make the proof stop after a g=3 tree has spilled.
4. **Item 4:** update the report's stale lines and results, and reword "fixed".
5. **Outside the 10:** correct the pid note in `tools/node_run.sh`.
