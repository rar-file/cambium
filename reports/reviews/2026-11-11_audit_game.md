Model: Fable 5.2 (claude-fable-5-2)

# Audit: can a game really use these trees? 2026-11-11

Independent, read-only review of the game side: the export, the Unreal scripts, the replay work and the plan for live trees. Master at `b84ab90`; branches `showcase-unreal` (`585bc0c`) and `replay` (`fd104f6`) read with `git show`.

- I read the code and docs named below, and the manifests and result files the showcase and replay runs left in their work folders (git-ignored).
- Nothing was run: no growth, no tests, no renders, no Unreal. The game's own project was not opened.
- What Unreal can and can't do is quoted from the project's own readings in `docs/unreal.md`, not checked by me.
- CONFIRMED: I saw it in code, a saved file or a live web check. SUSPECTED: I did not.

## Verdict

1. One tree at a time, as a film asset, the export is strong. Files come back from Unreal triangle for triangle, and the pictures are real model output.
2. As a game asset it isn't ready. Nobody has measured a frame time, a packaged build, a collision, or many trees on screen in real time.
3. The owner's rule (every tree its own, near and far, cuttable) can't be met with what is built. On the project's own numbers each way that exists today costs 140 GB or more.
4. A narrower form can be met: own data everywhere, own shape built at run time from a small stored skeleton. The parts for it don't exist yet, and the decision that unlocks it is still open.
5. A game developer outside the project can't follow the Unreal route today. The docs point at private scripts, and the import script sits on an unmerged branch.

**Score: 4 out of 10.** The single-tree export alone would earn 7. "Ready for games" would earn 2.

## What the files weigh

| Age | Stand-grown, nearest level | File, MB | Open-grown, nearest level | File, MB |
|---|---|---|---|---|
| 15 | 365,674 | 33 | 205,272 (age 16) | 18 |
| 30 | 1,392,278 | 119 | 3,498,126 | 299 |
| 40 | not listed | | 5,406,245 | 452 |
| 50 | 2,023,679 | 167 | not exported | |
| 60 | 2,208,447 | 178 | 10,330,374 | 856 |

- Triangles, seed 5. Stand: `docs/unreal.md:26-33`. Open: the showcase exports' manifests at `b662c2c`. On later defaults (`5734ac2`) the open tree at 60 is 8,568,277 triangles and 704 MB.
- The next level, `lod1`, is 16,000 triangles at every age, and `lod2` is 12.
- The open tree's 10.3 million: leaves 7,023,960 (234,132 leaves at 30 triangles each), wood 3,272,538, roots with the tree 23,252, bark strips 10,624. A further 1,379,180 lie below ground in `_roots`.

| Level | Keeps | Drops |
|---|---|---|
| `lod0` | Every twig as a tube, every leaf as a 30-triangle blade, bark relief in the stem's mesh, peel strips | Nothing. It has no budget |
| `lod1` | Only the wood thick enough to fit about 6,400 triangles, and 3,000-4,000 leaf cards | All fine twigs, single leaves (a card stands for about 12 leaves on the stand tree and 74 on the open one), bark relief, peel strips, leaf node ids |
| `lod2` | 3 crossed cards baked from `lod0` | Everything else |

**In the engine, measured by the project at age 60** (no age-50 tree was imported at its nearest level):
- Stand tree, 2,363,740 triangles: one run, 108 s to import. A tree of this size needs about 7 GB of memory with distance fields off (`docs/unreal.md:93`).
- Open tree, 10,330,374 triangles: cut into 9 pieces of at most 1.8 million, 5 editor runs, 464 s of import in all. The pieces add up to the source exactly.
- Size in the editor: 166-186 MB a stand tree and 451 MB the open tree, with a full fallback; 42 MB a stage with the game's small one (`docs/unreal.md:245`).
- Path tracing ran at about 7 s a frame at 1920 x 1080 (`replay:tools/replay_unreal.py:101-103`). No real-time frame was ever timed.

## The owner's rule against the numbers

