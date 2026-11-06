# P0: Performance

Started and finished 2026-11-06. Everything below keeps outputs bit-for-bit identical.

## Summary

| Goal | Result |
|---|---|
| About 10x campaign throughput | **About 4.9x:** 77 runs an hour on this PC one at a time, 380 on the node at 14. Not 10x. |
| Outputs identical | Yes, on the four golden runs, at every model-touching merge |
| 100-tree, 60-year plot under 2 GB | **Not met:** 3.1-5.0 GB with save files on this PC's older runs, 6.1-6.7 GB with none on the node. See "What's left" |
| Stop when every remaining idea gains under 10 % | Done: see "What's left". These are estimates |


## The node

The node: Ubuntu 24.04, ARM Neoverse-N1, 16 cores with no hyperthreading, 94 GB of memory, 32 GB of disk free. Other services run there, lightly: 0.25 cores and about 3 GB when measured.

### Dedicated user

The runs use a dedicated account with no admin rights, reached over SSH with its own key, which stays outside the repo. It was set up once from the server's admin account, after checking that no run was still going, and the admin account hasn't been used for runs since.

**Checked, logged in as the run account:** it is in no admin group, `sudo` asks for a password it doesn't have, and nothing outside its own folder is writable.

**The limit of this:** the run account can't change or stop the server's other services, but it still shares their CPU, memory and disk. Lowest priority (`nice 19`), the CPU check below and the 8 GB floor cover the first two. Disk has no hard limit; `~/origin` is 1.8 GB.

**After the move:** the environment was rebuilt, because it holds absolute paths, and tree60 still hashes the same as before the move.

### Runs at once

The maintainer's rule: before each batch, the CPU used by every process that isn't ours, averaged over a minute; above 1 core, 8 at once; otherwise 14. `tools/node_limit.py`. First reading: 0.25 cores, so 14.

### Golden runs on the node

Recorded twice side by side (`out/bench/node/`), at one maths thread, kernel `neoversen1`, code `0b98044`. **All 225 files were identical between the two recordings** (`golden_compare.log`).

| Run | Seconds, first / second | Peak MB, first / second | Files |
|---|---|---|---|
| tree60 | 93.7 / 94.1 | 770 / 767 | 3 |
| mesh30 | 28.3 / 27.7 | 520 / 518 | 13 |
| plot25 | 129.6 / 122.4 | 993 / 979 | 76 |
| regen10 | 38.3 / 38.7 | 491 / 495 | 133 |

Compared with this PC below: they differ.

### Throughput against this PC

| Machine | Runs at once | Mean run time (s) | Slowdown against 1 | Runs per hour |
|---|---|---|---|---|
| PC, 1 thread (screen so far) | 1 | 47 | 1.00x | 77 |
| PC | 2 | 77 | 1.64x | 93 |
| PC | 3 | 84 | 1.79x | 129 |
| Node | 1 | 85.8 | 1.00x | 42 |
| Node | 4 | 96.4 | 1.12x | 149 |
| Node | 8 | 110.1 | 1.28x | 262 |
| Node | 14 | 132.8 | 1.55x | 380 |

Sources: `out/bench/m1/screen/runs.csv` (91 runs when read) and `out/bench/node/parallel_diagnosis.md`. **Not quite like for like:** the PC's screen runs keep their history and the node's were lean, and the PC's run times vary with the parameter being screened. A like-for-like figure comes from the PC's diagnosis run. All hashes were the same at every level on the node.

**What this shows so far:**
- One PC core is nearly twice as fast as one node core: 47 s against 86 s.
- The node scales far better: 14 at once slows each run by 1.55x, while 3 at once on the PC slows each by 1.79x. So the node at 14 gets about 3 times the PC's best so far.
- **The node doesn't top out within the limit.** More at once kept adding throughput up to 14, its limit.
- **The node's memory benchmark:** a workload in memory slows to 0.52x at 14 copies, while one inside a core's cache stays at 0.99x. So memory bandwidth is the node's limit too, though a mild one at this scale.
- **The PC's own slowdown:** diagnosed below.

## The PC's run time against runs at once

