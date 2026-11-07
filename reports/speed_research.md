# Speed research

**State of this draft:** server access was blocked by an access check partway through. Numbers from jobs on the server that I couldn't fetch are marked pending. Nothing here is switched on.

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
