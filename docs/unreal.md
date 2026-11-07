# The tree in Unreal 5.8

How to get a grown birch from this project into the game, what Unreal keeps of it, and what the game's scripts would need. Written for someone who runs Python scripts and doesn't write C++ or Blueprints. Nothing here changes the game; the game's folder is only read.

**Tested** means run for real in Unreal 5.8.4 on this PC, in an empty test project. **Read in source** means read in the engine's code. **Documented** means Epic's pages say so.

## 1. Making the files

    python tools/game_export.py export --target unreal --seed 5 --ages 15,60 --seasons summer --out out/game/unreal

Ages and seasons are your choice. Without `--target unreal` you get the plain `.glb` export for any engine, and its geometry and textures come out byte for byte as they were.

You get the game's own folder shape, so it can be copied over:

| Where | What |
|---|---|
| `SourceArt/PolyHaven_split/betula_pendula_grown/<variant>.gltf` and `.bin` | One tree at one age, one level |
| `SourceArt/PolyHaven/betula_pendula_grown/textures/<slot>_diff_2k.png`, `_nor_gl_2k.png`, `_rough_2k.png` | Its maps, 8-bit, named as `build_materials.py` looks for them |
| `fragments/trunks.json`, `flora_variants.json`, `flora_rule.json` | Lines for the game's own files. Nothing is written into the game |
| `game_manifest.json` | Sizes, triangle counts, ground line and bark heights for every stage |

Variant names: `betula_pendula_grown_age060` is the nearest level in the base season, summer. `_autumn` and so on for other seasons, `_lod1` and `_lod2` for the other levels, `_roots` for what's under the ground. The folder name is new on purpose, so the game's birch stays as it is.

## 2. What each level is

| Age | Height, m | Leaves | Nearest level | of which wood | roots with the tree | bark strips | leaves | `_lod1` | `_lod2` | `_roots` | Nearest, MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 5.7 | 8,711 | 297,930 | 36,372 | 228 | 0 | 261,330 | 15,999 | 12 | 4,772 | 27 |
| 15 | 12.0 | 10,436 | 365,674 | 50,876 | 1,270 | 448 | 313,080 | 16,000 | 12 | 16,394 | 33 |
| 30 | 18.8 | 34,856 | 1,392,278 | 341,067 | 2,843 | 2,688 | 1,045,680 | 16,000 | 12 | 62,366 | 119 |
| 50 | 24.6 | 46,312 | 2,023,679 | 623,095 | 5,848 | 5,376 | 1,389,360 | 16,000 | 12 | 155,765 | 167 |
| 60 | 26.1 | 47,728 | 2,208,447 | 763,241 | 7,094 | 6,272 | 1,431,840 | 15,999 | 12 | 192,647 | 178 |
| 100 | 29.7 | 49,408 | 2,787,678 | 1,283,751 | 11,383 | 10,304 | 1,482,240 | 16,000 | 12 | 396,116 | 210 |

The game's own birch, `betula_pendula_a`, is 1,771,416 triangles, read back in Unreal. Budgets are settings: `--budget lod1=8000`, or `appearance.game` in the species file.

With Nanite and voxels, the nearest level is the one that matters. `_lod1` and `_lod2` are there for anything that can't use Nanite. In Unreal, `_lod1`'s leaf cards came out darker than the nearest level's leaves (section 9).

### How the mesh was cleaned

Same tree, same camera, before and after:

| | Age 50 before | after | Age 60 before | after |
|---|---|---|---|---|
| Wood | 287,700 | 241,584 | 311,604 | 265,630 |
| Roots with the tree | 7,274 | 6,571 | 8,687 | 7,874 |
| Leaves | 2,037,728 | 1,296,736 | 2,100,032 | 1,336,384 |
| **With the tree** | **2,338,078** | **1,550,267** | **2,426,595** | **1,616,160** |
| Below ground | 200,282 | 143,969 | 265,417 | 190,572 |
| File, MB | 178 | 120 | 184 | 124 |

