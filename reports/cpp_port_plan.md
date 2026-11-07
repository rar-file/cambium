# Plan: porting the birch model to C++, and what it costs now

Plan and measurement only. Nothing has been ported, nothing in `treegen/` or in the game was changed, and Unreal wasn't launched.

## The short version

- **Today, on one server core:** an old stand tree takes about 2 s for its year, and a tree to 60 takes about 67 s. In a forest plot an age-60 tree takes about 0.6 s for its year, and a 1000 m² plot takes about 45 s a year whatever its age.
- **C++ alone is no miracle.** About 2.5-3x on a whole plot and 1.3x on one big tree. With two speed settings that are already in the model and still need your yes, one big tree reaches about 2x. These whole-model figures are estimates, built on six small pieces I did port and measure.
- **Time isn't the limit.** At the game's 6x speed a game year lasts 61 real days. If each of the 31,573 trees in reach cost what an old birch does, they'd use under 0.4 % of one core, even in today's Python.
- **Memory and catching up are the limits.** An old tree holds 34 MB today, and about 7 MB looks like the floor for the full model. That's about 140 full trees per GB, against 4,222 birches in reach. After a real year away, the game's own 5-second limit covers about 45-95 full old trees.
- **So only a few trees can be full trees:** those in places the player has touched. The rest would be a small summary (age, height, stem, crown) from tables grown ahead by the real model. Summaries have no branches, and I haven't tested how well they match the model's own plots. That's the biggest unknown.
- **A shipped game can't build Nanite meshes.** So unless you accept much lighter live-built meshes, what you see comes from pre-built stages, not from the tree's own simulated limbs. That's your decision (section 3).
- **The port can be proved right.** With the same random numbers, a rounding-sized change stayed invisible until about age 47-56 on 3 seeds, so Python and C++ can be compared tree by tree, then as whole forests.
- **Don't start yet.** `growth.py` changed in 30 commits in two days. Some groundwork can start now (section 6).
- **Rough effort, an estimate:** 3-4 weeks for stages plus summaries; 50-90 agent-days for the full model live.

**What I need from you, when you're ready:**
1. Which option in section 3: stages with summaries, stages with full science in touched places, or live-built meshes near the player.
2. Does "1:1 with life" mean whole-tree numbers (height, stem, crown, mass, how the forest thins), or the actual limbs you see? This decides most of the work.
3. How much memory trees may have. The game's limit is 6 GB in all, and its own audit found nothing logs what it uses.
4. Whether `speed.light_rows` and `speed.drop_dead` can be used. They're already waiting on you, and the plan assumes yes.

## 1. What runs in the game, and what stays offline

Lines are from `treegen/` at 5f07fae, which has 15,037 lines. "Reached" counts lines of code run by a 30-year stand tree and a 200 m² plot to 30 on current settings, with storms and spread on. It's measured (`tools/cpp_cost.py lines`), but a short run misses rare branches. Compiled functions (marked \*) run where Python can't see them, so their counts are too low. "Changed" is commits since the reset on 2026-11-06.