From each screen's `runs.csv`. Runs at once is the time-weighted mean over each run's life. Parameter changes alter run time too, so compare groups.

| Maths threads | Runs at once | Runs | Mean run time (s) | Runs per hour |
|---|---|---|---|---|
| 16 | 1 | 1 | 48 | 74 |
| 16 | 2 | 6 | 74 | 97 |
| 1 | 1 | 20 | 47 | 77 |
| 1 | 2 | 19 | 78 | 93 |
| 1 | 3 | 74 | 83 | 130 |
| 1 | 4 | 48 | 114 | 126 |

- **One thread didn't remove the slowdown:** at 2 at once, 78 s against 74 s at 16 threads, though the 16-thread group has only 6 runs. Competition between maths threads wasn't the cause.
- **This PC tops out at about 3 at once.** 4 at once is no faster overall (126 against 130 runs per hour), so more cores wouldn't help as it stands. The cause is below.
- **One thread costs nothing measurable alone:** 47 s against 48 s.
- **The whole screen:** 161 runs in 5494 s, 105 runs per hour, 2.6 at once on average, against 77 per hour one at a time.

## The PC's golden runs

Recorded twice at master `bc723ee`, one at a time, one maths thread, kernel `Haswell`. **All 225 files were identical between the two recordings** (`out/bench/golden/pc_base`, `pc_base_rerun`). Peak memory is each run's own record; `hashes.json` for these two says 4.5 MB, which was the venv's launcher; `tools/golden.py` now reads each run's own figure (`peak_of_run`).

| Run | Seconds, first / second | Peak MB, first / second | Files |
|---|---|---|---|
| tree60 | 45.7 / 47.5 | 581 / 581 | 3 |
| mesh30 | 14.6 / 14.6 | 385 / 388 | 13 |
| plot25 | 71.6 / 69.3 | 782 / 786 | 76 |
| regen10 | 23.9 / 22.9 | 402 / 400 | 133 |

## This PC against the node

**Same code, same seed: 216 of the 225 files differ** (`tools/golden.py compare pc_base out/bench/node/node_a_hashes.json`). The 9 identical are `regen10` timelines of trees that died early. Crown width first differs at year 2, and other outputs from year 3. It behaves like the chaos from a tiny parameter change. The cause is most likely rounding, but I haven't separated chips from the other differences between the builds: Windows against Linux, OpenBLAS kernels, the C maths library.

**Seed 1, node minus PC** (`out/bench/node/golden_tree60/stats.json`):

| Age | Height (m), PC / node | DBH (cm), PC / node | Leaf area (m2), PC / node | Diffuse light (%), PC / node |
|---|---|---|---|---|
| 20 | 15.20 / 14.77 | 14.19 / 13.61 | 18.6 / 15.9 | 50.8 / 53.8 |
| 30 | 19.97 / 19.98 | 18.76 / 18.38 | 46.9 / 46.2 | 45.8 / 40.2 |
| 40 | 23.09 / 23.48 | 22.97 / 23.23 | 61.1 / 60.9 | 34.3 / 35.2 |
| 50 | 25.02 / 25.04 | 26.05 / 27.05 | 66.4 / 63.3 | 30.3 / 31.6 |
| 60 | 26.11 / 26.51 | 28.86 / 29.35 | 65.6 / 65.2 | 29.8 / 30.0 |

**Largest difference, for seed 1's tree60 only; plot and mesh files weren't examined.** Among height, DBH, leaf area, LAI, crown ratio, crown width, light and internodes: leaf area at year 17, 10.5 against 25.3 m2, +142 %. From age 20 on, in the scored metrics: LAI at year 24, +27 %. Other yearly stats differ by more: hanging twigs +203 %, and `carbon.late_shoot_net` 1.11 against 1411.

