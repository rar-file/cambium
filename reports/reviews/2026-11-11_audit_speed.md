Model: Fable 5.2, ID `claude-fable-5-2`

# Speed audit: why generation is slow, and what would make it fast

2026-11-11. Independent review of one area, at master `b84ab90`; master has since gained only the design reports. Read-only apart from this file.

**How it was done**
- Read: `reports/P0_performance.md`, `reports/speed_research.md`, `reports/cpp_port_plan.md`, the design files of 2026-11-11, and the hot code (`light.py`, `growth.py`, `plot.py`, `fast.py`, `compact.py`, `structure.py`, `game_unreal.py`).
- Read saved runs on today's defaults: `node_f5_trees`, `node_f5_plots`, `node_cd2_C`, `node_c107_openC`. A plot's `plot.json` holds its time and peak memory by year. I also recomputed the earlier speed tests from their saved ensembles (`node_speed_t_*`, older settings).
- Ran two profiling jobs on the server, one core each, at `b84ab90`, with `tools/cpp_cost.py`. `node_audit_speed_tree`: a stand tree by stage, its top functions, the same tree with the two unapproved speed settings, and an export at four ages. `node_audit_speed_plot`: a 1,000 m² plot by stage. Both can be fetched with `tools/node/fetch.sh b84ab90 <label>`.
- Nothing ran on the PC. The server didn't ask for a sign-in check. It is a 16-core ARM machine with 94 GB; P0 measured one PC core at about twice one of its cores, which I didn't re-measure.
- CONFIRMED: I measured it, or read it in code or saved runs. SUSPECTED: an estimate, or carried from an earlier report on older settings.

## Verdict in plain words

1. There isn't one slow thing. There are three. A single tree in a stand is slow because of light. A forest plot is slow because most of its code is plain Python. An export is slow because of textures.
2. On one server core today: a 60-year stand tree takes about 1 minute, an open-grown one 2 minutes, a 1,000 m² forest to 60 about 50-55 minutes and 6.5 GB, and writing one age as game files 53-83 seconds.
3. Much of what feels slow isn't the growth model. Growing a stand tree to 60 and writing it at four ages took 58 + 4 + 286 = 348 s. Growth is 1 minute of the 6. Texture baking and PNG writing are 4.
4. A 1.5x gain for single trees is built and tested. It has waited for a decision since 2026-11-07, because it changes rounding.
5. No tuning of this model will make old trees appear on demand in a game. Everything on my list together is worth about 5x. The need is 5-10x for birch alone, and far more with other species. That takes trees grown ahead and replayed, or the lighter far-tree model, which doesn't exist yet.
6. The C++ port should still wait. Its own plan puts it at 1.3x on a stand tree, and `treegen/` has had 84 commits since that plan measured it.

**Score for this area: 5 / 10.** The measuring is professional. The product is still slow for both audiences, and gains already measured aren't adopted.

## 1. How slow it is

Today's defaults, which have the six lossless speed settings on. Server, one core for each run. CONFIRMED, except the cells marked as estimates.

| Run | To 30 | To 50 | To 60 | Peak memory at 30 / 50 / 60 | Source |
|---|---|---|---|---|---|
| Stand tree, seed 1, quiet server | 9 s | 40 s | 58 s | 0.42 / 0.69 / 0.76 GB | my job |
| Stand trees, 20 seeds, up to 5 at once | not saved | not saved | 74 s (63-80) | not saved | `node_f5_trees` |
| Open-grown trees, 10 seeds, lean | about 18 s (estimate) | about 74 s (estimate) | 122 s (114-130) | 1.36 GB at 60 (1.26-1.49) | `node_c107_openC` |
| Forest plot, 1,000 m², 20 plots, up to 8 at once | 1,545 s | 2,726 s | 3,275 s (3,034-3,465) | 4.0 / 5.9 / 6.5 GB | `node_f5_plots` |
| The same kind of plot alone, seed 1, with timers | 1,516 s | 2,544 s | 2,982 s | 4.0 / 6.3 / 7.5 GB, with the profiler's records | my job |
| Export of the tree at that age: every level, with textures | 69 s | 81 s | 83 s | 3.1 / 3.6 / 3.6 GB | my job |