| Module | Lines | Lines of code | Reached | Changed | What it does | Side |
|---|---|---|---|---|---|---|
| `growth.py` | 2,840 | 2,170 | 1,685 | 30 | The year's step: light reads, shedding, carbon, allocation, shoots, rings | **Game** |
| `roots.py` | 1,040 | 811 | 729 | 5 | Root growth, soil water, anchorage | **Game** |
| `damage.py` | 645 | 443 | 347 | 7 | Old age, wind, snow | **Game** |
| `plot.py` | 581 | 438 | 323 | 9 | Trees sharing light and soil; the year's order; deaths | **Game**, rebuilt round the game's cells and scheduler |
| `light.py` | 470 | 345 | 251 | 3 | Voxel shade by FFT sweep, and reading it | **Game** |
| `regeneration.py` | 370 | 253 | 165 | 7 | Seed rain, germination, spread | **Game** |
| `environment.py` | 268 | 194 | 185 | 0 | Sky directions, soil | **Game**; climate comes from the game's drivers |
| `structure.py` | 208 | 155 | 126 | 2 | Node arrays, tree passes | **Game** |
| `thinning.py` | 174 | 105 | 102 | 4 | Deaths from crowding and low vigour | **Game** |
| `mechanics.py` | 168 | 92 | 59 | 2 | Bending and posture | **Game** |
| `hydraulics.py` | 119 | 62 | 56 | 0 | Water and stomata | **Game** |
| `kernels.py` | 119 | 87 | 13\* | 0 | Compiled passes | **Game** |
| `fast.py` | 649 | 540 | 133\* | 7 | Compiled copies of hot passes | **Game**: these forms are the port; their numpy twins aren't ported |
| `compact.py` | 95 | 70 | 4 | 4 | Drops dead nodes | **Game**, if you approve it |
| `reference.py` | 67 | 49 | 7 | 0 | Published curves | One function in the game (Eriksson's height, which the height limit reads); the rest offline |
| `params.py` | 148 | 103 | 34 | 0 | Reads the YAML | Offline; the game reads JSON through `science::Library` |
| `species_schema.py` | 706 | 597 | 434 | 9 | What a species file must hold | Offline; its table generates the C++ reader |
| `checkpoint.py` | 49 | 31 | 17 | 0 | Saves a tree | Replaced by the game's save format |
| `appearance.py` | 392 | 283 | 0 | 4 | How each part looks at an age | Offline; baked into UV channels the materials read. Part of it in the game only with live-built meshes |
| `mesh.py` | 1,054 | 825 | 55 | 8 | Tube meshes | Offline; in the game only with live-built meshes |
| `game.py` | 600 | 470 | 0 | 6 | Levels of detail | Offline |
| `game_unreal.py` | 1,342 | 1,027 | 0 | 8 | Export for the game | Offline |
| `textures.py` | 924 | 701 | 0 | 5 | Bark and leaf textures | Offline |
| `export.py` | 822 | 666 | 60 | 4 | File writers | Offline |
| `look_render.py` | 538 | 446 | 0 | 3 | Software renderer | Offline |
| `preview.py` | 443 | 365 | 36 | 0 | Silhouettes | Offline |
| `runhash.py`, `machine.py`, `threads.py`, `__init__.py` | 206 | 140 | 45 | 0 | Digests, machine details, thread setting | Offline; not needed in the game |

**In the game: 7,746 lines, of which 5,765 are code and about 4,000 are reached, plus the 627 compiled lines.** So on today's settings the port is about 4,500 lines of Python, or perhaps 8,000-10,000 lines of C++ (an estimate). About 490 lines of `growth.py` weren't reached. Options that stay off at the freeze needn't be ported at all.

**Where it would live.** `Source/<Game>Core`, the game's science core: plain C++20 with no Unreal types, built with precise floating point, with tests that also build on Linux (`Tools/Core/test.sh`). A new module adds its own files and edits nothing shared (`Docs/Design/Testing.md`). Drawing stays in `Source/<Game>/World`. The game has no plugins folder, and nothing here needs one.

## 2. What it costs now

**All measured on the server unless it says "estimate".** One Neoverse-N1 core, Python 3.14.7, numpy 2.5.4, scipy 1.18.1, numba 0.68.1. The model is 5f07fae. The tools are `tools/cpp_cost.py`, `tools/cpp_kernels.py` and `tools/cpp_cost_kernels.cpp` on this branch. Results are on the node in `out/bench/ensemble/` of `repo_53ef01f` (`node_cpp_res`), `repo_ba47503` (`node_cpp_res2`) and `repo_ca1592a` (`node_cpp_res3`, whose `tables.md` holds every table in full).

- **Settings:** the verdict settings of `node_dmg_fix5`: crown frame, paid roots, height limit, storms and snow on.
- **Speed:** the six lossless speed settings on, unless a table says otherwise. Those six gave the same digest as none on all 3 seeds.
- **Timers:** they changed nothing: the digest matches a run without them (`d51caa4498a5`), which took 67.2 s against 69.6 s.
- **Caution:** 11-16 of the server's 16 cores were busy, and this is 3 trees and 2 plots. The 3 seeds' whole runs differ by up to 10 %, and other work moves light more than that (`reports/speed_research.md`), so treat times as rough. Crown 2's settings aren't in this commit and will move these numbers.

The "Compiled" column is the share of a stage already inside compiled code (numba, FFTs, tensordot, ndimage filters). A port can't gain much there. The rest is Python and numpy.

### A stand tree: seconds for its year, mean of 3 seeds

| Stage | Age 10 | Age 30 | Age 50 | Age 60 | Share of run | Compiled |
|---|---|---|---|---|---|---|
| Light: the field | 0.055 | 0.395 | 1.198 | 1.265 | 58.4 % | 50 % |
| Light: reading it | 0.006 | 0.060 | 0.102 | 0.096 | 5.8 % | 7 % |
| Carbon | 0.004 | 0.140 | 0.384 | 0.319 | 16.4 % | 78 % |
| Growth: shoots | 0.015 | 0.065 | 0.059 | 0.051 | 4.6 % | 20 % |
| Growth: rings | 0.001 | 0.015 | 0.040 | 0.046 | 1.8 % | 12 % |
| Mechanics | 0.001 | 0.040 | 0.093 | 0.094 | 5.6 % | 84 % |
| Shedding | 0.001 | 0.014 | 0.023 | 0.024 | 1.1 % | 28 % |
| Roots | 0.014 | 0.030 | 0.059 | 0.061 | 3.7 % | 34 % |
| Water | 0.002 | 0.016 | 0.036 | 0.039 | 1.7 % | 10 % |
| Damage, stats | 0.001 | 0.010 | 0.016 | 0.016 | 0.9 % | 12 % |
| **All** | **0.098** | **0.785** | **2.010** | **2.010** | 100 % | **50 %** |
| With no speed settings | 0.158 | 1.379 | 3.746 | 4.010 | | |
| With lossless, light by rows and dead nodes dropped | 0.072 | 0.592 | 1.151 | 1.216 | | |
| Crown nodes, live of all | 776 of 913 | 28,915 of 71,013 | 52,128 of 197,328 | 48,968 of 230,475 | | |
| Root nodes, live | 144 | 4,919 | 16,745 | 22,000 | | |
| Light grid | 94 x 94 x 40 | 126 x 126 x 184 | 189 x 189 x 258 | 189 x 189 x 280 | | |

A whole tree to 60: 67 s with lossless settings, 119 s with none, 42 s with rows and dropped nodes. A stand tree has no thinning.

### A plot: seconds per tree-year, mean of 2 plots

1000 m², from 16,000 stems/ha, with thinning, seed spread and storms on.

| Stage | Age 10 | Age 30 | Age 50 | Age 60 | Share of run | Compiled |
|---|---|---|---|---|---|---|
| Light: the shared field | 0.0005 | 0.0097 | 0.0413 | 0.0647 | 7.0 % | 54 % |
| Light: reading it | 0.0014 | 0.0129 | 0.0394 | 0.0537 | 8.6 % | 0 % |
| Carbon | 0.0032 | 0.0159 | 0.1512 | 0.2315 | 21.4 % | 42 % |
| Growth: shoots | 0.0140 | 0.0302 | 0.0560 | 0.0631 | 25.5 % | 9 % |
| Growth: rings | 0.0005 | 0.0030 | 0.0146 | 0.0223 | 2.6 % | 11 % |
| Mechanics | 0.0003 | 0.0068 | 0.0403 | 0.0624 | 5.9 % | 80 % |
| Shedding | 0.0003 | 0.0071 | 0.0165 | 0.0202 | 3.8 % | 11 % |
| Roots | 0.0086 | 0.0155 | 0.0277 | 0.0355 | 12.7 % | 8 % |
| Water | 0.0021 | 0.0114 | 0.0237 | 0.0309 | 7.9 % | 5 % |
| Thinning | 0.0001 | 0.0003 | 0.0005 | 0.0006 | 0.2 % | 0 % |
| Seed spread | 0.0001 | 0.0012 | 0.0017 | 0.0021 | 0.6 % | 0 % |
| Storms and old age | 0.0002 | 0.0009 | 0.0004 | 0.0005 | 0.5 % | 0 % |
| Stats and the rest | 0.0008 | 0.0043 | 0.0124 | 0.0166 | 3.3 % | 5 % |
| **All** | **0.0321** | **0.1196** | **0.4258** | **0.6042** | 100 % | **22 %** |
| With rows and dead nodes dropped (1 plot) | 0.0315 | 0.1121 | 0.3302 | 0.4216 | | **20 %** |
| Whole plot's year, s | 46.7 | 40.5 | 46.5 | 45.9 | | |
| Trees in the year | 1,452 | 340 | 110 | 76 | | |
| Stems/ha | 14,245 | 3,180 | 1,060 | 745 | | |
| Live nodes in the plot, crown and roots | 384,813 | 2,398,674 | 3,218,012 | 3,303,532 | | |
| Largest tree's step, s | 0.067 | 0.233 | 0.737 | 1.041 | | |

- **Whole run:** about 2,560 s for 35,000-36,000 tree-years, or 0.069 s per tree-year, with the two cProfile years left out. Peak 4.6 GB. With rows and dropped nodes: 2,310 s, peak 3.4 GB.
- **Thinning and seed spread are almost free.** The cost is in the trees themselves.
- **A tree's own step at each age,** by least squares on its live nodes:

| Age | Seconds at no nodes | Microseconds per live node |
|---|---|---|
| 10 | 0.019 | 47 |
| 30 | 0.047 | 7.8 |
| 50 | 0.110 | 8.7 |
| 60 | 0.130 | 8.9 |

The no-nodes figure is a tree's fixed cost: thousands of numpy calls at age 10, and walking dead nodes later. With dead nodes dropped it falls to 0.054 at 50 and 0.060 at 60. The C++ port removes most of it.

### Meshing: one stand tree, every level, seconds for that age

Offline today, seed 1. This is the whole Unreal export, and most of it is textures.

| Part | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| Wood tube, nearest level | 0.07 | 1.59 | 4.78 | 5.62 |
| Leaf blades, nearest level | 0.05 | 1.07 | 2.32 | 2.04 |
| Stem relief and wood arrays, nearest level | 0.15 | 0.65 | 1.71 | 1.93 |
| Wood tube, `_lod1` | 0.05 | 0.11 | 0.12 | 0.12 |
| Leaf cards, `_lod1` | 0.01 | 0.08 | 0.15 | 0.15 |
| Far sheets, `_lod2` | 8.71 | 10.64 | 15.93 | 15.26 |
| Bark and root bake, atlases | 19.15 | 19.86 | 22.48 | 23.78 |
| PNG and file writing | 18.78 | 16.64 | 18.04 | 17.70 |
| Everything else | 1.57 | 4.39 | 6.50 | 7.32 |
| **All** | **48.6** | **55.0** | **72.1** | **74.0** |
| Triangles, nearest level | 46,311 | 986,828 | 2,199,240 | 2,156,095 |
| Triangles, `_lod1` | 5,598 | 16,000 | 16,000 | 15,998 |
| Mesh files, MB | 5 | 89 | 193 | 189 |
| Texture files, MB | 39 | 33 | 36 | 36 |

Peak 3.0 GB in the process. Building a `_lod1` mesh is about 0.3 s in Python, without its textures. That's the part that would matter for a mesh built live.

### Memory per tree, MB

| | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| **Plot tree: model state** | 0.15 | 3.69 | 22.15 | 33.81 |
| of which node arrays in use | 0.07 | 2.41 | 15.12 | 23.22 |
| of which Python's lists, dicts and history | 0.07 | 0.99 | 5.23 | 7.82 |
| Plot tree: state in a real run with dead nodes dropped | 0.14 | 2.99 | 11.81 | 17.26 |
| Plot tree: arrays, live nodes only (a sum, not a run) | 0.06 | 1.82 | 7.30 | 10.66 |
| Plot tree: and single precision (a sum, not a run) | 0.04 | 1.10 | 4.41 | 6.43 |
| Plot: light and soil grids, whole 0.1 ha | 80 | 122 | 148 | 155 |
| **Stand tree: model state** | 2.2 | 26.9 | 75.8 | 89.1 |
| Stand tree: state in a real run with dead nodes dropped | 1.9 | 13.0 | 31.1 | 29.6 |
| Stand tree: arrays, live nodes only (a sum) | 0.2 | 8.1 | 16.6 | 17.1 |
| Stand tree: and single precision (a sum) | 0.1 | 4.9 | 10.0 | 10.3 |
| Stand tree: light and soil grids, while they're in use | 5.3 | 18.5 | 51.9 | 54.9 |
| On disk: whole state pickled, gzip (stand tree) | 0.3 | 12.2 | 36.2 | 43.8 |
| On disk: with dead nodes dropped, gzip | 0.3 | 4.8 | 13.1 | 11.7 |
| On disk: live arrays, single precision, zlib (a sum) | 0.1 | 2.2 | 5.1 | 5.2 |

A node takes 252 bytes, or 152 in single precision. A single-precision run, measured with 8 seeds and no dead nodes dropped, took a stand tree from 85.1 to 57.5 MB at 60.

### A measured small port: six pieces in C++

`tools/cpp_kernels.py` hands `tools/cpp_cost_kernels.cpp` the arrays a real seed-1 tree reached, and times it beside the original in the same process, on one thread, best of a few runs, with g++ 13.3. Age 3 is about the size of most trees in a young plot.

"Strict" is `-O2 -ffp-contract=off`, the closest I can get on this server to what the game's core asks of its compiler. "O3" adds `-O3`. Each cell is how many times faster than the original the C++ is. The calls come through ctypes, which costs a few microseconds a call, so the age-3 figures are understated.

| Piece, and what it's measured against | Build | Age 3 | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|---|---|
| `hydraulics.solve`, against numpy | strict | 3.8x | 9.0x | 2.2x | 1.8x | 1.9x |
| `optimal_direction`, against numpy with a numba read | strict | 3.5x | 2.2x | 2.0x | 2.0x | 2.1x |
| `optimal_direction`, against numpy with a numba read | O3 | 3.8x | 2.7x | 2.4x | 2.5x | 2.6x |
| `bend_and_correct`, against numpy | strict | 32x | 10x | 4.9x | 4.4x | 4.4x |
| `bend_and_correct`, against numba | strict | 1.6x | 1.5x | 1.1x | 1.1x | 1.1x |
| Order of passes, against numpy | strict | 3.4x | 23x | 11x | 6.3x | 6.0x |
| Order of passes, against numba | strict | 0.3x | 0.7x | 1.1x | 1.1x | 1.1x |
| Leaf blur, against numba | strict | 0.6x | 0.7x | 0.7x | 0.7x | 0.7x |
| Leaf blur, against numba | O3 | 1.2x | 1.3x | 1.3x | 1.4x | 1.4x |
| Light sweep by rows, against numba by rows | strict | 0.3x | 0.3x | 0.3x | 0.3x | 0.3x |
| Light sweep by rows, against numba by rows | O3 | 1.1x | 1.1x | 1.1x | 1.1x | 1.1x |
| Light sweep by rows, against numpy by layers | O3 | 4.2x | 4.1x | 5.2x | 5.5x | 5.6x |

**What this says:**
- Against numba, C++ gains 10-40 %, and that needs the compiler to vectorise.
- Against numpy on big arrays, about 2-6x. On small arrays, about 3-30x, because numpy's cost per call is what hurts.
- `-O2` left the sweep 3.4x slower than `-O3`. So the sweep will need checking under MSVC, or writing by hand with vector instructions. I can't test MSVC here.
- FFTs aren't ported. A year-60 field takes 133 ms in scipy's and 222 ms in numpy's, and both are already C++. Expect about no gain beyond using scipy's way.

**Bits:** every strict and O3 result matched bit for bit, except `optimal_direction`, which differs by at most 6.5e-14 relative because numpy's `@` goes through OpenBLAS. g++'s default (`-O3 -mcpu=native`, which fuses multiply-add) gave different bits in the sweep, mechanics and hydraulics: up to 2e-5 relative in the single-precision sweep, and up to 7e-10 in a year's mechanics. So fused multiply-add must stay off.

### What a straight port saves, and what needs another method

| Per tree-year, one server core | Age 10 | Age 30 | Age 50 | Age 60 | Kind |
|---|---|---|---|---|---|
| Plot tree, Python today | 0.032 | 0.120 | 0.426 | 0.604 | Measured |
| Plot tree, Python with rows and dropped nodes | 0.032 | 0.112 | 0.330 | 0.422 | Measured |
| Plot tree, straight C++ | 0.003 | 0.04 | 0.21 | 0.32 | **Estimate** |
| Plot tree, C++ with rows and dropped nodes | 0.003 | 0.04 | 0.17 | 0.21 | **Estimate** |
| Stand tree, Python today | 0.098 | 0.785 | 2.01 | 2.01 | Measured |
| Stand tree, Python with rows and dropped nodes | 0.072 | 0.592 | 1.15 | 1.22 | Measured |
| Stand tree, straight C++ | 0.05 | 0.55 | 1.6 | 1.6 | **Estimate** |
| Stand tree, C++ with rows and dropped nodes | 0.03 | 0.4 | 0.9 | 0.9 | **Estimate** |

I made the estimates by applying the measured factors above, stage by stage, to the measured tables. For stages I didn't port, such as shoots and roots, I assumed 3x on old trees and about 10x on small ones. If numpy and Python took no time at all and compiled code stayed as it is, a plot could gain at most 4.5x and a stand tree 2x. Those two limits are measured.

**The game's PC is faster:** about 2.2-3.2x a core, from older runs of the Speed agent (`reports/speed_research.md`) against today's server figures. That's rough, and an estimate. I can't measure it now, because the PC is for games.

**What a straight port does and doesn't do:**

| Problem | A straight port | Needs another method |
|---|---|---|
| Small trees' cost | About 10x (estimate) | |
| A whole plot's time | About 2.5-3x (estimate) | |
| One big tree's time | About 1.3x (estimate): the light sweep is most of it | Light by rows: 5x on the sweep, already in Python (`speed.light_rows`) |
| Memory per tree | 34 to about 25 MB (estimate): only Python's own overhead goes | Dead nodes dropped, then single precision: about 7 MB (estimate) |
| Light for a whole forest | No help: 155 MB per 0.1 ha, so 1.5 GB per ha | Tiles, or one tree's cell at a time with neighbours summarised |
| Thousands of trees at once | No help: at about 140 trees per GB, 4,222 birches is 30 GB | Summaries |
| Meshes in a shipped game | No help: Nanite can't be built there | Stages, or lighter live meshes |

## 3. The live growth budget

### The game's own numbers

| What | Number | Where |
|---|---|---|
| Time | 6x, so a game year is 60.9 real days. It runs while the game's closed too | `<game>/time/Time.h:198`; `Decisions.md` round 3 |
| Frame | Game thread at most 9 ms, of which 1.5 ms for streamed commits. No frame over 50 ms | `Architecture.md` 2.10 |
| Threads | `UE::Tasks`, at most cores - 2, no raw threads. The PC is a 5800X, 8 cores and 16 threads | `Architecture.md` 2.3; `CLAUDE.md` |
| Memory | Budget 6 GB packaged, 6.5 GB video. Its audit found nothing logs it. The PC has 16 GB | `Architecture.md` 2.10, 3.3; `CLAUDE.md` |
| Catching up | Under 1 s after a real month, under 5 s after a real year, eyes closed | `Architecture.md` 2.5 |
| Trees in reach | 4,222 mature birches; 27,079 mature trees of all kinds; 31,573 with young trees and saplings. At the birth site, in the 2026-10-31 log | `Saved/Logs/<Game>.log:1683` |
| Streaming | Mature trees reach 450 m on 256 m cells; bodies only within 96 m; a tree cell takes about 10 ms to draw, one a frame | `flora.json`; `Architecture.md` 2.4; `CLAUDE.md` |
| What's simulated | Only touched places, on 64 m cells. Untouched land is a pure function of seed, place and date | `Decisions.md` round 8; `03-clock-persistence.md` |
| Planned tree model, not built | 32-byte `TreeState`, a yearly `StepYear`, and stand tables grown ahead (estimated 0.05-0.2 µs a tree) | `Research/Wave1/03-trees.md` 4.3, 4.7 |

### What those numbers allow

Estimates, from the measured costs above.

| Question | Sum | Answer |
|---|---|---|
| Steady live growth, all 31,573 trees at today's Python rate for age 60 | 31,573 x 0.604 s = 19,000 core-seconds, against 5.26 million real seconds a game year | **Under 0.4 % of one core: time isn't the limit** |
| Memory for all the birches at today's size | 4,222 x 34 MB | **143 GB** |
| The same at the floor | 4,222 x 7 MB | **30 GB: still far too much** |
| Full trees per GB, age 60 | Today 30; straight C++ about 40; dead nodes dropped about 85; single precision too about 140 | **Memory decides the count** |
| Catching up after a real year away (6 game years) | 5 s x 8 real cores = 40 core-seconds; an old tree's year in C++ on the PC is about 0.07-0.15 s | **About 45-95 full old trees** |
| Catching up after a real month (half the trees step once) | 8 core-seconds | **About 105-230 full old trees** |
| One 64 m place at full detail (0.41 ha), catching up a real year | About 30 core-seconds a game year, so 180 core-seconds, or 23 s on 8 cores | **Over the limit by about 5x, so run the rest in the background** |
| Growing a tree from seed to 60 when it's first needed | 42-67 s here in Python, perhaps 10-25 s on the PC in C++ | **Too slow to do as you walk** |
| Walking at 1.5 m/s with full trees within 64 m | A band 128 m wide sweeps 192 m² a second. At 32-66 birches/ha (4,222 over the 63.6 ha circle, or over the up to 133 ha of cells that hold it), that's 0.6-1.3 new birches a second | **Don't promote trees by distance** |
| Stage swaps, 14 stages over 100 years | A tree swaps about every 7 game years, or 14 real months. All 31,573: about one every 20 real minutes | **Rare, except after time away** |

The game's budgets don't name a share for trees, and these sums give trees all 8 cores, so they're upper limits, not allowances. The 1.5 ms commit slice is much smaller than the 0.05 s swap measured in the editor (`docs/unreal.md` section 7), and that test was one mesh, not an instance in the game's instanced cells. So one swap could be a dropped frame, and this needs testing.

### The schedule

| Tier | Which trees | State per tree | How often | Cost (estimate) |
|---|---|---|---|---|
| **Full** | Trees in touched places and round the player's home, by a memory dial: about 50-150 | 7-12 MB, and 5 MB compressed on disk | Yearly, staggered by the tree's id: with 100 trees, one every 15 real hours | 0.1 s on one worker, plus 55 MB of light grid while it runs |
| **Summary** | Other trees in touched places, felled or marked by the player | 32-256 bytes | Yearly, as a batch | Milliseconds |
| **Generated** | Everything else in reach: about 31,000 | Nothing stored: a function of seed, place and date | When a cell streams in | The game estimates 20-50 ns a tree |

**Between yearly steps,** height, stem and mass run on by date, as a straight line to next year's values. Colour by season is already live in the material (`docs/unreal.md` section 6).

**When a player returns:**
1. Summaries first, in milliseconds.
2. Full trees nearest first, year by year and place by place so neighbours stay in step, until the fade's limit runs out.
3. The rest on one or two workers in the background, while the player walks. A tree that's behind shows its last stage, which is a few years out at worst.
4. Stage swaps wait for a tree to be off screen, or happen behind the fade.
5. The death jump (30 game years) is the same, with summaries doing most of it.

**A tree becoming full** (the player starts work beside it, or fells it): take the closest pre-grown tree of its age from a library of saved states, and carry on from there. Growing it from seed takes too long, and its neighbours' history is gone anyway.

### What each shortcut loses

| Shortcut | What's lost | Evidence |
|---|---|---|
| Summary tree or table row | No branches and no real crown. A tree can't lean to a gap or respond to its neighbours beyond its table's density class. The forest's means should be right, and any one tree can be wrong | **Not tested.** Needs a test against plots before it's trusted. iLand and others do this (`reports/speed_research.md`), but it's a different model |
| A full tree with neighbours summarised | Real gaps in neighbours' crowns, and being overtopped. A stand tree can't show suppression or death | Stand trees against plots, older settings, 20 trees and 5 plots, at 50, 60: LAI 4.40, 4.24 against 4.35, 4.17; light 18.3, 18.6 % against 18.5, 19.5 %. Different runs, read from the overnight log. Real neighbours as summaries aren't tested |
| Pre-built stages | **The limbs you see aren't that tree's limbs.** Height and stem can be right by scale; limb layout, lean and scars come from the library tree | `docs/unreal.md` section 7; nothing measured |
| Scaling a stage between swaps | Limbs, bark and leaves scale with it, and a stem jumps a little at each swap | `docs/unreal.md` section 6; size not measured |
| Light by rows | Nothing that shows. Same sums in another order, so a seed makes a different tree | 5 plots at 50, 60: stems 902, 622 against 886, 620; LAI 4.40, 4.14 against 4.35, 4.17; inside the spread between plots |
| Dead nodes dropped | Nothing in the means; 3 of 5 plots differ in LAI from ages 47-58. An exported tree can't use it, since replay needs the dead nodes | 5 plots at 50, 60: stems 886, 614 against 886, 620; light 18.46, 19.75 % against 18.46, 19.54 % |
| Single precision | Nothing seen: 0 of 28 rows at z 2 or more across ages 10, 30, 50, 60, with 8 seeds a side. That's a first look. Crown width at 60 fell 7.6 % (z -1.0), so it needs 20 seeds | Measured here, stand trees, no plots. At 60: stem 27.6 against 28.0 cm; LAI 3.99 against 4.02; crown width 6.61 against 6.11 m |
| Light field kept 2 years | **Too much: don't use it.** Stem wood +16 %, crown width -9.5 % | `reports/speed_research.md` |
| 0.2 m light grid | **Too much on default:** crown width +12 %, upper limbs -11 %. 0.15 m showed nothing on Test A, and it's untested on current settings | `reports/speed_research.md` |
| Catching up late | A few years' lag in what's shown until it's done. Final numbers are the same if neighbours step together | By design; not run |
| Taking a tree from a library when it becomes full | Its own history. It didn't really grow beside these neighbours | By design; not run |

### Options for meshes and science

Nanite can't be built in a shipped game: only the editor has the builder (`docs/unreal.md` section 7, read in Unreal's source). The earlier recommendation was pre-built stages swapped live, with the science live. **You haven't decided, and A's weak point needs saying plainly: with stages, the branch-level science doesn't change the limbs you see.** It sets the numbers behind them, and which stage and scale to pick.

