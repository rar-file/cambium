# Plan: porting the birch model to C++, and what it costs now

Plan and measurement only. Nothing has been ported, nothing in `treegen/` or in the game was changed, and Unreal wasn't launched.

**Revised 2026-11-07, after the maintainer's answer:** every tree is its own tree, near or far, and trees can be felled and branches cut and sliced. Section 3 and the steps in section 6 are new, and the summary below is rewritten for it.

## The short version

- **What you asked for:** every tree grows as itself, stage by stage. Near you it has real limbs you can cut, slice and fell, and it drops branches. Far away it keeps growing as itself in a lighter form, and remembers your cuts.
- **Today, on one server core:** an old stand tree takes about 2 s for its year. In a forest plot an age-60 tree takes about 0.6 s, and a 1000 m² plot about 45 s a year.
- **Time isn't the limit.** A game year lasts 61 real days, so even every tree in reach in full would use under 0.4 % of one core.
- **C++ alone is no miracle:** about 2.5-3x on a plot and 1.3x on one big tree (estimates, built on six small pieces I ported and measured).
- **Memory and disk are the limits.** An old tree's whole state is 7-10 MB, or 3.5-5 MB compressed. 31,573 trees in reach would need about 110-170 GB.
- **The far form, measured:** a tree's limbs from 1 cm up, with every year's rings, come to about 0.06-0.1 MB at 60. That's about 2-3 GB for every tree in reach. At 60 fewer than 1 node in 13 is that thick, and about half the leaves sit on wood under 10 years old. So a far tree can keep its stem, limbs, cuts, scars and rings exactly, and have its twigs regrown when you come back. They'd be alike, but not the very same twigs.
- **That needs a lighter growth model, which doesn't exist yet.** It's the biggest new piece of work. It's model work in Python, tested against the full model, before any port.
- **Cutting:** the model already kills a limb from a point, keeps its stub, and regrows a leader. It knows which limb dies and when, which gives the order limbs die in. Missing: cuts anywhere, handing cut pieces over as objects, wounds closing, dead branches hanging before they drop, and where they land. Those need sources, or will be guessed and marked.
- **Meshes must be built live,** because cuts change them, and a shipped game can't build Nanite. Full detail is 2.2 million triangles and about 100 MB of video memory a tree (estimate), so only for the tree you're working on. Near trees can take 64,000 triangles (about 4-5 MB). Far trees need under about 30 KB each, or a shared look at a distance.
- **The port can be proved right.** With the same random numbers, a rounding-sized change stayed invisible until about age 47-56 on 3 seeds, so Python and C++ can be compared tree by tree.
- **Don't start the port yet.** `growth.py` changed in 30 commits in two days. Python work on cuts and the far form, and some groundwork, can start now (section 6).
- **Rough effort, an estimate:** about 100-170 agent-days in all.

**Still open, and not assumed** (section 3 shows what each answer changes):
1. What "1:1 with life" covers: whole-tree numbers, or every limb and twig.
2. How much memory trees may have. You said measure first, and that needs the game run.
3. The speed shortcuts: `light_rows`, `drop_dead`, single precision.
4. Whether far trees may share a look beyond some distance, while keeping their own data and growth.

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
| `appearance.py` | 392 | 283 | 0 | 4 | How each part looks at an age | **Game, in part:** each part's bark stage and thickness by age, for the materials and for cut faces |
| `mesh.py` | 1,054 | 825 | 55 | 8 | Tube meshes | **Game:** meshes must be built live, since cuts change them |
| `game.py` | 600 | 470 | 0 | 6 | Levels of detail | **Game, in part:** wood data and leaf cards for live levels. Texture baking stays offline |
| `game_unreal.py` | 1,342 | 1,027 | 0 | 8 | Export for the game | **Game, in part:** UV channels, wind data, leaves and the foot. Files and folders stay offline |
| `textures.py` | 924 | 701 | 0 | 5 | Bark and leaf textures | Offline |
| `export.py` | 822 | 666 | 60 | 4 | File writers | Offline |
| `look_render.py` | 538 | 446 | 0 | 3 | Software renderer | Offline |
| `preview.py` | 443 | 365 | 36 | 0 | Silhouettes | Offline |
| `runhash.py`, `machine.py`, `threads.py`, `__init__.py` | 206 | 140 | 45 | 0 | Digests, machine details, thread setting | Offline; not needed in the game |

**For growth in the game: 7,746 lines, of which 5,765 are code and about 4,000 are reached, plus the 627 compiled lines.** So on today's settings the port is about 4,500 lines of Python, or perhaps 8,000-10,000 lines of C++ (an estimate). About 490 lines of `growth.py` weren't reached. Options that stay off at the freeze needn't be ported at all.