(The plain `.glb` export's nearest level was 380,151 and 407,568, with two-triangle alpha-cut leaves and no roots. That's a different thing: voxels and Nanite don't want alpha.)

What changed, all behind settings in `appearance.game.unreal`, so `ring_tolerance: 0` and `ring_tolerance_m: 0` bring every ring back:

- **Hidden rings gone.** A branch starts on its parent's centre line, so its first rings lay inside the parent. Dropping them took off 1 to 1.6 % of the wood's surface, all of it unseen.
- **Rings that add nothing gone.** A ring goes if the tube between its neighbours stays within 10 % of the radius or 1 mm of it, whichever is more. The stem, buttresses and junction fillets keep all theirs. No run is longer than 0.5 m, so wind can still bend it.
- **Leaves: 30 triangles.** See "Leaves" in section 8. Going from 44 to 28 hadn't hurt the outline: it missed by 0.75 mm on eight rows and 0.79 mm on twelve. The straight edges came from the outline's own shape.
- **Nothing lost that can be seen.** Leaf area, height and width don't change. Wood surface stays within 0.02 % once hidden rings are gone. Whole tree at 1,100 pixels tall, same camera, ages 50 and 60: it covers the same share of the view to 0.03 of a percentage point, and about 3 % of its outline pixels differ, mostly twigs thinner than a pixel. Side by side I can't see a difference.
- **Clean.** At ages 15 and 60: no degenerate faces, no repeated faces, no unused vertices. Stem, roots and leaves have no bad slivers; twigs have some, being thin.

Leaves should suit voxels: the outline and main teeth are in the mesh, so losing the alpha loses only the small teeth. Voxels aren't tested.

Since then the bark has real depth and the leaves real outlines (section 8), which is where these went, with no triangle budget for now:

| | Age 50 cleaned | now | Age 60 cleaned | now |
|---|---|---|---|---|
| Wood | 241,584 | 623,095 | 265,630 | 763,241 |
| Roots with the tree | 6,571 | 5,848 | 7,874 | 7,094 |
| Bark strips | 5,376 | 5,376 | 6,272 | 6,272 |
| Leaves | 1,296,736 | 1,389,360 | 1,336,384 | 1,431,840 |
| **With the tree** | **1,550,267** | **2,023,679** | **1,616,160** | **2,208,447** |
| File, MB | 120 | 167 | 124 | 178 |

## 3. Importing with the game's own scripts

The game's scripts took these files in the test project without being changed. To add them to the game:

1. Copy `SourceArt/` from the export over the game's `SourceArt/`.
2. Import, as `Tools/Assets/import_all.py` does for its trees:

       set GAME_FILES=<full path to a .gltf>;<another>
       UnrealEditor-Cmd.exe <Game>.uproject -run=pythonscript -script="<project>/Tools/Editor/import_world_assets.py" -FullStdOutLogOutput

3. Materials:

       set GAME_MATERIALS=instances
       set GAME_ASSETS=betula_pendula_grown
       UnrealEditor-Cmd.exe <Game>.uproject -run=pythonscript -script="<project>/Tools/Editor/build_materials.py" -FullStdOutLogOutput

4. Add the lines from `fragments/` to `SourceArt/PolyHaven_split/trunks.json` and `Content/Data/Science/flora.json`, then run the import again with `GAME_FINISH=1` to rewrite `WorldAssets.json`.

Age 60's nearest level needs about 7 GB of memory, with distance fields off in the test project. With them on, as in the game, it needs more: free memory fell from 8.6 GB to 1.2 GB on a 1.85 million triangle try, when the runner stopped it. Import one heavy variant per run, as `import_all.py` does, with at least 8.6 GB free.

### What the game's scripts would need added

None of this has been changed in the game. Numbers 1-4 let the tree in. The rest make it better.

| # | File | What to add | Why |
|---|---|---|---|
| 1 | `Tools/Assets/import_all.py` | Look for `.gltf` as well as `.fbx` (lines 54, 67-68, 104-105) | It only lists `.fbx`. Running `import_world_assets.py` by hand with `GAME_FILES` works today |
| 2 | `Tools/Assets/measure_trunks.py` | Nothing: use `fragments/trunks.json` | It needs Blender and FBX. The export measures the trunk the same way |
| 3 | `build_materials.py`, `WIND` and `NANITE_SHAPE` | `"betula_pendula_grown": (1100.0, 0.16, 0.30)`, and the name in the voxelized list | Without `WIND` it doesn't sway. Same numbers as the game's birch |
| 4 | `Content/Data/Science/flora.json` | A rule with these variants and `sink_m: 0.10` | The game seats a tree by its lowest point, which here is 10 cm below the ground line. Its `min_z_cm` is about 32, not about 0, on purpose: section 5 |
| 5 | `Source/<Game>/World/WorldGenerator.cpp` line 1176 | Don't add `root_flare_tile` to a rule that has its own roots | Otherwise a made-up flare sits over the real one |
| 6 | `set_tree_looks.py`, `BRANCH` | `"betula_pendula_grown": (1.6, 3.0)` | Same branch sway and flutter as the game's birch |
| 7 | `build_materials.py`, M_Foliage | A `ThroughGain` parameter on line 562, default 0.25 | Fixed at 0.25 of the leaf's colour. Our measured leaves pass about as much light as they reflect, so 1.0 would be right for them. Not why leaves come out black in the test pictures: section 9 |
| 8 | `build_materials.py`, M_Foliage | Section 6's one line, and `MPC_Season` | Season change while the game runs |
| 9 | M_Surface | A third bark layer from UV3 (white, rough) | Full white-to-black from our ageing rules. See section 8 |
| 10 | `build_materials.py`, `rounded_normal` | A separate switch from `PlantKitWind` | Turning on the `COLOR_0` wind (Kit 1) also turns on "round mound" shading, made for ground plants. Until then leave Kit at 0, as the game's birch does |

## 4. What Unreal keeps

| What the plain export carried | Kept or lost | Where it goes now |
|---|---|---|
| Positions, normals, triangles | Kept, **tested**: 365,674 triangles come back exactly at age 15, and the same at each age I could import, by the Nanite count on the saved asset | Same. Metres become cm, y-up becomes z-up |
| Tangents | Kept on normal meshes. Nanite doesn't store them (**documented**) | Nothing to do |
| Base colour, normal map | Kept, **tested** | The game's script makes its own material and sets them |
| Roughness and occlusion map | The game reads roughness from a separate map's red | `_rough_2k.png`: red roughness, green height, blue occlusion |
| Height map | Lost as a texture | Green of `_rough_2k.png` |
| Vertex colour for branch and leaf colour | Lost as colour: the game's wind reads that channel | Branch colour in the atlas. Leaf colour by the atlas column UV0 points at |
| 16-bit `COLOR_0` | Lost, stored as 8-bit, **tested**: the smallest step that comes back is 1/255 | `COLOR_0` is 8-bit now, and holds the game's wind data. Values come back exact, so nothing is converted to sRGB on the way (**tested**) |
| `_NODE_ID`, `_RADIUS`, `_LEAF_SUN`, `_LEAF_TURN` | Lost: only position, normal, tangent, UVs, colour, joints and weights are kept. **Read in source**, **tested** by what comes back | UV channels, below |
| `TEXCOORD_0` to `_3` | All four kept, **tested** | Nanite keeps at most 4, with 14-bit precision (**read in source**). Node ids are split so they survive that |
| `KHR_materials_diffuse_transmission` | Lost, **tested**: "Extension is not supported" in the log, and the import carries on | M_Foliage has its own light through leaves. The measured value is in the material's `extras` for a future `ThroughGain` |
| `alphaCutoff`, `doubleSided`, wrap modes, normal direction | Kept, **tested** | The game's masters use the same clip, 0.35 |
| Material names | Kept as slot names, **tested** | That's how `build_materials.py` finds each slot's maps |
| Nested `extras` | Log `LogJson: Error`, **tested** | Now written as plain text; the error is gone |
| Images that aren't a power of two wide | Refused: "Cannot import texture with non-power of two dimensions", **tested** | All are now |

One error stays in the log with any masked glTF material: "Invalid input AlphaMode for material expression node MF_Default_Body". It's in Epic's own function. The game replaces those materials anyway.

### What's in each channel

| | UV0 | UV1 | UV2 | UV3 | `COLOR_0` |
|---|---|---|---|---|---|
| Bark | Colour, normal, roughness maps | Bark wrap: whole 0.4 m tiles round the part, tiles along it | x birth year of the part; y wood radius, cm | x how white (0-1); y how rough (0-1) | R flex by path length, G one phase for the tree, B 0, A 255 |
| Leaf | Leaf atlas: column by chlorophyll level, row by outline variant; a corner of each cell holds the stalk's colour | x + 1024 y = node id | x days later or earlier to colour; y light, 0 shade to 1 sun | x chlorophyll on the export's day; y leaf area, cm² | R flex, G phase, B 1, A leaf id 0-254 |
| Bark strip | Strip atlas: column by opacity | x + 1024 y = node id | x birth year; y wood radius, cm | x opacity | R flex, G phase, B 0, A 255 |
| Leaf card | Card atlas: column by chlorophyll | Unused | x mean delay; y mean light | x mean chlorophyll; y leaf area it stands for, cm² | R flex, G phase, B 1, A card id |
| Root | Root atlas: column by circumference | Bark wrap | x birth year; y wood radius, cm | x 0; y how rough | R 0, so a wind that reads it leaves roots still |

A part's age in a material is `stage age - UV2.x`. Vertex colour alpha is overwritten when Nanite voxelizes a mesh (**documented**), so don't rely on the leaf id in voxelized clusters.

## 5. Roots and the foot

The roots are the model's own (`treegen/roots.py`). No generic flare is added.

- **With the tree:** the stem's foot and the thick roots, down to 10 cm below the ground line. That reach is what the game's own flare uses, so uneven ground meets them without a gap. "Thick" is over 14 % of the collar's radius, and at least 6 mm.
- **In `_roots`:** everything else. It shares its cut vertices with the tree, so no seam. It isn't for drawing above the ground, because the thin roots would show as hairs. It's for a dug-up view, a cross-section, or a game system that needs them.

| Age | Root length, m | Thickest, cm | Deepest, m | Spread, m | Ground line, cm below model's zero | Roots showing | Out to, m | Triangles with the tree | Triangles below |
|---|---|---|---|---|---|---|---|---|---|
| 5 | 26 | 2.4 | 0.81 | 2.2 | 6 | 1 | 0.07 | 228 | 4,772 |
| 15 | 96 | 5.3 | 0.96 | 4.1 | 9 | 2 | 0.14 | 1,270 | 16,394 |
| 30 | 369 | 9.6 | 1.17 | 7.7 | 14 | 4 | 0.27 | 2,843 | 62,366 |
| 50 | 939 | 12.9 | 1.20 | 10.6 | 19 | 4 | 0.45 | 5,848 | 155,765 |
| 60 | 1,250 | 14.1 | 1.22 | 11.7 | 20 | 5 | 0.39 | 7,094 | 192,647 |
| 100 | 2,613 | 18.4 | 1.24 | 18.0 | 25 | 6 | 0.52 | 11,383 | 396,116 |

**Why a ground line.** The model keeps its roots under its own z = 0. So the ground meets the tree a little lower, 1.25 collar radii and at most 25 cm (`appearance.game.unreal.roots`). This moves where the ground meets the tree, not the tree, and no growth number changes.

**What the export does to the foot.** All of it is in the export only, behind those settings. A root's path as seen from above, its radius, its branches and its mass stay the model's. Only heights move, and the stem's own surface.

- **Straight down.** The stem goes straight down to below the ground line. In the model it runs on as the taproot, whose first half metre leans well out to one side, and with the stem's thickness on that it made a hoof.
- **Butt swell.** The stem swells into the ground by the species' own `geometry.root_flare_extra`, 35 % at the ground, steepest there as on a real butt.
- **A swell for each thick root.** The stem's surface runs out towards each root that leaves its foot: a ridge comes down the stem, flatter as it goes, and lands on the root's top (`flow_*`). So root and stem are one shape, and the root comes out from under the swell, not through a hard line. It's what the mesher's own ridges were for, and those are off here (`no_stem_ridges`), with the fillets it made from the foot out to each root's old path. Those fillets are why the foot looked crumpled once more of it was above ground.
- **Roots go under.** A thick root lies part buried and sinks along all it shows, gone by 5 of its radii (`visible_radii`), before it's thin, so what's left of a long root is under the soil, in `_roots`. That number is what to change if you want more of them to show. A tube that keeps its thickness cuts level ground in a long rounded tongue. It's a thin one tapering as it crosses that draws a spike.
- **One colour.** A root's bark is the foot's, in low contrast (`root_colour`, `root_contrast`), and the foot stains to that colour down each swell and a little all round at the ground (`stain_*`), so the two meet in colour too.
- **Moss.** Tufts and clumps on one side of the stem, thinning out with height and round the stem, so there's no edge and no collar (`moss_*`). Thin on white bark, which shows it pale.

The stem's foot takes whole rings, cut by each ring's mean height, 10 cm below the ground line. Below that the stem leans off along the taproot and its rings tilt, so one side of them can come up to the ground. A swell pushed that open edge out into a flat flap on the default roots at ages 50 and 60. Those rings now go with `_roots`. A swell also ends in a slope, over twice the height of the root's top, so a thick root's has no wall at its end.

The mesher also had a hole in it, now closed where relief is asked for: a sample was dropped if it was close to the last sample, kept or not, so where many roots' windows overlap a dense run dropped itself whole. The stem's foot had gaps of up to 7 cm between rings, which showed as a band.

**How it looks.** The foot flares into the ground, with roots low and sinking. All values are `TUNED` by eye against the Arnhem-Delhuyzen and Brastad photos in `birch-data/summer_reference`; I found no measurement. The placement in the test was not the fault: the game's own `Mounds` are round stones only, with no soil heaped at a tree, so a flat plane is close to what the game does. What's left: with no soil or litter heaped against it, a swell meets a flat plane in a clean, wavy edge. On the game's real ground I haven't seen it.

**What the model would have to change.** Roots stop showing a short way out, because the model's own main roots are few and taper fast. At age 60 the largest is 9.0 cm radius at its base, 2.8 cm at 0.5 m and 1.3 cm at 1 m; the next are 4.4, 3.1, 2.4, 2.3 and 2.2 cm at their bases; and they go down quickly. A real old birch has more roots at its surface that stay thick further out and sink along their length. That's a growth change in `treegen/roots.py`, not the export.

### With roots that cost carbon (`roots.paid`, off by default)

`--set roots.paid.enabled=true --set geometry.root_flare_min_share=0.5 --set roots.lateral_setpoint_deg=92 --set roots.lateral_gravitropism_per_m=3.0`

The roots themselves change in growth (`treegen/roots.py`, `update_radii_paid`): more of them at the collar, thicker, tapering as excavated birch does. The export then does these, only when that setting is on, and all in `appearance.game.unreal.roots` as `paid_*`:

- "Thick" goes by the stem foot's radius, not the root collar's, since the collar is now the real stump: 25 % of it, so 12-15 roots show at age 60 on the three seeds exported.
- The stump's mass stays in the model, but what's drawn is the stem's foot. Otherwise a 40 cm stump makes a bulb under a 30 cm stem.
- A root's radius already holds its bark, as its density does, so no wall is added.
- `geometry.root_flare_min_share` is for the plain export's ridges. In this target it's the swells above that shape the foot, for roots at least 45 % of the thickest's radius, and they don't pile up either.
- A root that shows goes under gradually along its length, never rising once it's going down, and stays under. Otherwise the model's up-and-down path made loose sausages on the ground.

With these settings, seed 1, the nearest level:

| Age | Height, m | Nearest level | of which wood | roots with the tree | leaves | Roots showing | Out to, m |
|---|---|---|---|---|---|---|---|
| 15 | 12.2 | 278,067 | 46,766 | 6,937 | 223,980 | 2 | 0.26 |
| 50 | 25.7 | 1,603,315 | 410,648 | 20,463 | 1,166,700 | 11 | 0.55 |
| 60 | 27.3 | 1,696,939 | 484,248 | 23,005 | 1,183,350 | 12 | 0.52 |

### The file's origin is below the tree, on purpose

Unlike the game's own trees, these files have their origin 32 cm below the tree's lowest point. Here's why.

Long streaks of green and dark ran up the lowest part of the stem, on our bark and on the game's scan alike. They come from `M_Surface`'s ground contact. It reads a moss texture by world XY, which barely changes up an upright surface, so the moss smears upwards. It applies where height above the mesh's origin, plus up to 6 cm of noise, is under `GroundBlendCm`, 20 cm. **Shown:** the same file and camera with `GroundBlendCm` at 0 has no streaks.

We can't change the game's material, so our data suits it. With the origin 32 cm below the lowest point, nothing in the file is low enough for that moss to apply, and the game's own seat, by the lowest point, is as right as ever. The moss is back in our own stem map instead, by `UV0`, as above. Bark heights in the manifest are in file coordinates (`upper_bark`), and `origin` gives where model zero, the ground and the lowest point are in the file.

## 6. Season change while the game runs

**Tested**, with the game's M_Foliage built by its own script and one line added. The mesh doesn't change. The colour is worked out in the material from UV0 and UV2, so a whole forest changes colour with one number. See `tools/unreal/season_example.py`.

One line in `build_master`'s foliage branch of `build_materials.py`:

    colour_out = season_colour(material, colour, colour_out)

Then set the day whenever you like:

    unreal.MaterialLibrary.set_scalar_parameter_value(world, season_collection, "Day", 283.0)

| Same leaf pixels, same camera, lit in both | Mean colour (sRGB, 0-255) | Red over green |
|---|---|---|
| Baked for day 200 | 90, 105, 74 | 0.86 |
| Live, day 200 | 93, 106, 73 | 0.87 |
| Live, day 270 | 100, 112, 69 | 0.89 |
| Live, day 283 | 140, 134, 71 | 1.04 |

So live and baked agree at day 200, and the leaves turn yellow later. Each leaf turns on its own day, from UV2.

Leaves falling isn't in this example. It needs them to disappear, by mask or by moving them, and both cost more than colour (section 7).

**Stages.** Swap a tree's mesh for its next stage while the player looks away, as the maintainer plans. Stems move a little between stages, so a swap in plain view shows a small jump. A cross-fade would need a masked copy of M_Surface and one more number per instance. That's not tested.

## 7. Replacing a tree's mesh while the game runs

The maintainer's plan: trees grown live, swapped while the player looks away.

**A shipped game can't build a Nanite mesh.** Only the editor can. **Read in source:** the builder is an editor module (`NaniteBuilder.Build.cs`), the engine lists it only in its `bBuildEditor` block (`Engine.Build.cs` lines 404-449), and `StaticMesh.cpp` line 8927 says "In non-Editor builds, we can only perform fast mesh builds". That fast build makes ordinary LOD and ray tracing data, no Nanite.

**Voxelized Nanite Foliage isn't different.** Voxelizing is a setting of the same builder (`NaniteBuilder.cpp` lines 623-632). A shipped game can draw voxels and can't make them. Nanite Assemblies too: they're built by the same module, and Epic's pages list only editor routes (USD, editor utilities, PCG, PVE).

**Options:**

| Option | In a shipped game? | Lumen | Virtual shadow maps | Distant crowns | Cost |
|---|---|---|---|---|---|
| **A. Stages built in the editor, swapped by `SetStaticMesh`** (recommended) | Yes. Swap **tested** in the editor, 0.05 s; not in a packaged game | Yes: "Foliage and Instanced Static Mesh Components can only be supported if the mesh is using Nanite" (**documented**) | Best: Nanite. A swap redraws only that tree's pages. The wind's own cost is what the game's trees pay today | Yes, voxelized in the build (voxel build not tested here) | **Tested:** per stage on disk, 42 MB at age 60, 9 MB at age 15, 7 MB for its `_roots`. Not "any shape": trees come from a library, varied by scale and turn |
| **B. One mesh of the oldest tree, parts hidden or thickened by material** | Yes | "World Position Offset (WPO) is not supported" in software tracing (**documented**) | Poor: world position offset redraws cached pages (**documented**) | Poor: voxelized foliage and world position offset don't mix well (**documented**) | Every sapling costs the oldest tree's triangles. Stems bend as they grow, which a mask can't show. Fine for buds and leaves, not a whole tree |
| **C. Static mesh built at run time, fast path** | Yes (**read in source**) | Hardware tracing: the fast build makes ray tracing data, but no distance field or cards (**read in source**) | Works, costs more: "Non-Nanite geometry is much more expensive to render into VSMs" (**documented**) | Own LODs needed. No Nanite, so 1.6 million triangles a tree won't do. Keep to `_lod1` size | CPU for each tree, memory per unique tree |
| **D. `UDynamicMeshComponent`** | Yes (**read in source**). Copied and drawn in the editor, **tested**: 16,000 triangles in 0.07 s | Hardware tracing: on by default. Its distance field support is deprecated (**read in source**) | As C | As C | As C. Per-tree draw calls, no instancing |
| **E. `ProceduralMeshComponent`** | Yes (**read in source**) | Hardware tracing: on by default. Its code has nothing on distance fields or Lumen (**read in source**) | As C | As C | As C, and no LODs of its own. The game's own research note: "ProcMesh terrain can't be Nanite" |

**What I'd do.** Grow the library in advance: this project grows the tree, and the editor builds each stage. At run time, the game's growth picks the nearest stage and scale, and swaps while the player looks away (A). If one special tree must be truly unique, say next to the player's home, use D at `_lod1` size for that tree alone.

A library of 14 stages for one tree is about 400 MB of mesh on disk in the editor, and five variants of it about 2 GB. That's the editor's asset, with its source mesh. I haven't measured a cooked game.

## 8. Making it beautiful

**Recommendation.** Take shape, age and roots from this project. Take the look from the game's scans and materials, with our ageing rules deciding where each bark shows. Keep our procedural textures as the fallback, and for young stages and the black base, where no scan fits.

Seen side by side in Unreal (section 9), the scan has detail and colour that our procedural white bark doesn't. Our black base holds up well. Our bark isn't the weak point: the crown is, by a long way.

Today, with no change to the game's materials, M_Surface's `UpperBark` switch does most of this. It fades from the colour map to a tiled scan by height. **Tested:**

- `BaseColor`: our bake, which holds the black base.
- `BarkColor`, `BarkNormal`, `BarkRoughness`: the scan, wrapped on UV1.
- `BarkStartCm`, `BarkBlendCm`: per stage, in `game_manifest.json` under `upper_bark`. Add about 40 cm to the start: the game's join wanders with the scan's green, which brings it down by that much on this scan.
- `BarkGain`: 0.191 / the scan's mean luminance, as `set_tree_looks.py` does. 0.6 for the game's birch bark.
- Branches: the same, with `BarkStartCm` far below the ground, so they're all scan.

For the whole job later, addition 9 blends three layers from UV3: young brown, white scan, black scan.

### Depth in the bark

The nearest level's stem has the bark's own height map in its mesh, so plates stand out of the outline and cracks hold shadow. It's the same height map as the colour and normal maps, from the same ageing rules, so depth follows a part's age and height:

| Age | Deepest crack in the mesh, mm | Highest plate, mm | Wood triangles |
|---|---|---|---|
| 5 | 0.1 | 0.2 | 36,372 |
| 15 | 4.1 | 1.5 | 50,876 |
| 30 | 15.1 | 1.5 | 341,067 |
| 50 | 19.7 | 1.6 | 623,095 |
| 60 | 21.2 | 1.5 | 763,241 |
| 100 | 27.0 | 1.6 | 1,283,751 |

The mesh is finest where the cracks can be deep, up to the highest of the base's tongues: 5 mm at the old base, 3 cm up on young white bark (`appearance.game.unreal.stem_relief`). `edge_fine_m: 0` turns it off. The normal map holds everything the mesh can't, and half of what it can, as a mesh shades only as sharply as its edges are short (`normal_keeps_deep_share`). `_lod1` has a smooth stem and its own map, `<slot>_lod1`, with everything in it.

**Nanite displacement tested against it.** Same camera, same age 60 stem.

| | Relief in the mesh (used) | Nanite Static Displacement, build-time |
|---|---|---|
| Looks | Real outline, plates, cracks in shadow | The same, near enough to call a tie |
| Leafless triangles at age 60 | 727,189 | 310,873, from 280,567 before the build, on the level base |
| Through the game's scripts | Yes, unchanged | Needs one more step on every stage, after import: set a height texture on the mesh, and rebuild |
| Other levels and other engines | It's in the file | Nanite only. `_lod1`, a fallback or anything else sees the smooth tube |
| Epic's status | Plain mesh | Experimental |
| How exact | To the mesh's edge length, chosen by height | One error for the whole mesh and all its slots, by its size (`NaniteDisplace.cpp`) |

So relief in the mesh, for now. If triangles come to matter, displacement saves about 57 % of the leafless tree and looks the same: `tools/unreal/game_route.py`, job key `static_displacement`.

**Runtime tessellation wasn't tried.** It needs `r.Nanite.AllowTessellation=1`, read only at start, in the game's config, plus `Enable Tessellation` and a Displacement input on `M_Surface`. Epic's "Working with Nanite-Enabled Content" says it doesn't change shading, is experimental, and has "serious impacts on performance, especially with virtual shadow maps". That's a change to the game, with a cost at run time, for a picture that build-time already gets.

### The top of the black base

**What was wrong, twice.** The rough stage climbed to one height all round the stem, so the black base stopped at a nearly level line, the same on every tree. Then, with that fixed, about half the stand trees still had a plain black sock that faded out at the top. Those were trees whose leader was lost when they were young. The old leader's last node lived on as a thread about 1 mm thick, so the mesher took it as a living fork and drew the real trunk as a branch. A branch gets no stem map: no tongues, no plates, just a smooth tint by height. The trunk now stays the stem past a thread no thicker than a quarter of the replacement's radius (`stem_stub_share`, `mesh.continue_trunk`).

**Now.** `bark.uneven_top`, read by the same ageing rules for each texel of the stem's map, not each row:

- **Tongues.** The top reaches further in places, and further up one side of the stem than the other.
- **Hard edges.** At each height a share of the bark has gone over, more low down. Which bark goes first is a field of patches longer than they're wide (`islands`), so what shows is black tongues and white plates at a size you can see from a distance, not a soft fade.
- **Every old stem.** All of it has gone over below `solid_share`, whatever the tree, and most of it for some way above that, with a few white plates left.
- **Tree to tree.** Each `--seed` makes its own stem: its pattern, which way it faces, how dark it is, and how high it goes (below). The pattern is the tree's, so it stays in place as it climbs from age to age.
- **Plates.** Rough bark's plates at their real size, 3 cm across and 16 cm long, lighter on their faces, so the fissures show.

**How high, tree by tree** (`bark.uneven_top.black`). Measured in Swedish trials as the height where smooth silver bark takes over (Jones et al. 2021, Forests 12:159; 2023, Forests 14:2031, publisher's PDFs):

| Trial | Age | Trees | Mean DBH | Mean black | CV | Range | r with DBH |
|---|---|---|---|---|---|---|---|
| Hyssna | 19 | 1141 | 110 mm | 67 cm | 65 % | 0-280 cm | 0.53 |
| Brunsberg | 19 | 1390 | 98 mm | 46 cm | 74 % | 10-240 cm | 0.51 |
| Southern Sweden | 15 | 118 | 110 mm | 70 cm | 48 % | not read | not read |

So: black = the tree's own share x 0.61 m x (DBH over bark / 10.6 cm)^1.36. The share is fixed for life, a gamma of mean 1, kept to 0.15-4.2. It rises only as the stem thickens, so it never falls or jumps. The black height is where half the bark round the stem has gone over; the tongues and patches above it are as before. Guessed: that one tree follows the between-tree line as it thickens (nobody followed one tree), and that the spread at 15-19 holds at 50-60. The side of the stem has no source.

15 stand trees, Crown 2's settings (`tools/black_height.py`):

| Age | Black, mean, m | Lowest tree | Highest tree | CV | Highest tongue, lowest to highest tree | Black in the lowest metre |
|---|---|---|---|---|---|---|
| 15 | 0.22 | 0.05 | 0.38 | 37 % | | |
| 30 | 0.95 | 0.20 | 1.67 | 40 % | | |
| 50 | 2.05 | 0.42 | 3.61 | 39 % | 1.2 to 11.3 m | 44 % to 100 % |
| 60 | 2.41 | 0.51 | 4.36 | 40 % | 1.4 to 11.3 m | 51 % to 100 % |

These stand trees are close in DBH (24-31 cm at 60), so the share does most of it. The 40 % here is below the trials' 48-74 %: these 15 seeds drew close shares; over 4,000 draws the rule gives 58 % at one DBH and 71 % with a stand's DBH spread.

**Thin limbs.** White now starts at about 2.5 cm over bark and is complete at about 7 cm (`uneven_top.stage_ramps`), where it was 1.2 and 4.2 cm. By eye, from `reference/meilen_switzerland_solitary.jpg`, `oslo_norway.jpg` and `hallinden_sweden.jpg`, judging limb widths against the stem's in the same photo: limbs of about 5 cm and over are white, and those of 2 to 3 cm are dark. `birch-data/REPORT.md` says branches stay white, with no source, and the photos don't bear that out for thin ones.

The values are `TUNED`, by eye against those photos and `reference/brastad_sweden_first_snow.jpg`, `reference/gullmarsskogen_stand_5.jpg` and the Arnhem-Delhuyzen, Bouleau verruqueux and Hange-Birke photos in `birch-data/summer_reference`. I found no measurement of any of it.

**Limbs: no hoops.** Limbs showed dark red hoops, and a hard ring where white met red. Two causes, both in the branch atlas, which had one column to each circumference class, holding the mean bark of all its parts:
- A limb's colour jumped where it crossed a class edge, at 2.7 and 5.4 cm over bark, inside the white ramp. Columns held 0, about 0.3 and about 0.93 of white (`tools/limb_bark.py`, 3 trees at 50 and 60), while the parts in the middle class ranged from 0.01 to 0.68.
- At about 0.3 white, the white stage shows through its own reveal pattern, which is strips 7 cm wide and 9 mm tall (`reveal_patch_m`), made for peeling on the stem. Round a limb of 12 cm, that's hoops.

Limb radius isn't the cause: on every limb it only falls going out. Now (`bark.uneven_top.limbs`) there's a column for each eighth of white at each circumference, and a face reads the one its own thickness and age give. White goes on in hard-edged patches longer than they're wide, set in turns round the limb and metres along it, the same at every level and circumference, so more white only adds to what's there. The largest step from one node to the next on a limb: median 0.125 of white, was 0.26-0.33. The atlas is 4096 x 2048, holding a metre of limb. Patch sizes are TUNED by eye on `reference/hallinden_sweden.jpg` and `oslo_norway.jpg`.

**Where it's on.** In this target, by `game.unreal.stem_relief.uneven_top: 1`. In the plain export it's off, so its bytes don't change. `--look bark.uneven_top.strength=1` turns all of this on there, and each export's `--seed` then gives its stem its own base. `tools/crown_look.py` does so.

### Leaves

**Outline.** Traced from real leaves, Commons' `Birkenblaetter Betula pendula.jpg` (Roletschek), and it agrees with what's published: "Triangular, the end drawn out to a slender tip, hairless, margin toothed, with every 2nd to 4th tooth much longer than the others" (Burren flora, Naturalis), and acuminate apex (Atkinson & Codling 1986, Watsonia 16:75-87). I found no published mean ratio, tooth count or widest point: length over width 1.32, widest at 32 % and 7 main teeth a side are off the photos, and labelled so.

**Mesh.** 26 triangles a blade: curved margin, main teeth at the side veins' ends, a midrib of 6 points with a fold of up to 26 degrees, curl and droop to the tip, a slight twist and ripple, all differing from leaf to leaf, with two outline variants, either way round. 4 more in a stalk, from the twig's surface, arching down to the blade. Small teeth are cut by the colour map's alpha at the game's clip, 0.35. The leaf's length comes from the model's area, so visible area matches it: section 2's check.

**Angles.** From Hagemeier & Leuschner 2019a (Forests 10:265): mean 49 degrees from the horizontal, about 55 at the top, about 30 in the lowest shade crown, all hanging. In the file, measured base to tip, curl included:

| Age | Height, m | Crown mean, by leaf area | Top tenth of the crown | Lowest quarter | Hanging | Mesh's leaf area, m2 | Model's, m2 |
|---|---|---|---|---|---|---|---|
| 5 | 5.7 | 41 | 55 | 38 | 100 % | 12.02 | 11.99 |
| 15 | 12.0 | 41 | 54 | 37 | 100 % | 16.95 | 16.98 |
| 30 | 18.8 | 41 | 54 | 31 | 100 % | 60.34 | 60.41 |
| 50 | 24.6 | 46 | 54 | 30 | 100 % | 80.59 | 80.46 |
| 60 | 26.1 | 50 | 53 | 30 | 100 % | 81.84 | 81.85 |
| 100 | 29.7 | 52 | 55 | 50 | 100 % | 85.86 | 85.67 |

Age 15 falls under the crown mean because the table goes by height in the tree, as the paper's does, and its crown sits low. The paper is on mature trees.

**Size.** "Smallest at the top, growing linearly down" is the paper's. This comes from the model's own light response, and the export doesn't touch it: leaf area stays the model's. Age 15 shows it; age 60 barely does.

| Age | Leaf area, cm2: top fifth of the crown | next | next | next | lowest fifth |
|---|---|---|---|---|---|
| 5 | 10.3 | 10.3 | 11.6 | 13.6 | 15.9 |
| 15 | 10.4 | 11.1 | 15.2 | 17.2 | 17.4 |
| 30 | 15.9 | 16.8 | 17.5 | 17.7 | 17.9 |
| 50 | 16.3 | 17.6 | 17.9 | 17.9 | 17.9 |
| 60 | 16.7 | 17.9 | 18.0 | 18.0 | 18.0 |
| 100 | 15.2 | 17.0 | 17.7 | 17.8 | 17.9 |

The paper's extract gives no slope to apply. So if age 60 should show more, that's a growth change to look at. The file used is from before the Tree agent's current work, so it may have changed already.

**Spread.** In the model nearly every leaf is about 18 cm2: P5-P95 13-18 at 50 and 60, CV 7-10 %. That's the shade end of `light.sun_shade`, where LMA tends to 50.5 g m-2 and size to 15 x 60.8 / 50.5 = 18.1 cm2. The rule takes Hagemeier & Leuschner's LMA by relative height and feeds it the leaf's relative light instead (marked VERIFY), and most leaves' light is low. With `leaves.on_shoots`, each leaf now gets a size of its own round the model's, CV 30 % (from Kovacic & Nikolic 2005's lamina lengths, *B. pendula*, 5,000 leaves), kept to -2.2 and +1.5 SD. The tree's total leaf area and its number of leaves stay the model's. At 50 and 60 (3 trees): CV 0.28, P5-P95 10-26.5 cm2, mean unchanged.

**The mean looks high.** The model's mean leaf is 17.0-17.3 cm2. *B. pendula* measured: 11.89 +- 5.73 cm2 over 3,672 leaves of 204 young trees, 8.8-15.8 by site (Konopka & Pajtik 2026, Cent. Eur. For. J. 72:159); laminae 42-47 x 31-36 mm in Croatia (Kovacic & Nikolic 2005), about 8-10 cm2 at a birch leaf's fill. The 15 cm2 reference is derived from shoot totals, not measured per leaf. Konopka & Pajtik also find the largest leaves high in the crown of dominant trees, where the model has its smallest. Both are growth matters, for Crown 2.

**Along a twig** (`leaves.on_shoots`, `tools/leaf_placement.py`). A node's leaves used to leave from one point, on any side, a petiole off the bark. Now:

| | Birch | Source | Before | Now |
|---|---|---|---|---|
| Leaves on a short shoot | 2-3 | Suzuki 2003 (*B. maximowicziana*); Caesar 1983 (*B. papyrifera*) | 2.5 | Same |
| Petiole | 17-19 mm | Kovacic & Nikolic 2005, *B. pendula* | 18 mm | Same |
| A short shoot's own length | A few mm a year, rarely over 4 cm at 10 years | Caesar 1983 | None | 3 mm a year, up to 4 cm |
| Side of the twig | Two ranks on long shoots | Trees and Shrubs Online (genus) | Any | The side the model's bud faces |
| A cluster's leaves | Opposite or whorled; 2/5 | Suzuki 2003; Caesar 1983 | Random, 17 % of pairs within 30 degrees | 144 degrees apart |

Placing them right doesn't make the crown fuller: crown fill side on rose by 1-2 points, and a twig's leaves still look about one blade wide.

**Scans and licences:**

| Scan | Licence | Fit | Note |
|---|---|---|---|
| Mantissa birch pack (the game's `betula_pendula`) | CC0, author asks for a mention, as noted in the game's research | White upper bark, leaves | Already in the game. Used in the test project only |
| cgbookcase Birch Bark 01 | CC0-1.0, listed in the game's `wave2_fetch.json` | White bark | Not under `SourceArt`: needs fetching. I haven't read its page |
| Poly Haven | CC0 | Pine bark, soil, moss | The game's source. No black birch base |
| ambientCG | CC0 | Moss, ground | Same |

No black birch base scan is in the game's collections; the game's `03-trees.md` lists it as a gap. So our procedural black base stays until one's found or photographed.

## 9. What was tested

All in `out/unreal_test/TreeTest`, an empty project, Unreal 5.8.4, no window. The game's `build_materials.py` and `import_world_assets.py` were copied in and run unchanged, except for one added line for the season test. Files: seed 5, grown in a stand.

**What came back:**

| File | Triangles in Unreal | UV sets | Vertex colour | Slots | Lowest point, cm |
|---|---|---|---|---|---|
| Age 15, nearest | 365,674 | 4 | Yes | 5 | 32.0 |
| Age 15, `_lod1` | 16,000 | 4 | Yes | 4 | 32.0 |
| Age 15, `_lod2` | 12 | 1 | Yes | 1 | 32.0 |
| Age 15, `_roots` | 16,318 | 4 | Yes | 1 | -54.2 |
| Age 60, nearest | 2,208,447 in the file; see below | 4 | Yes | 5 | 32.0 |
| Age 60, `_lod1` | 16,000 | 4 | Yes | 4 | 32.0 |
| Age 60, `_lod2` | 12 | 1 | Yes | 1 | 32.0 |
| Age 60, `_roots` | 191,929 | 4 | Yes | 1 | -79.9 |

Age 60's nearest level came back whole at 1,947,669 triangles. Since then the uneven base and the foot have made it 2,208,447, and I couldn't save that one here: Unreal's log shows its Nanite build finishing, then free memory fell to 1.21 GB from 8 GB and the runner stopped it, and 8.6 GB didn't come free in the half hour I waited to try again. The pictures of age 60 since then use its leafless file, `_winter`, which came back whole.

The game seats each mesh by its own lowest point, and every level of these ages now has it in the same place, so they stay in line. (They were up to 9 cm apart before.)

**What I saw:**

- The bark, its depth, normal maps, shadows and our moss at the foot all work through the game's materials.
- Nanite's fallback mesh is small: under 900 triangles at age 60, 1,336 for the game's birch. Where anything uses the fallback, such as ray tracing that doesn't trace Nanite itself, it sees a rough blob of the crown. Same for both trees. I didn't look further.
- `_lod1`'s leaf cards came out darker than the nearest level's leaves: more of each card sits in other cards' shadow. Not fixed. With Nanite you won't draw them.
- Leaves in shade, and leaves seen from below, come out black in these pictures, ours and the game's birch alike. **That's the test scene, not the leaves or `M_Foliage`.** See below.
- `DistanceFields` are off in the test project (`r.GenerateMeshDistanceFields=False`) to save memory on this PC. The game has them on.
- `_lod2` close up shows its crossed sheets, as expected. It's for far away.

**Why shade is black in these pictures.** They're all scene captures, because a windowless editor has nothing else to draw. A scene capture can't update a real-time sky light: `AllocateAndCaptureFrameSkyEnvMap` returns at once for one (`ReflectionEnvironmentRealTimeCapture.cpp`, **read in source**). So the sky light stays empty, and shade gets no sky at all. The game's sky light is real-time too (`WorldClock.cpp`, line 97), but the game has a real view to update it.

| Same trees, same cameras | Ground in shade, as a share of ground in sun | Age 15 leaves picture, near-black pixels | The game's birch, near-black pixels |
|---|---|---|---|
| As in all these pictures | 0.3 % | 64 % | 70 % |
| 1.0 in place of 0.25 for light through a leaf (test copy of `M_Foliage`) | not measured | looks about the same | not measured |
| Stand-in for the missing sky: 15,000 lux down and 8,000 up, no shadows (`fill_lux` in a job) | 9 % | 53 %, and those left have colour and veins close up | 62 % |

The ground has no leaves and no `M_Foliage`, and it's as black as they are. Real open shade on a clear day is more like 10 to 25 % of full sun, from memory, not measured here. Two tries at a real sky failed: capturing the sky light the old way, with Lumen on and off (0.5 %), and turning on the level viewport (0.3 %; a windowless editor doesn't appear to draw it). So the stand-in is only a stand-in, and I haven't seen the real sky on these leaves. That needs the game, or an editor with a window.

**Beside the game's birch.** Same project, same sun, sky and camera. Pictures: `out/unreal_test/sheets/`, `out/unreal_test/shots_final/` (this comparison, and the "before" of the bark and leaf work) and `out/unreal_test/shots_f/` (now), kept out of the repository because they hold scanned textures.

| | Ours, age 15, stand-grown | Ours, age 15, open-grown | The game's birch, `_a` |
|---|---|---|---|
| Size | 12 m tall, 2.5 m wide | 13.4 m tall, 9 m wide | 11 m tall, 7.3 m wide |
| Crown | A pole with a small crown | Heavy flat tiers on a bare stem | Full, with long hanging curtains |
| Leaves | About 6 cm long, from the model's area; 10,436 | Same; 87,234 | About 15 cm by eye; large leaves make up the mass |
| Bark | Clean white, a bit too clean | Same | Scanned, rich |

The game's birch looks better, and the crown is why. It isn't close. Bark and leaves through the same materials hold up; the tree's shape doesn't yet. The file used is from before the Tree agent's current crown work, so this should change. Open-grown stems are also far too thick: 31 cm at age 15.

**How this differs from the real game:** no clouds, no moving time, no forest around the tree, no terrain or `M_Ground`, a plain ground with one scanned colour map, a fixed exposure instead of the game's eye model, trees as single meshes rather than instances. So wind runs from each tree's own position. Sun, atmosphere, sky light, fog density, Lumen, virtual shadow maps and Nanite settings are the game's. Shaded sides are far too dark here, as above.

**Not tested:**

- A voxelized Nanite build, of ours or the game's. It needs 11 GB free on this PC by the agreed limit, and free memory never passed about 8.8 GB. So "leaves voxelize well" is from Epic's guidance and the mesh's shape, not seen.
- Distance fields on the bigger mesh, and so Lumen's software tracing with it.
- Our stem on real terrain, with the game's grass and its `root_flare_tile` taken off. Only on a flat plane.
- Runtime tessellation (section 8).
- Any of this under the game's real sky: pictures here have no sky light in them (above).
- A packaged game. Everything ran in the editor.
- The game itself, its world and its forest. Nothing was run in the game.
- Instancing, wind in motion, and frame times. Pictures are still, from a scene capture.
- Reading `COLOR_0` for wind (Kit 1). The data arrives; the switch is off.
- Autumn or spring exports through the import. The season test used the live material.
- Whether the plain import's own materials use vertex colour: the source says not, and the game replaces them.

## 10. Running the test yourself

    python tools/unreal_test.py route <job.json> --export out/game/unreal --label mytest

It makes an empty project under `out/unreal_test/`, copies what it needs, and starts Unreal with no window. It won't start while Unreal or the game is open, or with under 6 GB free, and it stops Unreal if free memory falls under 1.5 GB. Results go in `out/unreal_test/results_<label>.json`. Copied scans stay in that git-ignored folder.

Unreal 5.8 logs this PC's Visual C++ runtime as outdated, which makes command-line runs exit with code 1. The runner judges by other errors and the results file.

Pictures need real frames, which a command-line run doesn't have, so `render` runs the editor itself with `-RenderOffScreen`. Texture streaming is off in the test project, because a scene capture doesn't tell the streamer where it's looking. Distance fields are off too, to save memory.