| | A. Stages, with full science in touched places (earlier recommendation) | B. Stages and summaries only | C. A few live-built meshes near home, stages elsewhere |
|---|---|---|---|
| What you see | Library trees, chosen and scaled by the science | The same | Near home, that tree's real limbs, at about 16,000 triangles against about 2.2 million. Library trees elsewhere |
| Accurate in | Whole-tree numbers for every tree. In touched places, real competition and logs with the model's stem | Whole-tree numbers, as good as the tables | As A, and the limb layout for those few trees |
| Not accurate in | Limb layout | Limb layout, and any response beyond the tables. A clearing's edge trees don't change except by table | Near trees look plainer than the stages round them |
| Port | Everything in section 1's game side, plus summaries | A table reader and a stage picker, perhaps 1,500 lines | As A, plus `mesh.py`, some of `game_unreal.py` and `appearance.py`, about 2,000 lines of Python more |
| Memory | 50-150 full trees, and the library | Almost nothing, and the library | As A, plus each unique mesh |
| Rendering | Nanite, with Lumen and virtual shadows | The same | No Nanite: Lumen by hardware tracing, and virtual shadows cost more |
| Untested | Instance swaps, cooked size, a voxel build | The same, and how well tables match plots | All of it at this size |
| Effort, an estimate | 50-90 agent-days | 3-4 weeks | A plus 8-15 agent-days |

