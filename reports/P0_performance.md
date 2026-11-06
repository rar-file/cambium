# P0: Performance (in progress)

Started 2026-11-06. The full report comes when P0 finishes; this holds what's measured so far.

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

Compared with this PC below: they differ, as ARM and x86 round differently.

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

Recorded twice at master `bc723ee`, one at a time, one maths thread, kernel `Haswell`. **All 225 files were identical between the two recordings** (`out/bench/golden/pc_base`, `pc_base_rerun`). Peak memory is each run's own record; `hashes.json` for these two says 4.5 MB, which was the venv's launcher, now fixed (`tools/golden.py`, `peak_of_run`).

| Run | Seconds, first / second | Peak MB, first / second | Files |
|---|---|---|---|
| tree60 | 45.7 / 47.5 | 581 / 581 | 3 |
| mesh30 | 14.6 / 14.6 | 385 / 388 | 13 |
| plot25 | 71.6 / 69.3 | 782 / 786 | 76 |
| regen10 | 23.9 / 22.9 | 402 / 400 | 133 |

## This PC against the node

**Same code, same seed: every one of the 225 files differs** (`tools/golden.py compare pc_base out/bench/node/node_a_hashes.json`). Crown width first differs at year 2, and other outputs from year 3. It's the same chaos as a tiny parameter change, set off by rounding between chips.

**Seed 1, node minus PC** (`out/bench/node/golden_tree60/stats.json`):

| Age | Height (m), PC / node | DBH (cm), PC / node | Leaf area (m2), PC / node | Diffuse light (%), PC / node |
|---|---|---|---|---|
| 20 | 15.20 / 14.77 | 14.19 / 13.61 | 18.6 / 15.9 | 50.8 / 53.8 |
| 30 | 19.97 / 19.98 | 18.76 / 18.38 | 46.9 / 46.2 | 45.8 / 40.2 |
| 40 | 23.09 / 23.48 | 22.97 / 23.23 | 61.1 / 60.9 | 34.3 / 35.2 |
| 50 | 25.02 / 25.04 | 26.05 / 27.05 | 66.4 / 63.3 | 30.3 / 31.6 |
| 60 | 26.11 / 26.51 | 28.86 / 29.35 | 65.6 / 65.2 | 29.8 / 30.0 |

**Largest difference in any year:** leaf area at year 17, 10.5 against 25.3 m2, +142 %. From age 20 on, in the scored metrics: LAI at year 24, +27 %.

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

The largest gap between means is LAI at 50: 0.21, about 1.8 standard errors of an unpaired difference, on one of nine rows. These can't be paired, because the same seed is a different tree on each chip. **So a seed's tree belongs to its machine, while the ensemble's verdict doesn't depend on which of these two ran it.** Comparisons still stay on one machine, as PROTOCOL.md section 6 says.

## Why runs slow each other down on the PC

The maintainer asked which of these explains it: memory bandwidth, disk, paging, cores or clock speed.

**Like for like:** lean trees, seed 1, each group once, all hashes the same, with little else running on this PC (`out/bench/p0/scale_unpinned.md`, `scale_pinned.md`, in the worktree).

| Runs at once | Free to move: mean run time (s) | Runs per hour | Each on its own core: mean run time (s) | Runs per hour |
|---|---|---|---|---|
| 1 | 44.2 | 81 | 45.4 | 79 |
| 2 | 57.2 | 126 | 62.5 | 115 |
| 3 | 76.4 | **141** | 89.2 | 121 |
| 4 | 112.8 | 128 | 161.2 | 89 |
| 5 | 167.2 | 108 | 174.8 | 103 |
| 6 | 221.1 | 98 | 224.7 | 96 |

**More than 3 at once is slower overall, not just no faster.** Peak memory per run stays near 440 MB.

**A correction:** the first diagnosis had 2 at once at 1.73x-1.75x free to move and 1.15x pinned (`parallel_diagnosis_first.md`), so I told the maintainer pinning looked like the fix. It isn't. In the like-for-like test pinning is no better at any level, and worse at 3 and 4. The same case, lean with 2 at once, took 74.4 s in one test and 57.2 s in another, so a single group can move about 25 %. Read these tables as a shape, not to the second.