**Live meshes add about 1,500-2,500 lines of Python** from `mesh.py`, `appearance.py`, `game.py` and `game_unreal.py` (an estimate of the parts needed). On top of that come the far form, the lighter model and cuts, which don't exist yet (section 3).

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
| Thousands of trees at once | No help: at about 140 trees per GB, 4,222 birches is 30 GB | Far forms (section 3.3) |
| Meshes in a shipped game | No help: Nanite can't be built there | Plain meshes built live, by distance (section 3.6) |
| Far trees staying themselves | No help | A far form and a lighter model (section 3.3) |

## 3. Every tree its own tree: growing live, far forms, cutting, meshes

**What was asked:** trees that grow stage by stage, branches that drop to the ground, trees that can be felled, with branches cut off and sliced, and every tree its own tree, near or far.

**The coordinator's reading** (`DECISIONS.md` row 91 on master):
- Each tree keeps its own identity and growth everywhere.
- Near the player it's full detail, with real limbs that can be cut, sliced and felled, and that shed twigs and branches to the ground.
- Far away it keeps growing as itself in a lighter form, never a shared copy, and cuts are remembered.

This replaces the earlier choice between pre-built stages and summaries. Trees the player can cut need meshes built live. Every tree needs a form of its own that lasts while nobody is near.

**Still open, and not assumed here.** This is what each answer would change:

| Open question | One answer | The other |
|---|---|---|
| What "1:1 with life" covers | Whole-tree numbers (height, stem, crown, mass, the forest thinning): a far form with only main limbs is enough, and twigs can be regrown | Every limb and twig: far trees must keep their whole state, about 50 times the disk (section 3.3), and grow on with the full model |
| Memory for trees (to be measured first, which needs the game run) | 0.5 GB: about 30-70 trees in full near the player (section 3.7) | 2 GB: about 120-290 |
| Speed shortcuts (not decided yet) | None: plots about 1.4x slower and memory about 2x more than with them (section 2) | `light_rows`, `drop_dead`, single precision: faster and smaller, at the costs in section 3.8. `drop_dead` would have to hand a shed branch over as an object before deleting it |
| How far trees look | Each with a mesh of its own, built from its own limbs: about 0.8-9 GB of video memory for 31,000 trees (estimate), too much at the top end | Its own data and growth, but a shared look beyond some distance: cheap, and the identity is still kept in the data |

### 3.1 The game's own numbers

| What | Number | Where |
|---|---|---|
| Time | 6x, so a game year is 60.9 real days. It runs while the game's closed too | `<game>/time/Time.h:198`; `Decisions.md` round 3 |
| Frame | Game thread at most 9 ms, of which 1.5 ms for streamed commits. No frame over 50 ms | `Architecture.md` 2.10 |
| Threads | `UE::Tasks`, at most cores - 2, no raw threads. The PC is a 5800X, 8 cores and 16 threads | `Architecture.md` 2.3; `CLAUDE.md` |
| Memory | Budget 6 GB packaged, 6.5 GB video. Its audit found nothing logs it. The PC has 16 GB | `Architecture.md` 2.10, 3.3; `CLAUDE.md` |
| Catching up | Under 1 s after a real month, under 5 s after a real year, eyes closed | `Architecture.md` 2.5 |
| Trees in reach | 4,222 mature birches; 27,079 mature trees of all kinds; 31,573 with young trees and saplings. At the birth site, in the 2026-10-31 log | `Saved/Logs/<Game>.log:1683` |
| Streaming | Mature trees reach 450 m on 256 m cells; bodies only within 96 m; a tree cell takes about 10 ms to draw, one a frame | `flora.json`; `Architecture.md` 2.4; `CLAUDE.md` |
| What's simulated today | Only touched places, on 64 m cells. Untouched land is a pure function of seed, place and date. **The maintainer's answer changes this:** every tree now has a life of its own | `Decisions.md` round 8; `03-clock-persistence.md` |
| Wood after felling | The game's own wood science covers felling, cutting by swing, splitting, drying, checking and decay | `Content/Data/Science/wood.json`; `Research/Wave1/04-wood.md` |
| Physics | The core decides what happens; Unreal moves the bodies and reports when they settle | `Architecture.md` 2.3 |

Tree density near the player is an estimate. It's 32-66 birches/ha, or 240-500 trees of all kinds/ha: 4,222 birches (31,573 trees) over the 63.6 ha circle of reach, or over the up to 133 ha of cells that hold it.