**My view:** B first. It's a subset of A, it gives a working forest and most of the look soonest, and it doesn't wait on the tree settling beyond the tables. Then add A's full science if you want touched places to respond for real. Choose C only if you find you must see the real limbs near home. All of them need the same stage library: about 400 MB for 14 stages of one tree and 2 GB for five, in the editor. The cooked size isn't measured.

## 4. Proving the port is right

**Don't aim for whole runs to match bit for bit.** Parts can match, and most of what I ported did, on one machine with one compiler. A whole run can't match cheaply, for these reasons:
- numpy's `@` and `tensordot` go through OpenBLAS.
- numpy's maths differs by CPU.
- MSVC's C library differs from Linux's. The game's own `Architecture.md` 2.9 says so, and calls a portable maths layer 2-4 days of work, budgeted only if co-op or catching up on a server is ever planned.

**Do reproduce the random numbers.** That part is cheap, and it's what makes tree-by-tree tests work. The model has 13 named streams, all numpy's PCG64 from a SeedSequence, using `random`, `uniform`, `normal`, `beta`, `choice` and `permutation`. The algorithms are public, and it's perhaps 300 lines. Each tree keeps its generators' state, which suits the game's rules: a split step still equals the whole, and thread order doesn't matter. `Architecture.md` asks for `Hash(seed, entity, day)`, so that needs agreeing with whoever owns it, but seeding each stream from that hash fits.

