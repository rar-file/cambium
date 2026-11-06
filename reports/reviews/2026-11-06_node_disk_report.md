# Step report: the node's disk, and plots with no save files

Written by the builder, for review. Decisions made alone: DECISIONS.md row 33. Questions: QUESTIONS.md Q1, Q2.

## What happened

Times are the node's clock, 2026-11-06.

| Time | Free disk | What |
|---|---|---|
| Earlier, first look | 32 GB (P0_performance.md, says "32 GB of disk free") | before any plot |
| 03:00 | 17 GB | 5 plots running, year 15-20 |
| 03:05 | 19 GB | |
| 03:07 | 14 GB | during the plots' year-25 checkpoint, when temp and old pickles coexist |
| 03:09 | 18.6 GB | year 30; plots use 11.86 GB, of which checkpoint.pkl about 1.86 GB each |
| 03:13 | 10.7 GB | during the year-35 checkpoint; the lowest seen |
| 03:16 | 13.8 GB | proof run finished |
| 03:17 | 15.8 GB | plots stopped and resumed |
| 03:25 | 15.8 GB | steady |

**A plot writes a save file every 5 years** (`tools/plot.py --checkpoint-every`, default 5): `checkpoint.pkl` and each living tree's history. At the end the history is deleted, and only the pickle stays.

**My estimate of where it was heading: a guess, not a measurement.** At year 55: pickle about 2.6 GB per plot (the PC's finished plots: 2.3-3.5 GB, `out/bench/*/checkpoint.pkl`), history about 2.3 GB per plot (0.5 GB at year 30, scaled by age to the power 2.5, an assumed curve), so about 24.5 GB, plus about 6.5 GB of temp files during a checkpoint. Total 31 GB, against 30.4 GB available to the plots. Nothing ran out. The real figure might have been lower.

## What I did

1. **Stopped the screen** (it had just started), to free slots for a proof. It keeps finished runs, and was restarted after.
2. **Started a watcher** in the run account (`tools/node_disk_guard.sh`, in the worktree): under 8 GB free it pauses all my runs with SIGSTOP and logs a line. 8 GB is my choice, and Q1 asks the maintainer.
3. **Proved no save files is lossless** before relying on it: the same plot as golden plot25, three ways, at the node's current code `68782d9`. Raw: `out/bench/node/ckpt_proof.log`.

   | Way | Files identical to golden plot25 (recorded at `0b98044`) |
   |---|---|
   | Default, checkpoint every 5 years | 76 of 76 |
   | No checkpoints at all | 76 of 76 |
   | Stopped after the year-10 checkpoint, resumed, none after | 76 of 76 |

4. **Stopped the 5 plots at safe moments** and resumed each with `--checkpoint-every 0`.

## What went wrong

**My proof missed a case.** Plot25 has no deaths in those years, so it didn't test a tree that died after the checkpoint but before the stop. `export_tree` had deleted that tree's history when it died. On resume the checkpoint says it's alive, and when it dies again its history is gone: IndexError.

- Plots 3, 4, 5 crashed this way (`~/origin/base_plots_3.log`). Plots 1 and 2 passed the year their old runs had reached, so no such tree remains in them.
- Plots 3, 4, 5 run again from year 0 with the same seeds and `--checkpoint-every 0`. Their old folders were renamed `stopped_plot_N`, not deleted.
- **Fix in the worktree** (`tools/plot.py`, uncommitted when this was written): a dead tree's history is deleted only once a checkpoint no longer counts it as alive. `tools/proof_checkpoint.py` gains a case for it, stopping a dense plot hard after a death since its checkpoint. **Not yet run.**

**So plots 1 and 2 and plots 3, 4, 5 reach their results by different routes:** 1 and 2 ran to year 35 with save files, then resumed; 3, 4, 5 ran straight with none. The proof above says all routes give the same files, but it was on plot25 to year 20, with no deaths after the resume. Plots 1 and 2 have had deaths after their resume, which the proof doesn't cover.

**PROTOCOL.md section 6 says "A killed run may be restarted once, after finding and fixing the cause; log it."** Plots 1 and 2 were stopped once and restarted. Plots 3, 4, 5 were stopped once, resumed, crashed, and started afresh: that's a second start, in fresh folders. Row 33 logs it.

## Also

- `git_commit` is null in the node's run manifests, because the node has no git. The commit is in `repo/COMMIT`, not in the manifest. Fix in the worktree (`treegen/params.py`, falls back to that file). All the node's results so far, including the 20-seed baseline, have a null commit in their manifests.
- `tools/golden.py` reads the launcher's memory on Windows, not the run's (4.5 MB for everything). Fix in the worktree (`peak_of_run`). No effect on hashes.
- The screen ran at 3 at once for a few minutes, because the one-minute reading then was above 1 core (limit 8, minus 5 reserved for plots). Reading again gave 14, so it was restarted at 9.

## Where to look

- `git -C ../Cambium-p0 diff` for the code; `tools/example_tree.py`, `tools/node_disk_guard.sh`, `tools/light_lai_link.py` are new and untracked there.
- `git log -3 --stat` on master; DECISIONS.md row 33; QUESTIONS.md.
- `out/bench/node/ckpt_proof.log`.