- An export at age 10 takes 53 s and 2.6 GB.
- The first run after an install adds about 5 s once, to compile: year 1 took 6.2 s cold and 1.0 s warm.
- No saved run or profiler times an open-grown tree by year (`cpp_cost.py` and `speed_profile.py` only grow stand trees). The two estimates use section 2's rates per grid cell and per living node on these trees' saved sizes. The same sum gives 115 s to 60 against the 122 s measured. SUSPECTED.
- A plot gives 47 living trees at 60, so about 70 s per surviving tree: no cheaper per old tree than a stand tree.

## 2. Where the time and memory go

### A stand tree (seed 1; seconds in that one year)

| Stage | Age 10 | Age 30 | Age 50 | Age 60 | Share of the run | Already compiled |
|---|---|---|---|---|---|---|
| Light: the field | 0.053 | 0.382 | 1.082 | 1.158 | 57.5 % | 51 % |
| Carbon solve | 0.004 | 0.136 | 0.268 | 0.227 | 15.7 % | 74 % |
| Mechanics | 0.000 | 0.030 | 0.068 | 0.062 | 6.2 % | 86 % |
| Light: reading it | 0.005 | 0.051 | 0.088 | 0.085 | 5.5 % | 14 % |
| Shoots | 0.013 | 0.065 | 0.074 | 0.052 | 4.9 % | 18 % |
| Roots | 0.015 | 0.044 | 0.074 | 0.083 | 4.9 % | 27 % |
| Water, rings, shedding, stats | 0.003 | 0.047 | 0.109 | 0.120 | 5.3 % | about 10 % |
| **All** | **0.094** | **0.755** | **1.763** | **1.787** | 100 % | **50 %** |
| With `light_rows` and `drop_dead` | 0.068 | 0.523 | 1.090 | 1.099 | | 62 % |
| Crown nodes, living of all held | 437 of 483 | 24,908 of 58,351 | 40,936 of 190,507 | 38,400 of 229,960 | | |
| Light grid, cells | 94 x 94 x 40 | 126 x 126 x 184 | 189 x 189 x 258 | 189 x 189 x 280 | | |
| Model state, MB (with dead nodes dropped) | 2.2 (2.2) | 23.0 (12.7) | 83.1 (32.6) | 103.7 (30.2) | | |

- **Light is a place's cost, not a tree's.** It is 0.12-0.15 microseconds per grid cell a year at every age. A single stand tree solves a cell of 16 trees (`stand.cell_trees: 4`) at 0.1 m: 10 million cells and 60 directions at 60.
- **Three lines are 64 % of an old tree's year:** the sweep's multiply, weighted sum and FFTs (`light.py:349-352`), 1.11 of 1.73 s at 60 under the profiler.
- **Everything else follows living nodes:** about 10-12 microseconds per living node (crown and roots) a year from age 30. On a 10-year tree it is 70, because Python's cost per call rules there. Shedding alone is 1 % of the run.
- **An open-grown tree is a different case.** At 60 seed 1 has 262,852 living crown nodes, seven times a stand tree's. By the same two rates, light is a third of its year and node work two thirds, so `light_rows` helps it less and compiled growth more. SUSPECTED.
- **Old years cost most.** Years 31-60 are 48 of the 58 s. Light is 62 % of those.
- **Node count.** Living crown nodes level off near 40,000 from age 40. Held nodes keep growing by about 4,900 a year, so at 60 five in six are dead. The living ones are mostly twigs (an earlier report: 7 % are wood over 1 cm), so merging old internodes would gain little.
- **The carbon solve** runs its whole-tree sum 93 times a year at 60 (122 at 30): two solves, each landing on the exact bits of a 40-step bisection (`fast.py:574-640`).
- **Memory.** Of the 0.76 GB peak, about 0.3 GB is Python and its libraries, 0.10 GB the tree (0.03 GB with dead nodes dropped), 0.05 GB the light and soil grids it keeps, and the rest the sweep's working grids.