**Why tree-by-tree works.** I measured how fast a tiny change spreads. Stand trees, `resource.alpha` changed by the share shown, against the same seed:

| Seed | Change | First year a rounded yearly figure differs | Height, stem, leaf area at 30, % off | At 50 | At 60 |
|---|---|---|---|---|---|
| 1 | 1e-15 | 56 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 2 | 1e-15 | Never, to 60 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 3 | 1e-15 | Never, to 60 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 1 | 1e-12 | 56 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| 2 | 1e-12 | 54 | 0, 0, 0 | 0, 0, 0 | 0, -0.15, -0.75 |
| 3 | 1e-12 | 47 | 0, 0, 0 | 0, +0.02, -0.31 | -0.01, -0.13, +2.44 |
| 1 | 1e-6 | 15 | 0, -0.52, -4.70 | 0, -4.44, +0.13 | 0, -3.43, +5.05 |
| 2 | 1e-6 | 14 | 0, +0.56, +0.02 | 0, +4.05, +4.21 | 0, +6.09, +6.32 |
| 3 | 1e-6 | 16 | 0, -0.60, -4.75 | -0.01, -1.02, -2.83 | 0, -0.86, +2.22 |

So rounding-sized differences stay out of sight for decades, and a millionth doesn't. (Height follows the curve on these settings, so it barely moves.) A C++ tree with the same draws and strict builds should track its Python twin to about age 45 or more. If it parts sooner, that's most likely a bug, not chaos. This is 3 seeds on one setting, so it needs repeating at the freeze. Single precision and light by rows make differences nearer the 1e-6 row, so they're new draws and can only be judged as ensembles.

