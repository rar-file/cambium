# Speed research

**Status: tree results are complete; plot accuracy isn't.** I was asked to hand back while the plot ensembles were still queued, so nothing that changes neighbour light has passed its plot test yet. "How to finish" below has the commands. Nothing here is switched on, and no default or golden hash changed.

## The answer

- **Without changing a single number:** a tree to 60 runs about 2x faster, and a 100-tree plot to 60 about 2.8x (one run each way).
- **With the same maths in another order, which changes rounding (needs the maintainer's approval and a new baseline):** about 3x on a tree, measured on the PC, with no shift beyond noise across 80-100 trees. Plots aren't checked yet.
- **The maintainer's 4 s:** not reached. The best time with no shift shown is 17 s on one core. A C++ port might bring that to about 9-11 s (a guess). 4 s would probably also take several cores or a coarser light grid, and the coarser grid I tested at 0.2 m moved crowns on the default settings.
- **Live forest:** time isn't the limit; memory is. 15,000 trees at 0.23 s a tree-year is about an hour of one server core per game year, against 61 real days. At 38-43 MB a tree they'd need about 600 GB.

## Each idea

All times are 60-year lean trees. Times on one machine are comparable only with others in the same column. Every row from dropping dead nodes down also has the lossless set on, and each row below that also has `light_rows` and `drop_dead` on.

| Idea | PC, quieter, default (s) | PC, busy, default (s) | PC, busy, Test A (s) | Server, Test A (s) | Peak on the PC, Test A (MB) |
|---|---|---|---|---|---|
| Nothing on | 53.4 | 105.6 | 78.3 | | 493 |
| **Lossless set** | 27.1 | 40.8 | 39.0 | 77.7 | 449 |
| Drop dead nodes | 25.5 | 34.2 | 33.2 | 68.6 | 415 |
| Light by rows (`light_rows`) | 17.0 | 21.2 | 23.6 | 40.4, 40.6 | 445 |
| 24 light directions, not 60 | | 20.5 | 22.8 | 37.0, 34.1 | 443 |
| Light field lasts 2 years | | 18.6 | 18.6 | 36.5 | 457 |
| 16 probes, not 64 | | | 20.2 | 39.5 | 441 |
| 0.15 m light grid | | | 17.8 | 28.3, 26.9 | 323 |
| 0.2 m light grid | 9.7 | 11.9 | 16.0 | 27.0, 24.9 | 307 |
| 0.3 m light grid | | | | 22.8 | |

Quieter PC: seed 1, best of 3, CPU load about 18 % when checked. Busy PC: seeds 1 and 2, best of 2, other agents running. Server: mean of 20 trees per draw, 3 at once, and earlier draws had other jobs alongside. Default on the server: lossless 85.5 and 67.3 s across two draws (its load differed), dropped 74 s, rows 41.9 and 39.4 s, 24 directions 32.6 s, 0.2 m 20.4 s and about 20 s.

**Plots.** 100 trees to 60, default, server, one run each: 3,519 s off, 1,263 s with the lossless set except `quick_levels`, or 0.65 to 0.23 s per tree-year. A 25-tree Test A plot to 30 on the busy PC, best of 2: 161.0 s off, 66.5 lossless, 83.2 with dropped nodes (no gain seen in that pair, though peak memory fell from 939 to 547 MB), 66.2 with rows, 68.5 with a 0.2 m grid. A plot spends about 9.5 % of its time in light, so a coarser grid gains almost nothing there.

## Lossless: the proof

Six settings: `speed.compiled_carbon`, `compiled_mechanics`, `light_layers`, `keep_soil_grids`, `quick_solve`, `quick_levels`.

| Check | Result |
|---|---|
| All four golden runs, PC, all six, commit 692858f | Identical: 225 files |
| All four golden runs, server, all six, commit 692858f (`node_speed_gold3`) | Identical: 225 files |
| Default and Test A trees to 16, a 25-tree-start plot to 9, all six | Identical, in `tests/test_speed.py` |
| Test A trees to 60, first four settings, seeds 1-3 (to 30 on seeds 1, 2) | Every yearly stat and tree array identical |
| Test A tree to 60, `compiled_carbon` and `quick_solve`, seed 5; default, seed 6 | Identical |
| Each kernel against its numpy or scipy form | Bit for bit, in `tests/test_speed.py` |

**Gaps:** golden runs are default settings only, and all six together have been run on Test A only to 16 years. `quick_solve` also relies on the carbon sum rising with growth. If it ever fell across the target, the answer could differ from the plain loop, so its proof is "identical on every run tested", not a guarantee.

**Server, in one job, off then on (s):** tree60 126.9 to 86.8, mesh30 36.6 to 23.9, plot25 148.0 to 80.2, regen10 46.1 to 30.1. Peak MB: 752 to 787, 514 to 522, 910 to 903, 459 to 461.

**What each does:** carbon and mechanics are compiled and walk living nodes only. Light grids are held layer first, so a layer's cells lie together in memory. The soil grid is kept rather than rebuilt each year. The carbon solve reaches bisection's same answer in fewer evaluations. The order of passes comes from a compiled count.

**If anyone changes** `parts()` in `_growth_factor` or `bend_and_correct`, the copy in `treegen/fast.py` must change too; `tests/test_speed.py` fails if they drift.

## Not lossless, but the same maths: the maintainer's approval needed

**`light_rows`** does the same light sums one row of frequencies at a time, with scipy's FFTs. The field agrees with the plain sweep to at most 1.07e-6 (mean about 1e-7), in a field of up to 2.15, on three year-20, 40 and 60 fields. Because rounding differs, a seed makes a different tree, as it does on another machine. It also shrugs off other work on the PC: one year-60 field took 4.4-5.7 s the plain way and 0.57-0.75 s by rows in the same session.

**`drop_dead`** drops dead nodes in lean runs. In 20 seeds to 60 on the server, against the same seeds without it:

| Settings | Seeds with any yearly field changed | Fields | Means at 50, 60 |
|---|---|---|---|
| Test A | 0 of 20 (stats are rounded: one seed's geometry differs by about 1e-14 at 60) | 0 of 39,040 | Unchanged |
| Default | 5 of 20, earliest from age 37 | 136 top-level fields, 333 counted individually, of 37,820 | Unchanged to the digits shown |

So the sums round differently and this can spread. It isn't lossless.

**What `drop_dead` keeps:**
- Exports aren't affected, because it acts only on lean runs and exports aren't lean. All four golden runs are identical with it on, on the PC; `tools/game_export.py` itself wasn't run with it on.
- The count of what fell and new-shoot lengths match on 8 Test A seeds on the PC, after two fixes of mine. The server's 20-seed sets ran before those fixes, so those two columns aren't valid in them, and the fixed code hasn't been re-checked on the server.
- Scars on living wood match on one seed, to 24.

## Accuracy

Each cell: shift against the baseline, % (z). **Baselines, at 50, 60.** Test A, 60 seeds: LAI 4.30, 4.07; light 18.5, 19.4 %; stem 237, 310 kg; branches 39.6, 52.1 kg; crown width 6.72, 7.22 m; crown ratio 0.562, 0.530; low limbs 86.8, 84.3 deg; mid limbs 93.1, 88.8 deg. Default, 40 seeds: height 25.18, 26.91 m; LAI 3.23, 3.37; light 28.9, 26.9 %; stem 333, 435 kg; branches 44.6, 62.2 kg; crown width 3.32, 3.91 m; crown ratio 0.740, 0.713; low limbs 87.5, 85.9 deg; mid limbs 82.9, 82.9 deg. On Test A height follows the curve, so it isn't a test there.

**Test A, server, 40 seeds against 60 (every 2 years: 20 against 20):**

| At 50, 60 | Rows | 24 directions | 0.15 m | 0.2 m | Every 2 years |
|---|---|---|---|---|---|
| LAI | +0.3 (0.2), -0.6 (-0.2) | +1.4 (0.6), +0.8 (0.3) | +0.3 (0.1), 0.0 (0.0) | -0.4 (-0.2), -0.7 (-0.3) | +1.2 (0.3), +0.9 (0.2) |
| Light | +0.3 (0.1), +1.0 (0.3) | -1.1 (-0.4), -0.7 (-0.2) | +0.3 (0.1), +0.2 (0.1) | -0.8 (-0.3), -0.9 (-0.3) | -2.3 (-0.4), +0.2 (0.0) |
| Stem wood | -0.7 (-0.2), -0.9 (-0.3) | -0.2 (-0.1), -0.7 (-0.2) | -1.8 (-0.7), -1.8 (-0.6) | -4.1 (-1.5), -3.9 (-1.3) | **+15.0 (3.1), +16.0 (2.9)** |
| Branch wood | +0.5 (0.2), -1.5 (-0.4) | +3.3 (1.0), +2.7 (0.8) | +4.7 (1.5), +1.9 (0.6) | +2.7 (0.8), +1.4 (0.4) | +0.6 (0.1), **-12.0 (-2.5)** |
| Crown width | +0.1 (0.1), -1.0 (-0.7) | +1.2 (0.7), -0.9 (-0.6) | +2.9 (1.9), +2.1 (1.5) | **+3.3 (2.5)**, +1.7 (1.2) | **-5.5 (-2.8), -9.5 (-4.5)** |
| Crown ratio | +1.0 (0.3), +0.7 (0.2) | +2.8 (0.8), +4.9 (1.1) | +2.3 (0.6), +0.9 (0.2) | +0.5 (0.1), +0.3 (0.1) | -1.6 (-0.3), -7.2 (-1.1) |
| Limb angle, low | +0.6 (0.3), -1.7 (-0.9) | -0.5 (-0.3), -1.6 (-0.9) | +0.6 (0.3), -0.5 (-0.3) | -0.3 (-0.2), -2.8 (-1.4) | **+5.9 (2.0)**, +2.1 (0.6) |
| Limb angle, mid | -0.3 (-0.2), -0.5 (-0.3) | -1.5 (-1.0), -0.9 (-0.6) | -0.3 (-0.2), -0.5 (-0.3) | -0.2 (-0.1), -0.4 (-0.3) | +4.2 (2.0), +3.9 (1.5) |
| Rows with z of 2 or more | 0 of 30 | 0 of 30 | 0 of 30 | 1 of 30 | 6 of 18 |

**Default, server, 40 seeds against 40:**

| At 50, 60 | Rows | 0.2 m |
|---|---|---|
| Height | -0.9 (-1.5), -0.9 (-1.6) | -1.1 (-1.8), -1.1 (-1.7) |
| LAI | +0.8 (0.3), +0.6 (0.3) | +0.8 (0.3), +1.4 (0.6) |
| Light | -1.6 (-0.6), +0.4 (0.2) | -2.8 (-1.1), -2.8 (-1.4) |
| Stem wood | -0.8 (-0.1), -0.8 (-0.1) | +4.8 (0.8), +5.3 (0.8) |
| Branch wood (one outlier tree makes this row weak) | +0.9 (0.0), -0.3 (0.0) | +8.4 (0.2), +8.8 (0.2) |
| Crown width | +1.2 (0.3), +0.3 (0.1) | +9.6 (1.9), **+11.9 (2.0)** |
| Crown ratio | +1.0 (0.4), +0.6 (0.2) | +2.1 (0.9), +2.3 (0.6) |
| Limb angle, low | +2.3 (1.2), +3.6 (1.6) | -0.4 (-0.2), +0.4 (0.1) |
| Limb angle, mid | -0.1 (0.0), -2.6 (-0.9) | -5.6 (-1.8), **-8.6 (-2.9)** |
| Limb angle, upper | -1.6 (-0.5), 0.0 (0.0) | **-11.2 (-3.7), -8.2 (-3.3)** |
| Rows with z of 2 or more | 0 of 30 | 8 of 30 |

The 30-row counts also include where the crown is widest, side fill, hanging leaves, branch count and branch length: the other 0.2 m default rows are widest point +26 % at 60, fill -4.3 % at 60, hanging leaves -6.8, -8.6 %.

**Other first draws, 20 seeds:**
- 16 probes, Test A: 0 of 18.
- 0.3 m, Test A: 0 of 18 over the line, with branch wood +9.0 % (z 2.0, just under the line) and stem wood -6.0, -5.3 % at 50, 60.
- 24 directions, default: 0 of 18, with height -1.7, -1.8 % (z -2.0).

0.15 m on default wasn't run.

**Noise.**
- `tools/noise_floor.py`, server, default, one seed, 28 changes of a few parts per million. SD of the moves at 50, 60: height 2.35, 2.22 %; LAI 4.93, 3.75 %; light 5.38, 4.08 %; crown ratio 6.93, 6.51 %. Largest LAI move 13.4 %.
- Two baseline draws of the default differ by z 2.4 on LAI and light at 50. So a single row near z 2 proves little.
- The tests are unpaired. The sets from rows down run with `drop_dead` on and the baselines without.

**Plots:** no result yet. Only two baseline plots finished: Test A, lossless, 1,372-1,418 s each, 7.3-7.5 GB (`tools/ensemble.py` plots aren't lean, so `drop_dead` does nothing in them), with LAI 4.59, 4.30-4.34 and light 15.7-15.9, 16.4 % at 50, 60.

## Where the time and memory go, with nothing switched on

Lean runs, seed 1, one tree on a busy PC and one plot on a busy server. **Shares move with load:** the light sweep carries every direction's spectrum through memory once a layer, so other work on the PC slows it far more than the rest. One year-60 field took 0.9 s in the tree's profile and 4.4-5.7 s later, when the PC was fuller. So don't read these seconds as a tree's best time.

**A stand tree, seconds in that one year (shares of the whole run in brackets):**

| Part | Default | Test A |
|---|---|---|
| Year 10, 20, 30, 40, 50, 60, all parts | 0.32, 0.59, 1.45, 1.56, 1.60, 1.75 | 0.12, 0.35, 0.65, 1.60, 2.00, 2.82 |
| All of light, at 50, 60 (60 %, 46 %) | 1.00, 1.05 | 0.99, 1.01 |
| Carbon solve and subtree sums, at 50, 60 (14 %, 28 %) | 0.20, 0.27 | 0.54, 1.27 |
| Mechanics, at 50, 60 (10 %, 12 %) | 0.18, 0.20 | 0.22, 0.26 |
| Water, at 50, 60 (10 %, 7 %) | 0.13, 0.13 | 0.14, 0.14 |
| Nodes, of them alive, at 50 | 82,363, 30,078 | 126,669, 38,437 |
| Nodes, of them alive, at 60 | 89,766, 31,927 | 147,669, 40,121 |
| Light grid at 60 | 189 x 189 x 308 | 189 x 189 x 280 |

Light's parts on the default tree at 60: the sweep's own multiply and add 0.59 s, forward FFT 0.14, leaf blur 0.10, inverse FFT 0.08, weighting 0.08. The grid's cell jumps with stem density: 126 to 189 cells across at about age 25-30 tripled light's cost in a year.

**Inverse FFT and weighting on unread layers, P0's estimate of "at most about 9 %":** 218 of 308 layers are read at 60. So skipping the other 90 would save at most about 2.4 % of a tree. Not worth doing on its own.

**A plot of 100 trees to 60, default, on the server: 3,519 s.** It's very different from a tree:

| Part | Share | Seconds in year 50, 60 |
|---|---|---|
| Mechanics | 47.7 % | 11.4, 11.9 |
| Carbon solve | 21.2 % | 17.2, 15.9 |
| Subtree sums | 6.8 % | 6.1, 5.9 |
| All of light, shared and per tree | 9.5 % | 6.3, 6.4 |
| Everything else | about 15 % | |

- **Cost per tree-year, all in: 0.65 s** (5,421 tree-years): 0.61 s in each tree's own step, 0.044 s shared (light, soil). By plot age: 0.27 s at 10 and 0.56 s at 60.
- **Why mechanics is so large:** at 60 the plot holds 7.4 million nodes and 0.95 million are alive. Whole-array passes walk the dead ones.
- **Memory at 60: 37.6 MB per tree** in the model's attributes (80 trees, 3.0 GB), and 4.0 GB for the process. The six position and direction arrays are 1.14 GB of that.

**One stand tree's own state, lean, on the PC (`tools/speed_memory.py`):**

| Age | Nodes, live, default | State (MB) | If only live nodes were kept (MB) | And single precision (MB) | Save, gzip (MB) |
|---|---|---|---|---|---|
| 50 | 78,752, 27,473 | 34.3 | 9.5 | 5.8 | 17.8 |
| 60 | 86,768, 29,253 | 36.7 | 10.9 | 6.6 | 20.1 |

| Age | Nodes, live, Test A | State (MB) | If only live nodes were kept (MB) | And single precision (MB) | Save, gzip (MB) |
|---|---|---|---|---|---|
| 50 | 124,773, 38,144 | 51.2 | 12.2 | 7.3 | 27.6 |
| 60 | 146,163, 38,258 | 62.4 | 13.1 | 7.9 | 32.5 |

The last two columns of arrays are sums over what the arrays hold, not runs. A stand tree also holds about 170-180 MB of light grids for its neighbour cell while the sweep runs, but those belong to a place, not a tree.

## Published ways of keeping this cheap

| Source (where read) | What it does | Numbers it gives | What it means here |
|---|---|---|---|
| Palubicki et al. 2009, *Self-organizing tree models*, ACM TOG 28(3) (author's site) | Shadow copied into a pyramid of voxels under each bud, 4-8 layers deep, on a grid of about 200 x 200 x 200, cell about one internode | 700,000 internodes, 106 steps, 82 s on a 2.4 GHz Pentium 4; 225,000 in 21 s | Why a tree can be "a few seconds": no water, roots, mechanics or carbon solve, and only near shade. It never reaches a canopy's light target, so it isn't a like-for-like option |
| Perttunen, Sievanen, Nikinmaa 2007, FSPM07 (group's site) | LIGNUM stand: 0.16 m voxels on 20 x 20 x 20 m, one year step, all trees copies of one | Aim: a small plot in "a twenty-four-hour period" | Our stand tree is the same idea, far faster already. No voxel size test in it |
| Sievanen, Perttunen, Nikinmaa 2007, FSPM07 (group's site) | One tree grown, others identical, because "the calculation of radiation is computationally demanding" | No timings | The same trade |
| Seidl et al. 2012, *Ecological Modelling* 231 (Andrews Forest, a co-author's programme); iland-model.org (authors) | iLand: each tree's light pattern worked out once ahead, by species and size, on a 2 m grid, and stamped yearly | 5 million trees on 10,000 ha, one light cycle in about 15 s on office hardware; scales linearly | The route for distant trees: a summary per tree. It gives no branches, so it's a different model and would need its own check against our plots |
| Makowski et al. 2019, *Synthetic Silviculture*, ACM TOG 38(4) (author's site) | Plants built from reused branch modules; shadow per module on a coarse grid | 468,199 plants, 18.8 s a step, 26,776 K nodes shown (Table 2, its Fig. 19) | The route for detail by level. Results are judged as plausible, not against measurements |
| Lu et al. 2011, *Silva Fennica* 45(3) (publisher, abstract only) | Monte Carlo voxel space in LIGNUM for "computational efficiency" | None in the abstract | Nothing to use |

**Blocked:** Nauber & Mader 2024, *Light Distribution Models for Tree Growth Simulation*, Computer Graphics Forum: the Eurographics library and Wiley both returned 403, so I have only its abstract. It compares ray tracing, space colonisation, voxels and bounding volumes, and is the closest paper to this question. A search result offered a Scribd copy of another LIGNUM paper; I didn't use it.

**Not found:** any published test of how far ahead a light result can be reused. iLand updates its field yearly; LIGNUM's step is a year. That's why I tested it directly.

## How far this can go

| Target | Today | Lossless | With rows and dropped nodes | Plus a C++ port (a guess) |
|---|---|---|---|---|
| One tree to 60, default, one core, quieter PC | 53.4 s | 27.1 s | 17.0 s | about 9-11 s |
| 100-tree plot to 60, default, server | 3,519 s | 1,263 s (without `quick_levels`) | not finished | not worked out |
| Per tree-year in a shared forest, default, server | 0.65 s | 0.23 s | not finished | not worked out |

**What C++ would really add.** On a Test A tree with rows and dropped nodes (29.9 s, busy PC), 46 % of the timed work is already in compiled code: light 9.6 s, tree passes 3.5 s. A port gains little there. The other 15.7 s is Python and numpy. Carbon, subtree sums and mechanics went from 27.3 s to about 4.2 s when I compiled them, 6.5x, though that includes walking fewer nodes, across two runs at different load. The blur gained 3-4x. Applying 3-6.5x to the 15.7 s gives about 1.6-1.9x overall. That's my estimate, not a port. It would also lose bit-identity and need a new baseline.

**The maintainer's 4 s.** A tree isn't 4 s because each of 60 years solves light across up to 11 million cells in 60 directions, plus water, carbon, roots and bending for tens of thousands of living nodes. Palubicki's model made 700,000 internodes in 82 s on a Pentium 4, but it has none of that and doesn't aim at a canopy's light target.

| Route to 4 s | Time | Accuracy | Status |
|---|---|---|---|
| Rows and dropped nodes, one core | 17 s | No shift on 80 default trees; plots not checked | Measured |
| Plus C++ | about 9-11 s | As above, with a new baseline | Guess |
| Plus 0.15 m grid | about 5-6.5 s | No shift on 100 Test A trees; default not tested | Guess, scaled from a busy PC |
| Plus several cores | maybe about 4 s | As above | Guess. Against it: the row sweep alone gained 3.2x on 8 threads, but scipy's FFT workers gained nothing, on a busy PC |

So 4 s isn't shown to be reachable without an accuracy cost. On one core I don't expect it.

## The live forest

- **Time:** 15,000 trees at 0.23 s a tree-year (one server core) is about 3,450 s per game year, against 61 real days: about 0.07 % of one core. Even at today's 0.65-0.75 s it's about 0.2 %. Baking a forest ahead is the job where tree time matters.
- **Light in a forest:** the shared part cost 0.04 s per tree-year. It scales with ground area, not trees, so a real forest would need tiles. I didn't test tiles.
- **Memory is the limit.** At 60 a plot tree holds 37.6 MB (default) or 42.9 MB (Test A), so 15,000 trees would need 560-640 GB. A stand tree's arrays with only live nodes would be 11-13 MB, and 7-8 MB in single precision (sums over its arrays, not runs). That's still 100-200 GB. A gzip save is 20-32 MB a tree. So most trees can't hold their full structure at once. They'd need a tree-level summary, as iLand uses, with detail grown near the player. I haven't tested whether a summary reproduces our plots.

## Recommendations

| Decision | What | Why |
|---|---|---|
| Adopt now (main session's call) | The six lossless settings | Golden proof on both machines. First run all six on Test A to 60 once, to close the gap above |
| The maintainer's approval | `light_rows`, after its plots pass | About 1.5x beyond lossless, no shift on trees, far less hurt by other work. New baseline needed |
| The maintainer's approval | `drop_dead`, for forests | Modest time gain and plot memory down 42 % (one pair). Means unchanged, but not bit-identical |
| Optional | 0.15 m grid on stand trees | No shift on Test A, but default untested. No use in plots, where light is about 9.5 % of the time |
| Dead end | Light field lasting 2 years | Stem wood +16 %, crown width -9.5 % at 60 |
| Dead end on default | 0.2 m grid | 8 of 30 rows moved: crown width +12 %, upper limbs -11 % |
| Not worth it | 24 directions, 16 probes | 3-14 % on the PC once rows are on. No shift shown |
| Not worth it | Skipping unread light layers | At most about 2.4 % |
| Not tried | Trimming high light frequencies; single precision; neighbour summaries; light tiles | First is worth little after rows. Single precision is sums only. The other two need design work |

## Measured, and guessed

**Measured:** everything in the tables above except what's marked as a guess. PC times vary a lot with other agents' work, so treat them as rough; that's why each column stays on one machine under one kind of load.

**Guessed:** the C++ gain and everything built on it; several cores reaching 4 s.

**Worked out from measurements, not run:** the 15,000-tree core and memory figures; live-only and single-precision memory.

**Corrections to what I told `main` along the way:** a plot's light share is 9.5 %, not about 5 %. `drop_dead` doesn't keep every yearly stat on default seeds. The "136 rows" I reported are 136 top-level fields.

## How to finish

These were queued on the server at handback: `node_speed_q5b` (plots: baseline, rows, second baseline, 0.15 m) and two Test A plot profiles. They can be cancelled with `tools/node/cancel.sh <label>` if nobody wants them.

```
timeout 60 bash tools/node/fetch.sh 325ad08 node_speed_p_A_droponly     # then A_rows, A_base2, A_vox15
python tools/speed_accuracy.py plots node_speed_p_A_droponly node_speed_p_A_base2 -- node_speed_p_A_rows node_speed_p_A_vox15
CORES=1 timeout 60 bash tools/node/submit.sh 863bd50 node_speed_prof3 tools/speed_collect.py node_speed_prof3 863bd50
timeout 60 bash tools/node/fetch.sh 863bd50 node_speed_prof3
python tools/speed_plot_read.py out/bench/ensemble/node_speed_prof3/node_speed_plot_A_rows.json out/bench/ensemble/node_speed_prof3/node_speed_plot_A_lossless.json
```

Still not run: `tools/forest.py` with the settings on and off (the Forest agent's own lean plots, where `drop_dead` should matter most), `drop_dead` on the server with the fixed code, and 0.15 m on default.
