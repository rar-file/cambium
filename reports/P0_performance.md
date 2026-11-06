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

Not yet compared with this PC: its golden runs come after the screen and M1. ARM and x86 may round differently.

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
- **The PC's own slowdown is still undiagnosed.** That needs its own diagnosis run, after its golden runs.

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
- **This PC tops out at about 3 at once.** 4 at once is no faster overall (126 against 130 runs per hour), so more cores wouldn't help as it stands. The cause isn't diagnosed yet.
- **One thread costs nothing measurable alone:** 47 s against 48 s.
- **The whole screen:** 161 runs in 5494 s, 105 runs per hour, 2.6 at once on average, against 77 per hour one at a time.

## Found so far on the PC

**Parallel launching changes nothing:** hashes are identical alone and in a batch (`out/bench/m1/parallel_proof.txt`).

**Results depended on the maths library's thread count,** by up to 0.03 % at age 60 (`out/bench/m1/parallel_proof_one_thread.txt`). One thread per run is now the standard (DECISIONS.md row 26).