| Possible cause | Verdict | Evidence |
|---|---|---|
| Disk | No | Lean runs write about 0.1 MB/s and still slow each other |
| Paging | No | Lean at 2 at once: under 1 hard fault a second |
| Clock speed | No | 4,590-4,610 MHz in every case |
| Cores | No | 8 physical cores, and throughput falls after 3; pinning doesn't help |
| **Memory bandwidth, and the shared cache** | **Most likely** | Benchmark below. By elimination and from the benchmark: Windows can't show bandwidth directly |

**The benchmark, speed per copy against 1 alone:** in a core's own cache, 0.97x at 4 copies. In the shared cache, 0.94x at 2 and 0.38x at 4. In memory, 0.50x at 2 and 0.24x at 4: one copy alone already uses the whole 17 GB/s, and more copies split it.

**What would fix it:**
- **For now, at no cost:** at most 3 at once on this PC. Batch work is on the node anyway.
- **A second stick: an estimate, not a measurement.** It would double memory bandwidth, but not the shared cache, which limits from about 4 copies. So I'd guess 1.5-2x on throughput, about 200-280 runs an hour against 141. The maintainer's second slot doesn't work at the moment, so it may need more than a stick. The campaign doesn't need it: the node does 280-380 an hour.

## The merges

19 commits from `p0-perf`, one at a time. Those touching `treegen/`, `cli.py` or `tools/plot.py` needed all tests and all four golden runs identical to `pc_base`, or the merge was aborted. **None was aborted, and none conflicted.** Raw: `out/bench/p0/merges/`.

| Commit | What | Model paths? | Tests | Golden |
|---|---|---|---|---|
| `f92ea8c` | Lean mode | yes | 63 pass | identical |
| `41abb3b` | Checkpoints | yes | 71 pass | identical |
| `43ead90` | Worker kit, lock file | yes | 76 pass | identical |
| `0b98044` | Linux support | yes | 81 pass | identical |
| `68782d9` | Ensembles, paired comparison | yes | 90 pass | identical |
| `b64f75a` | Resume after any stop | yes | 98 pass | identical |
| `95233fc` | Node tools, golden memory | yes | 102 pass | identical |
| 12 others | Tools and reports only | no | not run for each; 102 pass at the tip | not needed |

**None of these makes a default run faster:** tree60 43-47 s against 45.7 s, plot25 68-70 s against 71.6 s, within what a run moves. **Their gain is in how they're used:**

| Change | Measured gain | Source |
|---|---|---|
| Lean mode | 44 s against 47 s alone; the seed-1 tree's peak 440 MB against 581 MB | scale table; golden |
| Parallel runs on the PC | 141 against 81 runs an hour at 3 at once | scale table |
| Node at 14 | 380 against 141 runs an hour | above |
| Result cache | reused 30 cases on the first node restart; later restarts lost only runs in progress | `~/origin/screen5.log` |

## Plots with no save files, on the node

From `reports/reviews/2026-11-06_node_disk_report.md`.

| Check | Result |
|---|---|
| Plots 3, 4, 5, stopped run against fresh run, to age 30-35, 100 trees, 20 dead between them | Every yearly value identical (`tools/route_check.py years`) |
| Seed 1, resumed at 35 against straight, to 60 | 302 of 302 files identical |
| Seed 2, resumed at 35 against straight, to 60 | Every model number identical; 94 trees' `plot_seed` label wrong in the resumed run, now fixed |
| Peak memory, 100 trees to 60, no save files | 6.1-6.7 GB a plot; lowest free memory on the node 64.8 GB (`~/origin/usage.log`) |
| Time, no save files, sharing the node | 2,515-2,678 s a plot |
| Disk, finished plot with no save files | about 0.3 GB, against 2.7-3.7 GB with them |

## Found so far on the PC

**Parallel launching changes nothing:** hashes are identical alone and in a batch (`out/bench/m1/parallel_proof.txt`).

**Results depended on the maths library's thread count,** by up to 0.03 % at age 60 (`out/bench/m1/parallel_proof_one_thread.txt`). One thread per run is now the standard (DECISIONS.md row 26).