### 3.2 One tree, three forms

| Form | Where | What it holds | How it grows | Size |
|---|---|---|---|---|
| **Near** | Within reach of the axe and the eye: about 30-100 m | The whole state: every living node, stubs, rings, random streams, carbon stores, its cut log | The full model, once a game year | About 7-17 MB in memory (estimate, from section 2) |
| **Far** | Out to 450 m and beyond, for as long as the tree lives | Its limb skeleton with every year's rings, the stubs on it, what the left-off twigs carried, its stores, streams and cut log | **A lighter model that doesn't exist yet.** It grows the skeleton from what its twigs carried, and its twigs are regrown when the player comes back | 0.025-0.23 MB on disk at 60, measured below |
| **Not yet seen** | Land the player hasn't reached | Nothing stored: it's a function of seed, place and date | When first seen, grown from germination by the lighter model to its age. It's its own tree from then on | Nothing |

The game's design already has the shape for this: places catch up lazily, every rate is per game hour, and untouched land is generated for its date. What's new is that a far tree is stored, as itself, once seen.

### 3.3 The far form, measured

**Stand trees, mean of 3 seeds.** Measured on the server (`tools/cpp_cost.py far`). Sizes are sums over the model's own arrays, written as a port might store them. A working far form doesn't exist yet. "Quantised" means position from the parent in mm, radius in 0.02 mm, and years in a byte. "Rings" are each node's ring width for every year of its life, at 0.01 mm.

| Per tree | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| Whole state: living nodes and stubs, all arrays, single precision, MB | 0.134 | 4.93 | 10.06 | 10.37 |
| The same, compressed, MB | 0.062 | 2.60 | 5.26 | 5.33 |
| Skeleton, living wood at least 0.5 cm, nodes | 147 | 2,997 | 11,773 | 14,267 |
| Skeleton at least 0.5 cm, quantised and compressed, MB | 0.001 | 0.021 | 0.077 | 0.094 |
| Its rings, compressed, MB | 0.001 | 0.022 | 0.090 | 0.126 |
| Skeleton, living wood at least 1 cm, nodes | 98 | 1,025 | 4,154 | 5,321 |
| Skeleton at least 1 cm, quantised and compressed, MB | 0.000 | 0.006 | 0.028 | 0.037 |
| Its rings, compressed, MB | 0.000 | 0.010 | 0.038 | 0.053 |
| Skeleton, living wood at least 2 cm, nodes | 21 | 561 | 1,461 | 1,928 |
| Skeleton at least 2 cm, quantised and compressed, MB | 0.000 | 0.003 | 0.008 | 0.012 |
| Its rings, compressed, MB | 0.000 | 0.006 | 0.016 | 0.021 |
| Everything else in today's model, gzip, MB (an upper bound) | 0.013 | 0.28 | 0.68 | 0.77 |
| Loading a whole pickled tree, Python, s | 0.003 | 0.012 | 0.028 | 0.033 |
| Decompressing the whole state's arrays, s | 0.000 | 0.018 | 0.036 | 0.037 |

At 60, seed 1 had 48,893 living crown nodes, 19,356 living root nodes, and 683 dead stubs on living wood (knots).

"Everything else" is mostly per-node and per-shoot lists that a skeleton wouldn't keep. What a far tree really needs beside its skeleton is its carbon store, random streams, frame plan, leaders and counters. I estimate that at about 10 KB, but haven't measured it.

**Trees in a plot**, 1000 m², with thinning, spread and storms. Mean per living tree, measured. Plot trees keep no yearly radii, so there are no rings here.

| Per tree | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| Living trees in the plot | 1,426 | 304 | 101 | 73 |
| Whole state, single precision, MB | 0.039 | 1.16 | 4.52 | 6.72 |
| The same, compressed, MB | 0.018 | 0.61 | 2.37 | 3.52 |
| Largest tree, compressed, MB | 0.05 | 1.72 | 4.73 | 7.83 |
| Whole plot, compressed, MB | 25.5 | 185.5 | 239.7 | 256.7 |
| Skeleton at least 0.5 cm, quantised and compressed, MB | 0.000 | 0.007 | 0.032 | 0.053 |
| Skeleton at least 1 cm, nodes | 24 | 563 | 1,845 | 3,056 |
| Skeleton at least 1 cm, quantised and compressed, MB | 0.000 | 0.003 | 0.011 | 0.019 |
| Skeleton at least 2 cm, quantised and compressed, MB | 0.000 | 0.001 | 0.004 | 0.006 |
| Loading a whole pickled tree, Python, s | 0.003 | 0.006 | 0.017 | 0.018 |
| Living leaves on wood under 10 years old | 100 % | 74 % | 75 % | 61 % |
| Shed that year: pieces under 5 mm at the base | 0.2 | 5.3 | 20.1 | 20.5 |
| Shed that year: pieces 0.5-2 cm | 0.0 | 0.4 | 3.4 | 4.6 |
| Shed that year: pieces over 2 cm (length, m) | 0.0 | 0.0 | 0.4 (5.9) | 0.6 (7.4) |