### A forest plot (seed 1; seed spread was on, as in the port plan's profile, and no recruit came up; seconds per tree in that one year)

| Stage | Age 10 | Age 30 | Age 50 | Age 60 | Share of the run | Already compiled |
|---|---|---|---|---|---|---|
| Carbon solve | 0.0036 | 0.059 | 0.229 | 0.323 | 24.5 % | 47 % |
| Shoots | 0.013 | 0.056 | 0.093 | 0.111 | 24.4 % | 10 % |
| Roots | 0.0085 | 0.032 | 0.052 | 0.073 | 16.7 % | 7 % |
| Shedding, rings, stats | 0.0014 | 0.019 | 0.064 | 0.091 | 8.3 % | 10 % |
| Light: reading it | 0.0013 | 0.018 | 0.059 | 0.077 | 7.7 % | 0 % |
| Water | 0.0018 | 0.013 | 0.034 | 0.048 | 6.5 % | 5 % |
| Mechanics | 0.0003 | 0.012 | 0.060 | 0.084 | 5.5 % | 75 % |
| Light: the shared field | 0.0004 | 0.0081 | 0.053 | 0.074 | 4.5 % | 56 % |
| Thinning, seed spread, damage, the rest | 0.0006 | 0.0044 | 0.0082 | 0.012 | 1.9 % | 0 % |
| **All** | **0.031** | **0.221** | **0.653** | **0.924** | 100 % | **23 %** |
| Trees stepped; the whole plot's year, s | 1,485; 45 | 316; 70 | 66; 43 | 50; 46 | | |
| Crown nodes, living of all held | 0.42 of 0.48 million | 3.08 of 5.91 million | 2.69 of 9.06 million | 2.66 of 10.34 million | | |
| A tree's step: fixed part, s, plus microseconds per living node | 0.019 + 28 | 0.077 + 10 | 0.074 + 10 | 0.094 + 9 | | |
| Model state per tree, MB (node arrays of living nodes alone) | 0.2 (0.1) | 8.7 (3.1) | 56.9 (12.9) | 87.4 (18.3) | | |

