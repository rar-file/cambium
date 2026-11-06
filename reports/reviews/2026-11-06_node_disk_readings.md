# The node's readings behind the disk step

Copied from command output in the session, 2026-11-06, node clock. Commands: `df -h ~` or `df -BM ~`, `du -sm`, `ls -la`, `free -g`, `tools/node_limit.py`. They weren't logged to a file at the time. From 03:52 on, `~/origin/usage.log` records free disk and free memory every minute.

| Time | Free disk | Used | Size | Plots then |
|---|---|---|---|---|
| Earlier, first look | 32 GB | | 96 GB | none (`reports/P0_performance.md`) |
| 03:00:54 | 17 GB | 80 GB, 83 % | 96 GB | year 15-20 |
| 03:04:35 | 19 GB | 78 GB, 81 % | | year 25 |
| 03:07 | 14 GB | 83 GB, 87 % | | year-25 checkpoint |
| 03:09:34 | 18,561 MB | 79,545 MB, 82 % | 98,122 MB | year 30 |
| 03:11:40 | 18,245 MB | 79,861 MB, 82 % | | |
| 03:13:03 | 13,132 MB | 84,975 MB, 87 % | | year-35 checkpoint |
| 03:13:31 | 10,663 MB | 87,444 MB, 90 % | | year-35 checkpoint; the lowest seen |
| 03:14:52 | 14,218 MB | 83,888 MB, 86 % | | |
| 03:16:09 | 13,816 MB | 84,291 MB, 86 % | | |
| 03:16:55 | 15,792 MB | 82,315 MB, 84 % | | plots stopped and resumed |
| 03:25:24 | 15,836 MB | 82,270 MB, 84 % | | |
| 03:37:46 | 17,003 MB | 81,104 MB, 83 % | | plots 1, 2 done |
| 03:38:21 | 29,860 MB | | | my leftovers deleted (`~/origin/deleted.log`) |
| 03:49:48 | 29,845 MB | 68,262 MB, 70 % | | |

**Plots' use at 03:09:34 (year 30):** all five together 11,860 MB (`du -sm`). `checkpoint.pkl` at 03:09: 1,859, 1,794, 1,901, 1,903, 1,941 MB as bytes shown by `ls` (1,859,259,661 and so on). At year 20: 1.57-1.77 GB. A whole plot at year 20: 1.9 GB.

**`~/origin` in total at 03:02:** 12 GB, of which `out/bench/ensemble/base_plots` 9.5 GB, golden 957 MB.

**The PC's finished plots, whole folder and pickle:** `out/bench/p38_nat` 2.7 GB (pickle 2.51 GB), `out/bench/p33_nat` 3.7 GB (pickle 3.52 GB).

**CPU used by others, one-minute average (`tools/node_limit.py`):** 03:00: 0.19 cores, limit 14. About 03:19, when the screen restarted: not shown, but the screen's log says up to 3 at once with 5 reserved, so the limit read 8, above 1 core. 03:29: 0.24 cores, limit 14.

**Memory at the node, `free -g`:** 03:00:54: 94 total, 16 used, 77 available. 03:13:31: 22 used, 71 available. 03:16:55: 16 used, 77 available. 03:49:48 (`free -m`): 21,741 MB used, 74,611 MB available.

**Plots' peak memory, from their logs (`out/bench/node/disk_step/base_plots_N.log`):** plot 1, 5,622 MB and plot 2, 5,397 MB, each counting only the part after its resume at year 35. Plots 3, 4, 5 with no save files: 4,998, 4,639, 4,716 MB at year 40, still rising.

**Proof's peak memory (`out/bench/node/ckpt_proof.log`):** plain 988 MB, none 990 MB, resumed 962 MB (plot25, 25 trees, to year 20). No difference there.

**Scripts as run:** `out/bench/node/disk_step/node_ckpt_proof.sh`, `node_plots_nockpt.sh`, `node_plots_fresh.sh`, `node_cleanup.sh`. The proof's "stopped" run was killed as soon as a poll every 2 seconds saw `plot.json` at year 10 or later.

**Running on the node at 03:49, with nice values and arguments:** `out/bench/node/disk_step/running_listing.txt`. All at nice 19.

**The node's code:** `out/bench/node/disk_step/code_hashes.txt`: SHA-256 of all 24 Python files in `treegen/`, `cli.py`, `tools/plot.py`, `tools/ensemble.py`, `tools/batch.py` on the node, checked against `git archive 68782d9` here: 24 of 24 match. `repo/COMMIT` says `68782d9`.