**How fast a tree's fine parts turn over.** Stand trees, mean of 3 seeds, measured:

| Share | Age 10 | Age 30 | Age 50 | Age 60 |
|---|---|---|---|---|
| Living nodes on wood under 3 years old | 71 % | 53 % | 22 % | 18 % |
| Living leaves on wood under 3 years old | 63 % | 48 % | 21 % | 16 % |
| Living leaves on wood under 5 years old | 81 % | 65 % | 32 % | 24 % |
| Living leaves on wood under 10 years old | 100 % | 93 % | 59 % | 45 % |
| Living nodes at least 1 cm thick | 8.1 % | 2.5 % | 5.5 % | 7.2 % |

An old tree's identity is its limbs: at 60, fewer than 1 node in 13 is 1 cm thick, in stand trees and plot trees alike. About half its leaves (45 % in stand trees, 61 % in plot trees) sit on wood under 10 years old. So a far form can keep the limbs exactly and let the twigs be regrown. A tree that comes back will have the same stem, limbs, cuts, scars and rings. Its twigs will be new ones that the model grew on the same limbs, in the same light: alike, but not the twigs it would have had. **Whether that's close enough is untested.** The test is a round trip (section 4).

**The far forms side by side.** Sizes are measured at 60, for stand trees and then plot trees. Rings for plot trees are estimated from the stand trees' ratio, and stores are the 10 KB estimate. The column for all trees in reach is an estimate, assuming every tree is a birch of that size.

| Far form | Per tree at 60, stand / plot | All 31,573 trees in reach | Comes back as | Grows on by |
|---|---|---|---|---|
| Whole state | 5.33 / 3.52 MB | About 110-170 GB | Exactly itself | The full model, about 0.1 s a tree-year on the PC (estimate): 0.06 % of one core for all of them |
| Skeleton at least 0.5 cm, rings, stores | About 0.23 / 0.14 MB | About 4-7 GB | Limbs from 0.5 cm, stem, cuts, scars and rings exact; twigs regrown | The lighter model, which needs building |
| Skeleton at least 1 cm, rings, stores | About 0.10 / 0.06 MB | About 2-3 GB | The same from 1 cm | The same |
| Skeleton at least 2 cm, rings, stores | About 0.04 / 0.025 MB | About 0.8-1.3 GB | Main limbs exact; branches under 2 cm regrown too | The same |
| Seed and cut log only | About 100 bytes (estimate) | About 3 MB | Itself only if regrown together with its neighbours, since a forest tree grows in their shade. Alone it's a different tree | Regrowing from seed: 10-25 s a tree (estimate) |

**Hybrid:** whole state for trees within about 100 m and for any the player has cut, and a 1 cm skeleton beyond. About 750-1,600 trees x 5 MB is 4-8 GB of disk (estimate), plus about 3 GB for the rest. A tree moving out loses its twig detail at that moment.

### 3.4 Bringing a tree back to full detail

| Step | Time | Kind |
|---|---|---|
| Read and decompress a whole state | 0.03-0.04 s in Python at 60 | Measured |
| Regrow twigs onto a skeleton: a few years of the full model on that tree | About 0.5 s on the PC, for 5 years at 0.1 s | **Estimate: the method doesn't exist** |
| Catch up the years since it was last full, if the far model and the full one differ | 0.1 s a year | Estimate |
| Build its mesh at 64,000 triangles | 0.65 s in Python, measured; about 0.1-0.2 s in C++ | Estimate for C++ |
| Build its mesh at full detail (2.2 million triangles at 60) | 9.5 s in Python, measured; about 1-3 s in C++ | Estimate for C++ |

**Doing it ahead as the player walks** (estimates):
- At 1.5 m/s, a ring 100 m out with a 200 m wide band brings in 300 m² a second. That's 1-2 birches, or 7-15 trees of all kinds, a second.
- With 64,000-triangle meshes and twigs regrown (about 0.7 s a tree on one worker) and 6 of the PC's workers, that's about 8 trees a second. **So birch alone is easy at walking pace. All species is borderline, and running isn't covered.** Then trees keep their middle form longer, which is plainer, never wrong.
- Full detail (about 1-3 s a tree) would be built only for the tree being worked on, once the player starts on it.