### The ladder: checks before C++ replaces anything

Every check runs on the settings actually in use. That matters: the compiled carbon sum drifted from the model once, and its tests passed because they only ran on settings where the drifted path was off (`reports/speed_research.md`).

| # | Check | How | Must hold |
|---|---|---|---|
| 1 | Data | C++ dumps every value it read; compare with Python's `flatten` | Exact. An unknown key or a switch it can't honour stops the load |
| 2 | Random numbers | Vectors from numpy, all 13 streams | Exact bits |
| 3 | Pieces | Arrays recorded from real trees at ages 3, 10, 30, 50, 60. `tools/cpp_kernels.py` is the prototype | Exact bits where the original is plain loops or numba. Within 1e-12 where it goes through OpenBLAS or vectorised maths. The game's vectors can hold these |
| 4 | **One year from the same state** | From a saved Python state at every age and the same draws, run one year in C++; compare every array. 20 seeds x 60 years, then plots | Integers, births and deaths exact. Numbers within 1e-9. A single step isn't chaotic, so any miss is a bug or a threshold it can be shown to sit on |
| 5 | Same seed, whole life | Same draws from germination, 20 seeds and 5 plots | No visible difference in yearly figures before age 40 on at least 18 of 20. Any earlier parting gets traced |
| 6 | **Forest, as ensembles** | 40 trees and 10 plots each side, plus a second Python draw as the chance line. `tools/speed_accuracy.py`, `tools/gate.py`, `tools/scorecard.py`. Ages 10, 30, 50 and 60 | The same PASS or FAIL on every target. Under 1 row in 20 at z 2 or more. A row over the line reruns once on new seeds, and only a repeat blocks, as the gate does now |
| 7 | Sensitivity | `tools/noise_floor.py`'s test on both | Same size of noise. Python's last reading, older settings: median 10.8 %, largest 28.1 % |
| 8 | Power of the test itself | C++ with a planted fault, say `resource.alpha` x 1.02, and with a shoot rule broken | Checks 4 and 6 must catch them. A test that can't fail proves nothing |
| 9 | The game's rules | `Tests/Core`: 1, 2 and 8 threads identical; a step split in two equals the whole; a save and load changes nothing; a digest per compiler | All of them, on MSVC and g++ |
| 10 | Cost | In a packaged build on the PC: time, memory and frame spikes against section 3 | Inside whatever you set |