| Way of giving each birch its own tree | Per tree at 50 | Per tree at 60 | 4,222 birches, at 60 |
|---|---|---|---|
| Live in Python | 22 MB | 34-43 MB | 140-180 GB of memory |
| Live after a C++ port (the plan's estimate) | 4-12 MB | 6-17 MB | 27-73 GB |
| Its own Nanite mesh, built in the editor | not measured | 42 MB | 177 GB on disk, one age each |
| Its own textures, as exported | 36 MB | 36 MB | 152 GB of source art, one age each |
| A replay tree (all ages in one) | | 610 MB | 2.6 TB |
| A 16,000-triangle plain mesh | 16,000 | 16,000 | 68 million triangles, about 17,000 draw calls; never measured |
| A stored skeleton, 1 cm and up, with rings | 0.07 MB | 0.09 MB | 0.4 GB: this fits |

Sources: `reports/cpp_port_plan.md:146-183, 295-312, 434`; `reports/speed_research.md:230`. Birches are 4,222 of 31,573 trees in reach, so the whole forest is roughly 7 times these sums if the other trees are as large. A shipped game can't build Nanite (`docs/unreal.md:237`), so a tree that can be cut can't be a Nanite mesh at all.

## Who does what

| Part | The model's | Added in export or engine | Missing |
|---|---|---|---|
| Wind | One weight per vertex (path length from the ground), one phase per tree | All the motion: a shader with a fixed direction. Stems don't bend | Sway from the model's own stiffness; cost with Nanite and shadows |
| Seasons | Leaf colour by day, each leaf's own delay (timing TUNED by eye) | Colour worked out in the material from UVs; one number turns a forest (tested) | Leaf fall, spring leaf growth |
| Bark | Stage by a part's age, thickness and height; black-base height from Swedish trial data, by the project's docs | Baked textures per stage; relief in the mesh | A material that ages bark live (the replay has one) |
| Roots | The whole root system, anchorage, a root-plate record on uprooting | The visible foot: swell, sinking roots, moss, all TUNED by eye | A fallen tree with its plate; any ground but a flat plane |
| Felling, cutting | Limb death from a node, a broken top, ring widths, shed records | Nothing | A cut anywhere, stump, cut face, pieces, branches on the ground, collision, physics |

## Findings, most serious first

### G1. Critical, CONFIRMED. The rule in decision 91 can't be met as built, and the choice that would make it feasible is open
- Where: `DECISIONS.md` row 91; `docs/unreal.md:237, 245, 251`; `reports/cpp_port_plan.md:13-15, 264, 457`.
- What: each way to "its own tree, near or far" that exists today costs 140 GB or more (table above), and the C++ estimate is still 27-73 GB. The plan's way out is a far form and a lighter growth model, and neither exists. Its open question 4 (may far trees share a look while keeping their own data) has no answer, and line 457 rules it out.
- Why: the port, the meshes and the saves all hang on this. Work done before it is settled may be thrown away.
- Fix: put one choice to the owner with the table: own data and growth everywhere; own shape wherever the eye can tell; far trees drawn coarse from their own skeleton. Effort: S to decide, L to build.

### G2. Critical, CONFIRMED. Nothing has been measured in real time
- Where: `docs/unreal.md:460-472`; `reports/cpp_port_plan.md:540, 594`.
- What: no frame time, no packaged build, no voxel foliage build, no run in the game. The showcase did draw 1,254 instanced trees and a wind loop, but through the offline render queue, with no frame timed. The plan's step 1 (100-500 plain meshes at three sizes) was never run.
- Why: "made for games" rests on stills. Milliseconds per frame for N trees is the first number a studio asks for.
- Fix: step 1 in an empty project, then packaged: 1, 50 and 500 trees, Nanite and plain, with wind and shadows; log frame time, memory and video memory. It needs the owner's PC for an afternoon, or another machine. Effort M.

### G3. High, CONFIRMED. There is no middle level of detail
- Where: `species/betula_pendula.yaml:2226-2229`; `treegen/game.py:468-524, 610-626`; `docs/unreal.md:231, 431-432`.
- What: 2.2 million triangles (10.3 million for the open tree), then 16,000, then 12. `lod1` has no twigs, its cards face random ways, and in Unreal they come out darker ("Not fixed"). Nanite's own fallback is "a rough blob". Stage swaps jump, and the cross-fade is untested.
- Why: without Nanite there is nothing between a film mesh and a pole with cards. With Nanite, the far view rests on a voxel build nobody ran.
- Fix: add 200,000 and 64,000 levels (the plan already built them: 2.0 s and 0.65 s), cards cut along the tree's own twigs, `lod1` shading mended, a far form checked at distance, screen sizes given. Effort M.

### G4. High, CONFIRMED. The tree in every hero picture is too heavy for a game and is the least-checked form
- Where: the open-grown export's manifest; `showcase-unreal:tools/unreal/showcase_jobs.py:26, 150`; `DECISIONS.md` row 86; `reports/birch_v1_final.md:72-79`.
- What: 10.3 million triangles, 856 MB, 9 pieces. `lod0` has no budget, by row 86. Lone trees at 50 / 60 are 17.8 / 19.2 m tall with 44.5 / 49.4 cm stems and 8.65 / 9.35 m crowns, and the report says "This isn't a test": the width is capped by formula. The crown design track had no open-grown run to read.
- Why: the project's public face is a tree no game could place twice, grown in the mode with no independent check.
- Fix: a leaf level by distance (8-12 triangles, then 2), an optional `lod0` budget, triangle counts in the public docs, open-grown trees in the validation track. Effort M.

### G5. High, CONFIRMED. A grown forest can't reach the game
- Where: `cambium/_forest.py:5`; `tools/game_export.py:49-62`; `showcase-unreal:tools/unreal/showcase_woodland.py:204` and its `docs/media/README.md`.
- What: forest trees "can't be exported as a mesh". The game export grows one tree alone or among copies of itself. The showcase wood is a few exports repeated as instances; its notes call it "our layout for the picture, not a model run".
- Why: the forest is what the science validates and what the owner asked for. None of it can be seen in an engine. Repeated trees also break rule 91.
- Fix: a forest export: at chosen years, every living tree's place, seed and age, with a middle-level game mesh. Effort M to L.

### G6. High, CONFIRMED. No collision, cutting, felling or fallen branches anywhere
- Where: no match for "collision" in `treegen/`, `cambium/`, `tools/unreal/` or the docs; `showcase-unreal:tools/unreal/showcase_scene.py:112, 195, 211` switch it off on every tree; `reports/cpp_port_plan.md:376-390`.
- What: the model can kill a limb from a node, break a top, and record an uprooting with its fall direction and plate (`treegen/damage.py:254`). It has no cut at a chosen point, stump, cut face, handed-over piece or branch on the ground.
- Why: these are the features the owner named, and the public roadmap lists them.
- Fix, in order: trunk and main-limb capsules from the skeleton, written into the manifest (S); a cut call in Python that returns the piece with its rings, and a record for each shed piece (M); wound and stump-sprout rules only from opened sources (M to L).

### G7. High, CONFIRMED. The public Unreal route doesn't work for an outsider
- Where: public `docs/unreal.md:80-110`; public `tools/unreal/` (no `cambium_import.py`); public `README.md:51, 116`; public `docs/site/install.md:6`; `https://pypi.org/pypi/pycambium/json` and the docs site address in `mkdocs.yml` (both 404 today); no release on the public repository.
- What: section 3 has the reader run the game's own editor scripts, which aren't public. The script behind every README picture, and the notes saying what in them is dressing, are only on `showcase-unreal`. "Inside a birch wood grown by Cambium" doesn't say the wood was laid out by hand. `pip install pycambium` fails, and there is no release. None of decision 104's four ways in is live.
- Why: it's the first wall a game developer hits.
- Fix: merge and publish `cambium_import.py` and the media notes; a short public quick start; mend the caption; publish to PyPI or change the install page. Effort S to M.

### G8. High, CONFIRMED. The replay proves the idea, but it is a film tool
- Where: `replay:tools/replay.py:60, 241-276`; `replay:tools/replay_unreal.py:70, 101-105`; `replay:tools/unreal/replay_material.py:188`; the run's manifest, check and result files.
- What: the check is real: 0 wrong nodes in 5.84 million node-years, radius within 2 %, position within 0.74 mm. But one tree is 6.19 million plain triangles, 80 MB of data textures and 610 MB on disk. In Unreal one test frame was path traced; no shot finished, and the branch's notes say the level with the tree "ran this PC out of memory in 23 s". A replay can't show a cut. The branch is unmerged and names a file under a home folder.
- Why: "grow once, replay in a shader" is the main idea for live trees. As built it holds one tree, not 4,222.
- Fix: keep it for films. For the game, store only the thick skeleton (on a stand tree, 5,321 living nodes at 60 out of 230,475 ever grown) and rebuild a plain mesh when the game year turns. At 6x time that's once in 61 real days. Effort L.

### G9. Medium, CONFIRMED. Every stage carries its own textures, and every season its own mesh
- Where: `treegen/game_unreal.py:1195-1267`; the exports' texture folders.
- What: 21 PNGs a stage. The leaf, card and strip atlases are byte for byte the same across trees and ages (one hash on three exports), yet each stage writes its own. Autumn is a second full mesh, though `docs/unreal.md` section 6 turns one mesh by material.
- Why: texture memory and material count grow with trees times stages, and nothing batches.
- Fix: species atlases written once; bark from shared stage tiles blended in the material by the age and size already in UV2 and UV3; no per-season meshes for Unreal. Effort M.

### G10. Medium, CONFIRMED from the plan's table. Export time is mostly textures
- Where: `reports/cpp_port_plan.md:146-157`.
- What: a 10-year tree of 46,311 triangles takes 48.6 s, 96 % of it far sheets, bark baking and PNG writing. At 50 and 60 it's 72.1 and 74.0 s, 78 % and 77 % the same three. One 60-year stand tree end to end is about 67 s to grow and 74 s to export (server), and 108 s to import (the PC).
- Why: it's a share of "generation is slow" that is cheap to remove.
- Fix: after G9, write textures once; cache bark tiles; skip `lod2` unless asked. Effort S.

### G11. Medium, SUSPECTED as the cause; each fact CONFIRMED. Pendulous has no owner and no measurement
- Where: `treegen/game_unreal.py:831-850`; `docs/unreal.md:356-363`; `reports/extracts/crown_and_light_papers_2026-11-07.md:12`; `species/betula_pendula.yaml:599-603, 1838-1839`; `KNOWN_ISSUES.md:2181, 2186`; `DECISIONS.md` row 92.
- What: the export points every leaf tip-down ("Hanging 100 %" at every age), where the project's extract says "Most leaves hang downward". Twigs under 1.2 cm radius hang by a value TUNED "against the look". Lone trees' longest strands are 5.2 / 6.1 m against "about 2-4 m in photos, judged by eye", as single strands where photos show sprays. Row 92 set the owner's earlier less pendulous aside for real life, yet all of these values were set by eye.
- Why: the owner has now said it twice, and none of the four tracks covers it.
- Fix: measure hang on the reference photos and on the model (strand length, share of the outline that is curtain); take leaf direction from the shoot with the measured spread; retest option J. I couldn't open the paper (the publisher returned 403): UNVERIFIED. Effort M.

### G12. Medium, CONFIRMED by reading, not run. The import script's defaults are film settings
- Where: `showcase-unreal:tools/unreal/cambium_import.py:46-61, 187-190, 210, 290`.
- What: `--fallback 1.0` keeps every triangle twice (about 166-186 MB a tree, against 42 MB with a small one). A `.glb` gets none of the script's materials. No collision, no LOD screen sizes, a fixed wind direction.
- Fix: a small fallback by default, materials for `.glb`, a trunk capsule, screen sizes. Effort S.

### G13. Low, CONFIRMED. Two front doors grow different trees by default
- Where: `cambium/cli.py:46-48`; `tools/game_export.py:20, 585-586`; `docs/site/install.md:53`.
- What: `cambium` grows in the open unless `--forest`. `tools/game_export.py` grows in a stand unless `--open`, and its docstring says the reverse. The only triangle table is for the stand tree. The site says a 60-year open birch has "well over a million leaves"; the exports have 234,132 and 188,511.
- Fix: one stated default, counts for both in the public page, the leaf figure mended. Effort S.

### G14. Low, SUSPECTED. The trunk's place may be mirrored in y
- Where: `treegen/game_unreal.py:1087, 1095`. Carried from the 2026-11-09 review. The check needs the game's own trunk file, which I may not open.
- Fix: read back one leaning stem in the test project. Effort S.

## A design that could meet the rule

Untested, and every cost below needs G2's measurements first.
1. **Grow once, offline.** Each forest cell is grown on the server with its real neighbours. Each tree keeps a small history: its skeleton from 1 cm up, ring widths, what its twigs carried each year, and its sheds and breaks. The date picks the state, so time away from the game costs nothing for untouched trees.
2. **Draw by distance from that history.** Far: skeleton and crown cards, merged per cell. Middle: 16,000. Near: 64,000 to 200,000. The tree in hand: full detail with cut faces. All plain meshes, rebuilt off the game thread when the game year turns or a cut lands.
3. **Twigs regrown from the tree's own seed,** so they come back the same each visit.
4. **A cut forks the tree.** From then on it grows live on the lighter model. A fixed pool of live trees is shared; the rest stay on their stored history.
5. **Nanite only for a library,** and only if the owner allows shared shapes somewhere.

## What a game developer hits first

1. `pip install pycambium` fails; the clone works.
2. `cambium grow --years 60 --export glb` takes minutes and gives the open-grown tree, the heavy form, with no wind data and no roots in the `.glb`.
3. A full-detail old tree takes about 7 GB of free memory to import, or has to be cut into pieces, and no public script imports or cuts it.
4. The imported tree has Unreal's default materials, no collision and no working chain of levels.
5. Wanting a forest, they find forest trees can't be exported at all.

## Before "ready for games" is a fair claim, in order

1. A timed real-time scene in a packaged build, on stated hardware (G2).
2. A full chain of levels with a tested far form, and a budget on the nearest (G3, G4).
3. A public one-command import with game defaults, and a tree pack to download (G7, G12).
4. Shared textures and materials per species (G9).
5. Collision shapes in the export (G6).
6. A forest export with places (G5).
7. Cut, fell and shed records in Python, then the far form and the port (G1, G6, G8).

## The four design tracks

I don't disagree with any of them. None touches the game side or the hang. Two of them (crown extent, earned size differences) will change leaf counts, so every triangle and memory figure here needs reading again after they land. If limbs come to stop at their own neighbours, forest trees will differ more, which makes G5 matter more.

## What's genuinely good

- **The export is tested against the engine for real.** Triangle counts come back exact, four UV sets survive, node ids are split to survive Nanite's 14-bit UVs, and every file is read back by two readers.
- **`docs/unreal.md` is honest.** Each claim is marked tested, read in source or documented. It lists what wasn't tested, and says the game's own birch looks better and why.
- **Leaf area in the mesh equals the model's** within 0.3 % at every age, 50 and 60 included.
- **Seasons from one mesh:** the live material matches the baked colour at day 200.
- **The model's own roots reach the file,** with the buried part kept apart and seamless.
- **The port plan is sober engineering.** It measures first, keeps measured apart from estimated, names memory as the limit, and says "don't port yet". I agree.
- **The replay check is the right kind of check:** the shader's arithmetic mirrored in numpy and compared with the model's own state every year.
- **The owner's PC is guarded:** runs refuse to start under 6 GB free and stop Unreal under 1.5 GB.
- **The public copy holds no user name and no game name** (searched today).

## Not checked

- Nothing was run, so every time, size and memory figure is the project's own, read from its files.
- Cooked game sizes, video memory and draw calls are unmeasured by anyone; my sums for them are arithmetic.
- I read `cambium_import.py`, `showcase.py` and `showcase_split.py` in full, and the other showcase and replay scripts by search.