### 3.5 Cutting, felling, slicing and falling branches

What the model already does, read in its code, and what's missing.

| Needed | The model has | Missing | Basis for what's missing |
|---|---|---|---|
| A cut limb stops growing | Shedding kills a whole limb from a node (`growth.py` `_shed`, lines 1482-1499), keeping its pipes in the parent as heartwood. Browsing (lines 344-431) and a snapped top (`damage.py` `apply_top_break`, lines 426-473) do the same | A cut at any node, or part way along one; a cut log the far form keeps; the cut piece handed over | Mechanism in place; a cut is a new caller |
| The tree's response | Next year's light, water, carbon, rings and bud fates follow from the leaves and buds it lost. A lost leader or top gets replacement leaders from the buds below. Limbs can take over the top (`_reiterate`) | Sprouts from a wound, and from a stump after felling. Birch sprouts from stumps; the model has nothing for it | **Guessed** until a source is read; none has been |
| The wound | Dead stubs on living wood stay, with their place and size (683 at 60) | The wound closing year by year, a stub dying back, decay getting in | **Guessed**: no birch source read |
| Branches dropping to the floor | Which limb dies and when comes from light and carbon, and every node keeps its death year, so the order limbs die in is there (`tools/tree_table.py shed_events`). Measured falls a year at 50, 60: a stand tree sheds 9.3, 6.7 branches 0.5-2 cm (45, 29 m of them) and 0.3, 1.7 thicker than 2 cm (0.9, 12 m); a plot tree 3.4, 4.6 and 0.4, 0.6 | How long a dead branch hangs before it falls (the model drops it at once); where it lands; handing its shape over as an object. With `drop_dead` the shape is deleted, so it must be handed over first | **Guessed**: no birch source read for how long. Decay on the ground is the game's (`wood.json`) |
| Twigs and leaves to the floor | Twig sheds a year (24 a stand tree at 60, measured) and leaf mass (`carbon.leaf_dm_g`) | Feeding the game's litter layer, which has its own birch twig rule | The game's ground already draws litter |
| A felled stem becomes logs | The stem's taper, sapwood and heartwood area, wood density, knots (side limbs' births, deaths and sizes along the stem), bark thickness by age (`appearance.add_bark_radius`), roots and their anchorage (`roots.py`) | A stem-section call, giving radius, sapwood, rings and knots at a height. A stump. Which way it falls: Unreal moves the bodies, and storm falls already log a direction (`damage.py`) | Model data |
| Slicing shows rings | Yearly radii for every node, but only in runs that keep them (`radius_history`). Lean runs drop them | Keep rings for wood at least 0.5-1 cm in every run: 0.04-0.13 MB a tree at 60 (measured above); the heartwood line year by year; reaction wood is a growth rate, not a record | Model data |
| Cut pieces become objects | Any limb's nodes, radii and leaves at the moment it's cut | A hand-over format: shape, mass from wood density and leaves, green moisture from `wood.json` | The game's wood science takes it from there |
| Cuts are remembered far away | Nothing yet | A cut log in the far form, perhaps 16 bytes a cut (estimate), replayed onto the skeleton | |

**Counting what falls, an estimate:** if every tree in reach shed like a 60-year plot tree (stand trees shed about 3 times as many big pieces), that's about 19,000 branches thicker than 2 cm a game year, one every 4-5 real minutes. It's also about 800,000 twigs and small branches. Only pieces near the player should become objects. The rest become litter on the game's ground, by cell.

### 3.6 Meshes

**Every tree the player can touch needs its mesh built live,** because cuts and growth change it. A shipped game can't build Nanite (`docs/unreal.md` section 7, read in Unreal's source), so these meshes are plain meshes. Every triangle is drawn, virtual shadows cost more, and Lumen sees them by hardware tracing. Measured on the server, one stand tree at 60, Python:

| Level | Triangles | Vertices | File, MB | Build time, Python, s |
|---|---|---|---|---|
| Full detail | 2,156,095 | 1,820,636 | 174 | 9.5 (wood tube 5.6, leaves 2.0, bark relief and wood data 1.9) |
| About 200,000 (asked for 256,000) | 192,271 | 248,929 | 20.5 | 2.0 |
| 64,000 | 63,997 | 91,808 | 7.5 | 0.65 |
| 16,000 | 15,998 | | | 0.28 |

At 50 the levels are 2,199,240, 198,973 and 63,998 triangles.