**Do verdicts change? No.** 20 seeds on each machine, targets at master (`out/bench/ensemble/scorecard_base_trees.txt`, `scorecard_pc_trees.txt` in the worktree's `out/`):

| Target | Age | Node, mean +- SD | PC, mean +- SD | Verdict, both |
|---|---|---|---|---|
| Height (m) | 20 | 14.89 +- 0.48 | 14.85 +- 0.77 | FAIL |
| Height (m) | 30 | 19.73 +- 0.71 | 19.66 +- 0.87 | FAIL |
| Height (m) | 40 | 23.07 +- 0.75 | 22.96 +- 0.79 | FAIL |
| Height (m) | 50 | 25.29 +- 0.62 | 25.23 +- 0.66 | FAIL |
| Height (m) | 60 | 27.07 +- 0.74 | 26.93 +- 0.85 | FAIL |
| LAI | 50 | 3.09 +- 0.41 | 3.30 +- 0.32 | FAIL |
| LAI | 60 | 3.27 +- 0.37 | 3.37 +- 0.30 | FAIL |
| Diffuse light (%) | 50 | 30.1 +- 4.2 | 28.2 +- 3.5 | FAIL |
| Diffuse light (%) | 60 | 27.5 +- 2.7 | 26.9 +- 2.9 | FAIL |

The largest gap between means is LAI at 50: 0.21, about 1.8 standard errors of an unpaired difference, on one of nine rows. These can't be paired, because the same seed is a different tree on each chip. **So a seed's tree belongs to its machine. Today, on these nine tree rows, the two machines' verdicts agree;** three of the PC's rows are within about 1 standard error of the band, so that could change. Plots weren't compared. Comparisons still stay on one machine, as PROTOCOL.md section 6 says.

## Why runs slow each other down on the PC

The maintainer asked which of these explains it: memory bandwidth, disk, paging, cores or clock speed.

**Answer: most likely memory bandwidth and the shared cache.** That's by elimination and from a benchmark: Windows can't show bandwidth directly.

**Test:** lean trees, seed 1, on a quiet PC, three repeats each way, every hash the same (`out/bench/p0/repeat_summary.txt`, `repeat_*.json`). My first comparison ran while other work was on the PC, so it's withdrawn.

| Runs at once | Free to move: mean of 3 (s) | Each repeat | Runs per hour | Each on its own core: mean of 3 (s) | Each repeat | Runs per hour |
|---|---|---|---|---|---|---|
| 1 | 42.5 | 43.6, 41.6, 42.2 | 85 | 41.9 | 42.2, 41.8, 41.6 | 86 |
| 2 | 58.0 | 59.0, 57.6, 57.5 | 124 | 56.6 | 59.1, 56.7, 53.9 | 127 |
| 3 | 77.7 | 76.9, 78.4, 77.8 | 139 | 78.0 | 81.0, 77.6, 75.4 | 138 |
| 4 | 116.9 | 125.5, 112.9, 112.4 | 123 | 113.8 | 114.8, 114.3, 112.3 | 127 |

- **This PC peaks at 3 at once.** At 4 it does fewer runs an hour than at 3, by more than the spread between repeats.
- **Pinning makes no difference** at any level. **A correction:** the first diagnosis showed 1.15x pinned against 1.75x free at 2 at once (`parallel_diagnosis_first.md`), so I told the maintainer pinning looked like the fix. Those groups were disturbed by other work on the PC.

| Possible cause | Verdict | Evidence |
|---|---|---|
| Disk | No | Lean runs write under 3 MB/s at every level |
| Paging | No | Under 2 hard faults a second at 1, 2 and 3 at once. At 4, one group had 13,873 a second and took 125.5 s, against 112-115 s for the others, so that was something else on the PC |
| Clock speed | No | 4,561-4,667 MHz, rising with load |
| Cores | No | 8 physical cores, and throughput falls after 3; pinning doesn't help |
| **Memory bandwidth, and the shared cache** | **Most likely** | Benchmark below, and nothing else is left |

**The benchmark, speed per copy against 1 alone:** in a core's own cache, 0.97x at 4 copies. In the shared cache (8 MB), 0.94x at 2 and 0.38x at 4. In memory (512 MB), 0.50x at 2 and 0.24x at 4: one copy alone already uses the whole 17 GB/s, and more copies split it. The model's less memory-bound than that benchmark, since it slows only 1.36x at 2.

**What would fix it:**
- **For now, at no cost:** at most 3 at once on this PC. Batch work is on the node anyway.
- **A second stick: an estimate, not a measurement.** It would double memory bandwidth. If that makes n runs behave like n/2 do today: 3 at once, 216 runs an hour (mean of the 1 and 2 rows, 50.2 s); 4 at once, 248; 6 at once, 278 (the 3 row, 77.7 s). That assumes all the slowdown is bandwidth and none is the shared cache, so these are upper limits: up to about 2x. The maintainer's second slot doesn't work at the moment, so it may need more than a stick. The campaign doesn't need it: the node does 262 at 8 and 380 at 14.

**Power mode:** Balanced, not Best performance (`powercfg`, and the overlay setting is empty). The clock figures above show it costs nothing measurable, so I'd leave it.

**Time writing files:** not significant, so no Defender exclusion is needed. A tree spends 0.6 of 44.5 s on timeline and stats; profile shares are 1.1 % on a plot and 2.3 % on a mesh export (`out/bench/p0/profile_*.md`). Save files don't change that on this PC: plot25 took 69 s with them and 68 s without, with 327 MB against 29 MB on disk. The node's 185 s against 124 s was contention between runs, not the writing.

## The merges

23 commits from `p0-perf`, one at a time. Those touching `treegen/`, `cli.py` or `tools/plot.py` needed all tests and all four golden runs identical to `pc_base`, or the merge was aborted. **None was aborted, and none conflicted.** Raw: `out/bench/p0/merges/`.

| Commit | What | Model paths? | Tests | Golden |
|---|---|---|---|---|
| `f92ea8c` | Lean mode | yes | 63 pass | identical |
| `41abb3b` | Checkpoints | yes | 71 pass | identical |
| `43ead90` | Worker kit, lock file | yes | 76 pass | identical |
| `0b98044` | Linux support | yes | 81 pass | identical |
| `68782d9` | Ensembles, paired comparison | yes | 90 pass | identical |
| `b64f75a` | Resume after any stop | yes | 98 pass | identical |
| `95233fc` | Node tools, golden memory | yes | 102 pass | identical |
| `d205edd` | A resumed plot's seed label; plots' memory figure | yes | 107 pass | identical |
| `63e2491`, `eb9c984` | Resume by each tree's own age; gate, scorecard | yes | 110 pass | identical |
| Tree arrays grow by 1.25x | Lossless memory | yes | all pass | identical |
| 12 others | Tools and reports only | no | not run for each; each covered by the next checked commit | not run for each (DECISIONS.md row 45) |

**None of these makes a default run faster:** on an otherwise idle PC, tree60 43-47.5 s against 45.7 s, and plot25 68-70 s against 71.6 s, within what a run moves. During the two merges that ran beside the PC's ensemble, tree60 took 77 s and plot25 89 s, so those two say nothing about speed. **Their gain is in how they're used:**

| Change | Measured gain | Source |
|---|---|---|
| Lean mode | No time gain beyond the noise: lean took 42.9, 44.2 and 45.4 s across three tests, and full 43.1-47.5 s. Peak memory 440 MB against 581 MB | scale tables; golden |
| Lean scores the same | 3 pairs of 61-year runs, 23 scored keys: 0 values differ | `out/bench/p0/lean_proof.txt` |
| Parallel runs on the PC | 141 against 81 runs an hour at 3 at once | scale table |
| Node at 14 | 380 runs an hour on lean trees, against the PC's best of 139 | above |
| Tree arrays grow by 1.25x | plot25 peak 737 MB against 783; tree60 577 against 581; no slower | `out/bench/p0/mem125_hashes.json` |
| Result cache and finished runs | The screen's restarts lost only runs in progress: 58 already done at one, 408 at the last | `out/bench/node/disk_step/screen5.log`, and the session for the last |

## Plots with no save files, on the node

From `reports/reviews/2026-11-06_node_disk_report.md`.

| Check | Result |
|---|---|
| Plots 3, 4, 5, stopped run against fresh run, to age 30-35, 100 trees, 20 dead between them | Every yearly value identical (`tools/route_check.py years`) |
| Seed 1, resumed at 35 against straight, to 60 | 302 of 302 files identical |
| Seed 2, resumed at 35 against straight, to 60 | Every model number identical; 94 trees' `plot_seed` label wrong in the resumed run, since changed in `tools/plot.py` (`out/bench/node/disk_step/evidence/`) |
| Peak memory, 100 trees to 60, no save files | 6.1-6.7 GB a plot; lowest free memory on the node 64.8 GB (`out/bench/node/disk_step/evidence/usage.log`) |
| Time, no save files, sharing the node | 2,515-2,680 s a plot |
| Disk, finished plot with no save files | about 0.3 GB, against 2.7-3.7 GB with them |

## What's left, and why P0 stops here

The rule for P0: stop once every remaining idea gains less than 10 %. From the profiles (`out/bench/p0/profile_tree.md`, `_plot.md`, `_mesh.md`; one run each, on the worktree). **The gains here are estimates from those shares, not measurements.**

| Run | Largest shares of its time |
|---|---|
| Tree, 60 years | Light 55 %, carbon solve 14 %, mechanics 11 %, water 9 % |
| Plot, 25 trees, 20 years | Carbon solve 25 %, mechanics 23 %, light 21 %, shoot growth 10 % |
| Mesh, 30 years | Light 33 %, mesh export 32 % |

| Idea | Estimated gain on a tree | Why I'm stopping |
|---|---|---|
| Inverse FFT only for light layers something reads | About 7 %: about 30 % of layers, on about a quarter of the time | Under 10 % |
| A faster FFT library | Up to about 8 % of a run, if it stays bit-identical, which isn't known | Under 10 % |
| Faster carbon solve in compiled code | At most about 9 %, if it took no time at all, and only if arithmetic order holds | Under 10 % |
| Mechanics in compiled code | At most about 5 % of the time it owns | Under 10 % |

Together they might give 15-25 %, against 380 runs an hour already. That's little beside the M2 work waiting.

**Memory:** the 2 GB target isn't met, and I'm not chasing it now. The node has 94 GB and no plot needs more than 6.7 GB. Lossless steps left: writing history to disk without the pickle (the pickle was 78 % of a plot's disk at year 30), with no measured gain yet. **Largest plot in 6 GB, an estimate:** a plot's peak is about 0.4 GB plus an amount in proportion to trees; at 5.0 GB for 100 trees, 6 GB fits about 120 trees with save files. With no save files, a 100-tree plot already goes over, at 6.1-6.7 GB.

**Plots parallel within a year (B8): not done.** On a 5-plot ensemble the node already runs one plot per core, so its limit of 14 could gain at most 14/5 = 2.8x, in theory, with more memory. Trees in a plot share the light field, so it needs a real rewrite. Worth another look if M4's 1,000 m2 plots turn out too slow.

**A rewrite in C++ or Rust (E11), an estimate only.** Most of a run is already compiled code: FFT, the maths library and numpy. If all the rest took no time, the gain is about 1.5x. It'd take weeks, couldn't be bit-identical, and so would need a new baseline.

**A GPU (E12), an estimate only.** Only light's FFT and matrix work could move, about 35 % of a tree, so at most about 1.5x. The node has none. It'd change rounding, so it isn't lossless, and the grids are small enough that moving data would eat into it.

**Proposals needing the maintainer's approval, none recommended now.** Listed as asked; nothing's been done:
- **float32 for tree positions and directions:** at year 15 on 25 trees those six arrays hold about 197 MB (`out/bench/p0/profile_plot.md`), so about 98 MB less out of 823 MB. It changes rounding, so every result moves as if by a new seed and needs a new baseline.
- **Coarser light grid:** faster, but changes the light field itself; not measured.

**Second PC:** skipped by the maintainer (DECISIONS.md row 37). `WORKER.md` and the kit stay in the repo, unused.

## Found so far on the PC

**Parallel launching changes nothing:** hashes are identical alone and in a batch (`out/bench/m1/parallel_proof.txt`).

**Results depended on the maths library's thread count,** by up to 0.03 % at age 60 (`out/bench/m1/parallel_proof_one_thread.txt`). One thread per run is now the standard (DECISIONS.md row 26).