**Golden runs:** `tools/golden.py` stays as Python's own lock, so any change to Python's output shows. C++ gets its own digests, one per compiler, in the game's existing way. The two aren't compared with each other. Checks 3-6 link them.

**One model afterwards.** Keep Python as the tuner, with checks 3-6 running on any change to its logic, until C++ can be called from Python (ctypes does this in `tools/cpp_kernels.py`). Then the tools can drive one model, and the numpy forms can retire.

## 5. Species as data, and keeping tuning out of the way

**The route.** `species/<name>.yaml`, `reference/<name>/labels.yaml` and `targets.yaml` stay the source (`docs/adding_a_species.md`). A new offline tool writes `Content/Data/Science/<name>.json` in the game's envelope, read through `science::Library` with its strict reads, and adds the name to `trees.json#/species_list`. The JSON carries the accuracy line too. `species_schema.py`'s table generates the C++ struct and reader, so no value is ever typed into C++.

**What has to be fixed first. Measured from the files:**

| Finding | Number | What to do |
|---|---|---|
| Entries in the species file | 756, of which 275 are appearance | |
| Not in `species_schema.py` | 382 | Add them, or a generated reader misses them |
| Values by label | 89 sourced, 72 TUNED, 426 VERIFY | Carry the labels; they don't block a port |
| Settings | 169, of which 57 are on/off and 18 are on in the file. Current runs set 11 more switches, and 6 speed settings | Each one either adopted or removed at the freeze |
| `getattr(x, "name", default)` in model code | About 234 (grep; some only serve old saves) | Move any that hold a value into the species file. Otherwise a hidden number gets ported twice |
| Climate in the species file | `soil_water_balance`, storm direction | Belongs in the place: the game has `DriverSource` and `RegionId` |

**What data can't do yet.** `docs/adding_a_species.md` lists these: leaves fall every year, and there's one side bud per node. So **pine and spruce can't be made, and they're 22,857 of the 27,079 mature trees in reach.** Those need code in Python first, then in C++. Fix them before the port, or C++ inherits them. Until then the other species stay on the game's own models.

**Keeping tuning out of the way:**
- **Values can keep changing for good.** Once every value comes from data, retuning needs a data file and a re-run of checks 1 and 6, not new C++. So the port waits for **logic** to settle, not for numbers.
- **What "settled" means,** for you to confirm: you accept the tree by eye at several ages; the scorecard passes at 50 and 60 on 20 trees and 10 plots; two weeks with no logic change in `growth.py`, `roots.py` or `plot.py`; and each off-by-default branch adopted or removed.
- **Order of work:** parts that barely change first (`hydraulics.py` and `kernels.py` have had 0 commits since the reset, `mechanics.py` and `structure.py` 2 each, `light.py` 3), and `growth.py` (30) last.
- **A switch it doesn't know stops the load.** C++ refuses a species file that turns on anything unported, and says which. That way a new Python option can't silently do nothing in the game.
- **The bark and the rest of the ageing stay data.** Stages bake them from `appearance`, and the material reads `stage age - UV2.x` (`docs/unreal.md`). Addition 9 in that file's table gives the third bark layer.