**In video memory, an estimate:** about 40 bytes a vertex and 12 a triangle in the game's own format, which I haven't checked. That's about 100 MB for full detail, 12 MB at 200,000, 4.4 MB at 64,000 and about 1 MB at 16,000. Shared bark and leaf textures aren't counted.

**Rings by distance, all estimates:**

| Ring | Trees of all kinds (birches) | Mesh | Video memory |
|---|---|---|---|
| The tree being worked on | 1-3 | Full detail, with its cut faces | About 100-300 MB |
| Within 30 m | 70-140 (9-19) | 64,000 triangles | About 0.3-0.6 GB |
| 30-60 m | 200-430 (25-55) | 16,000 triangles | About 0.2-0.5 GB |
| 60-450 m | About 31,000 (4,200) | Under about 30 KB each, built from its own skeleton (trunk, main limbs, crown cards). Or a shared look | About 1 GB for its own; little for shared |

So if every tree has its own far mesh, the far ring alone takes about a sixth of the game's 6.5 GB of video memory. A shared far look is cheap, and it's the maintainer's call (the table at the start of section 3).

**Following cuts and growth:**
- The mesher already builds a tree in chunks (`mesh.build_mesh_chunks`). A cut rebuilds only its chunk and adds a cap showing the rings, which is new mesher work.
- Growth rebuilds each near tree once a game year (61 real days), off the game thread.
- Between years, the material can carry the year's ring growth and season, as it already carries ageing (`docs/unreal.md` sections 4 and 6).
- The game's own test copied a 16,000-triangle dynamic mesh into the editor in 0.07 s. Bigger meshes and a packaged game are untested.

### 3.7 What those numbers allow

All estimates, from the measured costs above.

| Question | Sum | Answer |
|---|---|---|
| Steady growth: all 31,573 trees in full, at today's Python rate for age 60 | 31,573 x 0.604 s = 19,000 core-seconds, against 5.26 million real seconds a game year | **Under 0.4 % of one core: time isn't the limit** |
| The same in far forms with the lighter model | Unknown until it's built; it walks about a tenth of the nodes | Smaller still |
| Full trees in memory, at 7-17 MB each (C++ with dead nodes dropped, single precision or not) | 0.5 GB: 30-70; 1 GB: 60-140; 2 GB: 120-290 | **Memory decides how far "near" reaches.** About 70-140 trees of all kinds stand within 30 m |
| Far forms on disk | 31,573 x 0.025-0.23 MB | **About 0.8-7 GB for the trees in reach**, and more as the player explores |
| Catching up after a real year away (6 game years) | 5 s x 8 real cores = 40 core-seconds; an old tree's year in C++ on the PC is about 0.07-0.15 s | About 45-95 full trees inside the fade. The rest catch up in the background, and the far forms' lighter steps are cheaper |
| Catching up after a real month | 8 core-seconds; half the trees step once | About 105-230 full trees |
| A first look at new land | Each tree grown from germination by the lighter model | Unknown until it's built. The full model would take 10-25 s a tree, far too slow |

### 3.8 What each shortcut loses

| Shortcut | What's lost | Evidence |
|---|---|---|
| A far form with a limb skeleton | The twigs. A tree comes back with the same limbs, cuts and rings and new twigs on them | Turnover measured above; the round trip **not tested** |
| A far form of only seed and cut log | The tree's real neighbours, unless they're regrown too | By the model's design: plot trees read one shared light field |
| A shared far look | Nothing in the data, only in the picture beyond that distance | By design |
| Light by rows | Nothing that shows. Same sums in another order, so a seed makes a different tree | 5 plots at 50, 60: stems 902, 622 against 886, 620; LAI 4.40, 4.14 against 4.35, 4.17; inside the spread between plots |
| Dead nodes dropped | Nothing in the means; 3 of 5 plots differ in LAI from ages 47-58. **A shed branch's shape is deleted, so it must be handed over first.** Replay for export needs the dead nodes | 5 plots at 50, 60: stems 886, 614 against 886, 620; light 18.46, 19.75 % against 18.46, 19.54 % |
| Single precision | Nothing seen: 0 of 28 rows at z 2 or more across ages 10, 30, 50, 60, with 8 seeds a side. That's a first look. Crown width at 60 fell 7.6 % (z -1.0), so it needs 20 seeds | Measured here, stand trees, no plots. At 60: stem 27.6 against 28.0 cm; LAI 3.99 against 4.02; crown width 6.61 against 6.11 m |
| A full tree with its neighbours as summaries | Real gaps in neighbours' crowns, and being overtopped | Stand trees against plots, older settings, 20 trees and 5 plots, at 50, 60: LAI 4.40, 4.24 against 4.35, 4.17; light 18.3, 18.6 % against 18.5, 19.5 %. Different runs, read from the overnight log |
| Light field kept 2 years | **Too much: don't use it.** Stem wood +16 %, crown width -9.5 % | `reports/speed_research.md` |
| 0.2 m light grid | **Too much on default:** crown width +12 %, upper limbs -11 %. 0.15 m showed nothing on Test A, and it's untested on current settings | `reports/speed_research.md` |
| Catching up late | A few years' lag in what's shown until it's done. Final numbers are the same if neighbours step together | By design; not run |