- **Tree steps are 92 % of the time.** The shared light field is under 5 %: light is cheap once many trees share it.
- **Only 23 % of the run is in compiled code,** against 50 % for a stand tree. To year 20 it is 6 %.
- **Young years are costly.** The first 20 years take 893 s, 30 % of the run: up to 1,500 small trees at 0.03-0.06 s each, mostly Python's cost per call.
- **In old trees the carbon solve leads:** 0.32 of 0.92 s a tree at 60.
- **Memory.** The peak is 6.5 GB on the 20 saved plots (7.5 GB here, with the profiler's own records). The model state is 87 MB a tree at 60, 4.3 GB in all, and 67 % of its node arrays hold dead nodes. So dropping them should now save more than the 27 % measured earlier.
- **Slower than four days ago.** 2,982 s against 2,513 s at `5f07fae`, same seed and tool. The model changed, not the code's speed: the plot now holds 10.3 million crown nodes at 60 against 6.5 million then.

### An export (one stand tree, all levels, summer; seconds for that age)

| Part | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| Geometry: wood, leaves, stem relief, both levels | 0.2 | 3.9 | 8.5 | 9.4 |
| Texture baking: bark, roots, leaf atlases, far sheets | 29.8 | 38.5 | 44.6 | 44.8 |
| Writing the textures as PNG | 21.6 | 21.5 | 22.2 | 21.9 |
| Everything else | 1.8 | 4.8 | 6.1 | 6.6 |
| **All** | **53.4** | **68.8** | **81.3** | **82.7** |
| Triangles, nearest level; files, MB | 25,845; 47 | 1,127,957; 145 | 2,181,242; 237 | 2,301,350; 246 |

- Geometry is 0.4-11 % of an export, about 4 microseconds a triangle. Textures are 81-96 %, and cost 51-67 s whatever the tree's size.
- A 10-year sapling grows in half a second and takes 53 s to export.

## 3. What users need, and the gap

Game figures are from `reports/cpp_port_plan.md` sections 3.1 and 3.4. I didn't open the game.

| User | Needs | Today | Gap |
|---|---|---|---|
| Game, trees grown ahead | Thousands of unique trees: 4,222 mature birches in reach | 58-74 s a tree: about 70-85 core-hours, 8-10 hours on the server | None in time, for birch. In disk, yes: 246 MB a tree at full detail is 1 TB, so baked trees must be kept as skeletons, not meshes |
| Game, trees on demand | 1-2 birches a second at walking pace: 3-6 core-seconds a tree on 6 workers | 58 s on a server core; about 30 s on a PC core (SUSPECTED) | 5-10x for old birches. More with other species, or running |
| Game, steady growth | One step per tree per game year (61 real days) | 1-2 s a tree-year | None: under 1 % of a core |
| Looking at a tree | Seconds | 2.4 minutes for one age, 5.8 minutes for four; then 108 s to import one into Unreal (game audit) | 20-50x |
| Science, tree ensembles | 20 trees in minutes | 25 core-minutes: about 3 minutes on 16 cores | None |
| Science, plot ensembles | 20 plots within the hour | 18 core-hours: 2.5-3 hours, held back by 6.5 GB a plot | 3-5x |
| This round's design plan | 140-180 plots and about 210 single trees (`reports/design/2026-11-11_plan.md`, section 5) | 21-27 server hours, at 8 plots at once because of memory | What slow plots cost this round |

## 4. Findings, most serious first

- **S1. There is no fast way to get a tree: every tree is grown in full.** High. Effort L. CONFIRMED.
  - Where: `treegen/` has no far form or lighter model. Replay is on branch `replay`, unmerged, 18 commits behind master.
  - Why: a game can't wait 30-60 s for each old tree. Rows, threads, a tolerance solver and C++ together give about 5x, not 50x.
  - Fix: decide the route now. Grow each tree ahead on the server, keep its skeleton and history, replay it in the game, and switch a tree to live growth when it is cut.
- **S2. Forest plots run mostly as plain Python.** High. Effort L (M for the first pieces). CONFIRMED.
  - Where: `growth.py:2606` `_grow_shoots`, `roots.py:479` `_grow`, `light.py:127` `own_shade`, `:404` `sample`, `:453` `optimal_direction`, `hydraulics.py:55` `solve`, `growth.py:1126` `flow`, `structure.py:173` `trunk_chain`.
  - What: 23 % of a plot's run is in compiled code, against 50 % for a stand tree. Shoots and roots are 41 % of the run and under 10 % compiled.
  - Why: plots are where the science is judged, and each 20-plot test costs 18 core-hours. Memory already bends the science: the cell that limits recruits is labelled "memory, not biology" (`species/betula_pendula.yaml:1193`; the science audit's H5).
  - Fix: compile in order of share: shoots, roots, light reads, water. Start with the small exact ones: `trunk_chain` walks the stem in a Python loop and is called from 14 places, about 16 times a tree-year. A cheap path for seedlings (0.03 s a seedling-year today) is also what the science audit's fix for H5 needs.
- **S3. Exports spend 81-96 % of their time on textures.** High. Effort S. CONFIRMED (times); gains SUSPECTED.
  - Where: `game_unreal.py:115` (PNG at compression level 6); `:1246-1254` (the leaf, card and bark-strip atlases, 9 of the 21 PNG files a stage, are rebuilt and rewritten for every age from the look and the texture seed alone); `game.py:548` (far sheets).
  - Why: this is most of the wait before anyone sees a tree. The game audit (G9, G10) read the same from the plan's older table; this is it measured at master.
  - Fix: PNG level 1-3; build the species' atlases once; export ages in separate processes where memory allows (3.6 GB each); a geometry-only option for quick looks.
- **S4. A measured 1.5x for single trees sits unadopted.** Medium. Effort S. CONFIRMED.
  - Where: `species/betula_pendula.yaml:2383`, `:2385` (`light_rows`, `drop_dead`). DECISIONS 91 records them as not settled; `QUESTIONS.md` has no open item for them. Why: every single-tree run costs half as much again as it needs, and memory holds plots to about 12 at once.
  - What: today, seed 1: 58 to 38 s, peak 759 to 603 MB. I recomputed the accuracy tests from the saved ensembles, on two older settings sets: 100 trees against 80, 28 rows at 50 and 60. Where the curve drives height, as today, nothing is over z 0.8. Where it didn't, the largest is z 1.6: height 0.9 % lower, in both draws of 20 seeds, so worth watching. Dropping dead nodes alone, 20 against 20: means equal to three digits.
  - Fix: test both on today's defaults (20 trees and 5 plots a side). Then adopt them with the first model change that needs a new baseline anyway.
- **S5. Every speed change must match the old bits, and that now costs speed.** Medium. Effort S-M. CONFIRMED (code); gain SUSPECTED.
  - Where: `fast.py:574-640` (the solver replays 40 halvings: 93-122 whole-tree sums a tree-year); `fast.py:113-170` (numpy's summing order rebuilt by hand).
  - Why: a solver to a tolerance needs about 20 sums. In old plot trees the solve is the largest stage.
  - Fix: write down that same-maths changes pass by the ensemble test (`tools/speed_accuracy.py`), and batch them into planned new baselines.
- **S6. A single stand tree pays for the light of 16.** Medium. Effort M. CONFIRMED (cost); gains SUSPECTED.
  - Where: `species/betula_pendula.yaml:1296` (`cell_trees: 4`), `:366` (`voxel_size: 0.10`), `light.py:347-354`. Why: that field is 58 % of every single-tree run.
  - Fix, in order: `light_rows`; threads over its independent rows; then test a 3 x 3 cell (0.56 of the cells) and a 0.15 m grid (0.30) on today's defaults, 20 seeds each.
- **S7. A plot uses one core.** Medium. Effort M-L. CONFIRMED (code); gain SUSPECTED.
  - Where: `plot.py:397-405`. Tree steps are 92 % of a plot's time. Each only reads the year's shared light and soil and draws from its own random streams. Plot-level draws come after (`plot.py:407-417`). Why: one forest takes 55 minutes on a machine with 16 cores.
  - Fix: step trees in worker processes. One plot would finish several times sooner. An ensemble that already fills the cores gains nothing.
- **S8. Runs that can export carry every dead node.** Medium. Effort M. CONFIRMED.
  - Where: `compact.py:23`: only lean runs can drop them, and a lean run can't export. A 60-year stand tree holds 229,960 crown nodes, 38,400 alive. Why: every tree that is exported pays in memory and time for nodes only a replay reads.
  - Fix: move dead nodes to a side store that exports read, so every run walks living nodes only.
- **S9. No draft quality, no batch call, no published timings, no speed check.** Medium. Effort S. CONFIRMED.
  - Where: `cambium/_tree.py:219`, `cambium/cli.py:56-88` (one seed a call); `docs/site/forests.md:94-96` ("much longer", no figure); `.github/workflows/tests.yml` (no timing); `tools/golden.py:16` (times recorded, never checked). Why: a user can't plan a run, has to write their own process pool for many trees, and a slowdown would pass every check.
  - Fix: a labelled draft preset for looking only, never scored; `--seeds` and `--workers`; section 1's table in the docs; a nightly time bound (the tests audit's T6).
- **S10. Smaller points.** Low. Effort S. CONFIRMED.
  - `treegen/fast.py:1` says the speed settings are "all off by default". Six are on (also the code audit's D1).
  - `species/betula_pendula.yaml:363-365` says 0.1, 0.15 and 0.2 m grids "give the same light distribution". The saved test ensembles say otherwise: crowns at 60 are 2 % wider at 0.15 m and 12 % wider at 0.2 m (recomputed).
  - The cost tables in `reports/cpp_port_plan.md` are for `5f07fae`. Plots have grown a fifth slower since (2,982 s against 2,513 s to 60, same seed and tool). Regenerate the tables before anyone plans from them.
  - Results come back from the server in 1.5 MB parts (`tools/node/fetch_examples.sh`); that wait isn't timed anywhere.
  - No profiler grows an open-grown tree, the public default (`cambium/_tree.py:219`, `stand=False`) and the slowest case. By section 2's rates its time is mostly node work, not light. SUSPECTED.

## 5. The options, ranked

"Bits" is the risk to bit-identical results. Speed-ups are for a 60-year run unless said. M = measured by me today; E = earlier report; S = my estimate (SUSPECTED).

| # | Option | Speed-up | Effort | Bits |
|---|---|---|---|---|
| 1 | Export: faster PNG, atlases once, ages in parallel | Four ages 286 s to about 215 s of work, about 65 s of waiting on four cores (S) | S | Growth untouched. PNG files differ, pixels the same |
| 2 | Adopt `light_rows` and `drop_dead` | Stand tree 1.5x (M); less on an open-grown tree (S). Plot 1.1x and 27 % less memory (E, one plot, re-read), so 16 plots fit at once, not 12 | S | New rounding once: a new baseline. No shift over z 1.6 on 100 trees against 80 (recomputed, older settings) |
| 3 | Draft preset for looking: 0.15 m grid, 24 directions, rows | Stand tree about 2.5x: 58 to about 23 s (S, from E) | S | A different tree, never scored. Not 0.2 m: it widened crowns by 12 % at 60 (recomputed), and the look is what is being judged. 0.15 m widened them by 2-3 % (z 1.9, recomputed, older settings) |
| 4 | Threads over the rows sweep and its FFT layers | Another 1.2-1.5x on one tree at 4 threads (S; the sweep alone gained 3.2x on 8 in E) | S-M | None beyond option 2, if rows stay independent: to prove. Needs an exception to the one-thread rule (DECISIONS 26) for compiled routines shown not to depend on thread count |
| 5 | Compile the small exact pieces for plots: `trunk_chain`, level lists, `flow`, `own_shade` | Plot about 1.1x: they are 8-12 % of a plot's year (M) | S-M | None for the integer walks. `own_shade` sums need care |
| 6 | Carbon solve to a tolerance | Solve 3-5x: stand tree 1.1x, plot 1.2x (S) | S-M | Last digits change: a new baseline |
| 7 | Compile shoots, roots, light reads, water | Plot 1.5-2x; the measured ceiling was 4.5x (E) | L | None if copied operation for operation. A copy drifted from the model once (E) |
| 8 | Step a plot's trees in parallel | One plot up to 7x in waiting time on 16 cores (S): tree steps are 92 % of it (M). No gain for full ensembles | M-L | None expected: read-only shared fields, own random streams |
| 9 | Side store for dead nodes | Export runs and plots: about 10 % time, 25-40 % memory (E) | M | As `drop_dead` |
| 10 | Smaller stand cell (3 x 3) or 0.15 m grid | Light 1.8x or 3.4x: stand tree 1.3x or 1.5x after rows (S) | S to test | Lossy: coarser grids widen crowns (2-3 % at 0.15 m, 12 % at 0.2 m, older settings). 20 seeds on today's defaults first |
| 11 | Grow once, replay | Growth costs nothing while playing. 70-85 core-hours once for 4,222 birches (M). As built on the branch one tree is 610 MB (game audit, G8): it must replay a skeleton, about 0.1 MB a tree | L | None: a view of an exact run. A replayed tree can't answer a cut; a stand tree can be regrown from its seed when that happens, a plot tree only with its whole plot |
| 12 | Lighter far-tree model | The game's far trees. About a tenth of the nodes (E) | L | A new model, checked against the full one |
| 13 | C++ port | Stand tree 1.3x, plot 2.5-3x (E, estimates) | L: 100-170 agent-days with the game side (E) | Lost. New baseline, and two models to keep in step |
| 14 | Single precision; GPU light | Memory -33 %, time -6 % (E); tree at most 1.5x (E) | M; L | Lost |

Together, options 2, 4 and 6 would take a stand tree from 58 s to about 25 s on four cores, with no change to the model's rules. SUSPECTED.

## 6. Quick wins and big jobs

- **Quick wins, days each:** options 1, 2, 3 and 5; and from S9, `--seeds` and `--workers`, a timing table in the docs, and a nightly time check.
- **Middle jobs, a week or two each:** options 4, 6, 9 and 10.
- **Big jobs, weeks each:** the game's route, grown ahead and replayed with the lighter far model behind it (options 11 and 12); plots, compiled then parallel (options 7 and 8); and C++ (option 13), only when the model's logic has stopped moving, as its own plan says.
- **The order I'd take them in:** 1, then 2 and 3, then 5 and 4, then the decision on the game's route.
- **What the quick wins buy (SUSPECTED):** a look at a 60-year stand tree in about 30 s (draft growth, geometry only) instead of 2.4 minutes; a full-quality tree at four ages in about 2 minutes instead of 6.

## 7. On the four design tracks

- I don't disagree with any of them. They are about what is true, which comes first. Their plan budgets 140-180 plots and about 210 single trees: 21-27 server hours. It runs 8 plots at once because each needs 6.5 GB; with dead nodes dropped, 12 or more would fit.
- Every arm is paired with a control that matches bit for bit, so speed settings can't change mid-round. The clean moment to adopt `light_rows` and `drop_dead` is with the first accepted model change, when a new baseline is needed anyway.
- The plan allows 15 minutes for a stand tree with the new limb logs, against 62-80 s without. Time one tree with the logs first (`tools/cpp_cost.py tree`): logging shouldn't cost more than growing.
- One difference of order: I would fix the export before the next round of pictures. The owner judges by pictures, and each one costs minutes it doesn't need.

## 8. What's genuinely good

- **The measuring.** Three reports, every figure with its source, timers shown by digest not to change results, guesses marked as guesses, and their own corrections listed.
- **The six lossless settings.** About 2x on trees and 2.8x on plots, proven identical on four golden runs on two machines, and now the defaults. Single trees haven't slowed since: 67 s at `5f07fae`, 58 s today.
- **`light_rows` is real algorithm work:** the same sums in an order that fits the processor's cache, 5x on the sweep.
- **The port plan is sober.** It ported six pieces and timed them before promising anything, and it says not to start.
- **The run tooling.** Lean runs, save and resume, a memory-aware batch runner, one maths thread for repeatable results, growing once for several ages (`stages`, and `--state` in `tools/game_export.py`), and `cpp_cost.py` still worked 84 commits later.

## 9. Not checked

- Anything on the PC, in Unreal, or in the game's project.
- `light_rows` and `drop_dead` on today's defaults: one seed only, for time. Their accuracy on plots (5 plots) is carried from earlier reports; no such plots are saved where I could read them.
- Every gain marked S or SUSPECTED: none was tried. And each of my profiles is one seed; earlier reports found seeds differ by up to 10 % in time.
- An open-grown tree by stage: no tool does it.
