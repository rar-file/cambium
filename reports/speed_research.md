# Speed research

**State of this draft:** server access was blocked by an access check partway through. Numbers from jobs on the server that I couldn't fetch are marked pending. Nothing here is switched on.

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