The pre-built stages from the earlier plan don't suit trees that can be cut. At most they could serve as the shared far look.

> **Superseded by DECISIONS.md row 91 (2026-11-07, on master).** Far away a tree keeps growing as itself in a lighter form, never a shared copy. So pre-built stages can't serve as a shared far look either. The shared far look offered elsewhere in this plan (the open-questions table in section 3, section 3.6's far ring, the table above, step 0 and the note after the steps in section 6) falls under the same row, unless the maintainer changes it.

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
| 11 | **Far and back** (Python first, then C++) | Grow a tree in full to 30 and to 50. Turn it into its far form, grow it 1, 5 and 10 years by the lighter model, and bring it back. Compare it with the same tree grown in full all the way, on 20 seeds | Every limb in the skeleton still there, with radii within a set share. Crown figures inside the noise between seeds. Cuts and scars exactly where they were |
| 12 | **Cuts** | The same cut in Python and C++ on a recorded state, then the next years | As check 4 for that year. The tree plus the cut piece weigh what the tree did. The piece's rings and knots are the tree's |
| 13 | **What falls** | Shed pieces a year, by size, against the model's own death records (`tools/tree_table.py shed_events`) | Exact counts. Every piece's shape is handed over before anything deletes it |

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
- **The bark and the rest of the ageing stay data.** Live meshes carry each part's birth year and size in their UV channels, as the export does now. The material reads a part's age from them (`docs/unreal.md`), and `appearance` sets the bark stage, thickness and peeling from the species file. Addition 9 in that file's table gives the third bark layer.
- **New settings for cuts, wounds and the far form go in the species file too,** each with its label. Anything guessed is marked TUNED or VERIFY, like the rest.

## 6. Steps, effort and risks

Effort is my rough estimate in agent-days. It isn't measured, and none of it includes waiting for the maintainer or for the PC. Steps 5-7 are **model work in Python**, behind settings that are off by default, as every new behaviour is now. They're not the port, but they touch `treegen/`, so they need agreeing with Crown 2.

| # | Step | Effort | When | Needs |
|---|---|---|---|---|
| 0 | The maintainer's open questions: what 1:1 covers, memory once measured, speed shortcuts, a shared far look | | When the maintainer's ready | The maintainer |
| 1 | Measure in the game: memory in play; 100-500 plain meshes of 16,000, 64,000 and 200,000 triangles for frame time, shadows and Lumen; rebuilding one after a cut; handing a falling piece to physics | 3-5 | When the maintainer says the game may be run | PC, Unreal |
| 2 | Species route: the YAML-to-JSON tool now; the schema's 382 missing entries, the 234 fallbacks and climate once Crown 2 has merged | 3-5 | Now, then after Crown 2 | |
| 3 | Recording tool: states, arrays and draws from any year, Python only | 2-3 | Now | |
| 4 | Random numbers in C++, with vectors from numpy | 1-2 | Now | |
| 5 | **Cuts and hand-overs in Python:** a cut at any node or along one; a cut log; cut, shed and felled pieces handed out as records with shape, rings and knots; rings kept for wood from 0.5-1 cm in every run; a stem-section call | 5-8 | Now | Server for tests |
| 6 | **Wounds, hanging dead branches, stump sprouts in Python:** from publisher or PMC sources where they exist, otherwise TUNED and marked | 5-10, with reading | Reading now; the rules with step 5 | |
| 7 | **The far form and the lighter model in Python:** skeleton, rings, stores and cut log; growing it; regrowing twigs onto it; check 11 on the server | 15-25 | Prototype now; finish after the tree settles, because it has to follow the full model | Server |
| 8 | Port: stable core (node store, passes, light with an FFT, water, mechanics), checks 3 and 4 | 5-8 | **Wait:** until the maintainer says port | |
| 9 | Port: growth and roots | 12-20 | **Wait:** until the tree settles | |
| 10 | Port: plot (shared light, soil, thinning, spread, damage) | 6-10 | **Wait** | |
| 11 | Port: cuts, hand-overs, far form, lighter model | 8-12 | **Wait:** after 5-7 | |
| 12 | Port: live meshes: tubes, leaves, bark data by age, chunks rebuilt after a cut, cut faces with rings, far meshes | 15-25 | **Wait:** can follow 8 | |
| 13 | The proof: checks 5-13 on the server | 8-14 | **Wait** | Server |
| 14 | In the game: the forms and the rings they change at, the scheduler's step, saving far forms, pieces to the wood science and to physics, litter for the ground | 15-25 | **Wait:** it needs the game's R9 and R10b first | PC builds |