## 6. Steps, effort and risks

Effort is my rough estimate in agent-days. It isn't measured, and none of it includes waiting for you or for the PC.

| # | Step | Effort | When | Needs |
|---|---|---|---|---|
| 0 | You choose an option, a memory share and what "1:1" covers | | Now | You |
| 1 | Measure the game's side: memory in play, a cooked stage's size, swapping an instance, a voxel build | 2-3 | Now, when the PC is free | Your say, and Unreal on the PC |
| 2 | Species route: the YAML-to-JSON tool now; the schema's 382 missing entries, the 234 fallbacks and climate once Crown 2 has merged | 3-5 | Now, then after Crown 2 | |
| 3 | Recording tool: states, arrays and draws from any year, Python only | 2-3 | Now | |
| 4 | Random numbers in C++, with vectors from numpy | 1-2 | Now | |
| 5 | Trial of summaries: tables from existing plots, tested against plots | 3-5 | Now as a trial; again at the freeze | Server |
| 6 | Stage library: grow, export, import; 14 stages x variants | 3-5 of machine time | Once the look settles | PC, 7-11 GB per heavy import |
| 7 | A table reader and a stage picker in the game. **Option B is done here** | 2-5 | Once 5 and 6 pass | PC builds; the game's flora streaming, which exists |
| 8 | Stable core: node store, passes, light with an FFT, water, mechanics, with checks 3 and 4 | 5-8 | **Wait:** when you say port | |
| 9 | Growth and roots: `growth.py`, `roots.py`, the frame and height limit | 12-20 | **Wait:** tree settled | |
| 10 | Plot: shared light, soil, thinning, spread, damage | 6-10 | **Wait** | |
| 11 | The proof: checks 5-8, on the server | 5-10 | **Wait** | Server |
| 12 | In the game: the scheduler's step, saves, threads, the view, swaps, checks 9-10 | 8-15 | **Wait**, and it needs the game's R9 and R10b first | PC builds |
| 13 | Live-built meshes, option C only | 8-15 | **Wait** | PC |

So B is steps 1, 2, 5, 6 and 7, 13-23 agent-days, or about 3-4 weeks. A is steps 1-12, about 50-90 agent-days. C adds step 13.

**Nothing in steps 8-13 should start until you say so.** Steps 1-7 are groundwork, and none of them is the port.

### Biggest risks

1. **The model moves under the port.** `growth.py` had 30 commits and 772 changed lines in two days, and Crown 2 is at work now. Porting early means porting twice. Hence the wait, and logic-only freezing.
2. **Summaries don't match real plots.** Nothing's tested, and most of the forest would rest on them. Step 5 finds out cheaply, before any C++.
3. **A copy drifts from the model.** It has happened once already. Hence checks on the settings in use, and one model afterwards.
4. **Memory.** The game's limit is 6 GB, the PC has 16 GB, and I don't know what the game uses in play. The count of full trees could be far lower than 50-150.
5. **The science doesn't show.** With stages, a lot of C++ might change little you can see. Decide that in step 0, before building it.
6. **Compiler and FFT.** The sweep needs vectorising, and MSVC is untested. The game's FFT (`water/Surface.cpp`) is radix-2 only, while the light grids are 94, 126, 189 and 316 across. So it needs a mixed-radix FFT, such as pocketfft (BSD, the one numpy uses), or grid sizes that change results.
7. **Other species.** Pine and spruce need model changes first (section 5).
8. **Stage library size and swaps.** Cooked size is unmeasured, and swapping instances in the game's cells is untested. Imports need 7-11 GB each on a 16 GB PC that's for games.
9. **ARM here, x86 there.** Everything measured here needs measuring again on the PC, and PC and server results for the science stay apart.
10. **The game's roadmap.** Live trees need its World and its scheduler. `USimSubsystem` calls itself a skeleton (R9a), and there's no scheduler, `TreeState` or `StepYear` in its source yet. `Architecture.md` puts the scheduler (R10b) before Growth.

## Measured, and estimated

**Measured here, on the server:** every stage table, the mesh table, the memory table except rows marked as a sum, disk sizes, the six C++ pieces with their bits, how fast a tiny change spreads, single precision against double (8 seeds a side), lines reached, and species file counts.

**Measured earlier by others, read not rerun:** `light_rows` and `drop_dead` on plots, `node_v1_*` stand trees against plots (`reports/overnight_log.md` at 7c512a6), light every 2 years, grid sizes, the noise floor, and swap time and stage sizes (`docs/unreal.md`). The game's numbers are from its own files and its 2026-10-31 log; nothing was run there.

**Sums over measured arrays, not runs:** live-only memory, and live single-precision memory.

**Estimates:** all whole-model C++ gains; the factor for the game's PC; full trees per GB after C++; every catch-up count; the tier sizes; lines of C++; all effort; shoots and roots gaining 3-10x. The game's own figures for its planned `TreeState` are its estimates too.

**Couldn't measure:**
- Anything on the game's PC or under MSVC, because the PC is for games.
- Anything in Unreal: cooked sizes, swaps in instanced cells, voxels, frame times.
- Summaries against plots, since none exist yet.
- Single precision on plots, or with 20 seeds.
- `_grow_shoots` or the roots in C++: too large to port cheaply for a measure. They'd need the draws replayed.
- Crown 2's settings, which aren't in 5f07fae.