**In all, about 100-170 agent-days** (estimate). Steps 1-4 are groundwork. 5-7 are Python model work that can start now behind settings. 8-14 are the port and the game, and **nothing there starts until the maintainer says so.**

The earlier stage-library and summary steps are dropped: trees that can be cut can't come from a library. A library could still give a shared far look, if the maintainer wants one.

### Biggest risks

1. **The model moves under the port.** `growth.py` had 30 commits and 772 changed lines in two days, and Crown 2 is at work now. Porting early means porting twice. Hence the wait, and freezing logic only.
2. **The far form doesn't hold the tree.** The lighter model doesn't exist, and a tree brought back has new twigs on its old limbs. Check 11 finds out in Python before any C++. If it fails, far trees need whole states, about 50 times the disk.
3. **Video memory for live meshes.** No Nanite means every triangle is drawn and every tree's mesh is its own. The rings in section 3.6 are estimates until step 1 measures them in the game.
4. **Memory and disk.** The game's limit is 6 GB, the PC has 16 GB, and I don't know what the game uses in play. Far forms grow as the player explores: about 0.8-7 GB for the trees round the birth site alone.
5. **Bringing trees back at speed.** Walking is covered for birch, but all species is borderline and running isn't covered (section 3.4). Then trees stay in their middle form longer.
6. **Guessed parts of cutting.** Wounds closing, dead branches hanging, stump sprouts: no source read yet. Each stays marked until one is.
7. **A copy drifts from the model.** It has happened once already. Hence checks on the settings in use, and one model afterwards.
8. **Compiler and FFT.** The sweep needs vectorising, and MSVC is untested. The game's FFT (`water/Surface.cpp`) is radix-2 only, while the light grids are 94, 126, 189 and 316 across. So it needs a mixed-radix FFT, such as pocketfft (BSD, the one numpy uses), or grid sizes that change results.
9. **Other species.** Pine and spruce need model changes first (section 5).
10. **ARM here, x86 there, and the game's roadmap.** Everything measured here needs measuring again on the PC. Live trees need the game's World and scheduler. `USimSubsystem` calls itself a skeleton (R9a), and there's no scheduler, `TreeState` or `StepYear` in its source yet.

## Measured, and estimated

**Measured here, on the server:**
- Every stage table, the mesh tables at four detail levels, and the memory tables except rows marked as sums.
- Far form sizes and load times; how fast fine wood turns over; what's shed each year, by size.
- Disk sizes, the six C++ pieces with their bits, how fast a tiny change spreads, single precision against double (8 seeds a side).
- Lines reached and species file counts.

**Measured earlier by others, read not rerun:** `light_rows` and `drop_dead` on plots, `node_v1_*` stand trees against plots (`reports/overnight_log.md` at 7c512a6), light every 2 years, grid sizes, the noise floor, and the 0.07 s dynamic-mesh copy (`docs/unreal.md`). The game's numbers are from its own files and its 2026-10-31 log; nothing was run there.

**Read in the model's code, not run:** what a cut, a wound, a felled stem and a falling branch can use today (section 3.5).

**Sums over measured arrays, not runs:** live-only memory, live single-precision memory, and every far form size. No far form exists yet.

**Estimates:**
- All whole-model C++ gains, the factor for the game's PC, and full trees per GB after C++.
- Catch-up counts, tree densities and counts by ring, and video memory per mesh and per ring.
- Rates of bringing trees back, the small state a far tree needs (about 10 KB), and how much falls across the forest.
- Lines of C++, all effort, and shoots and roots gaining 3-10x.

**Couldn't measure:**
- Anything on the game's PC or under MSVC, because the PC is for games.
- Anything in Unreal: plain meshes by the hundred, cut rebuilds, physics, frame times.
- The far form itself and its round trip, and the lighter model, because none exist yet.
- Single precision on plots, or with 20 seeds.
- `_grow_shoots` or the roots in C++: too large to port cheaply for a measure.
- Crown 2's settings, which aren't in 5f07fae.
