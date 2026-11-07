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
| 5 | 5.7 | 8,711 | 280,382 | 36,336 | 138 | 0 | 243,908 | 16,000 | 12 | 4,494 | 22 |
| 15 | 12.0 | 10,436 | 341,940 | 47,962 | 1,322 | 448 | 292,208 | 16,000 | 12 | 15,908 | 27 |
| 30 | 18.8 | 34,856 | 1,138,090 | 156,074 | 3,360 | 2,688 | 975,968 | 16,000 | 12 | 59,338 | 88 |
| 50 | 24.6 | 46,312 | 1,550,267 | 241,584 | 6,571 | 5,376 | 1,296,736 | 16,000 | 12 | 143,969 | 120 |
| 60 | 26.1 | 47,728 | 1,616,160 | 265,630 | 7,874 | 6,272 | 1,336,384 | 16,000 | 12 | 190,572 | 124 |
| 100 | 29.7 | 49,408 | 1,727,301 | 318,813 | 14,760 | 10,304 | 1,383,424 | 15,999 | 12 | 391,979 | 132 |

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
- **Leaves: 28 triangles, not 44.** Eight rows miss the outline by at most 0.75 mm on a 5 cm leaf; twelve rows miss by 0.79 mm. The game's own ground plants use about 32 a leaf.
- **Nothing lost that can be seen.** Leaf area, height and width don't change. Wood surface stays within 0.02 % once hidden rings are gone. Whole tree at 1,100 pixels tall, same camera, ages 50 and 60: it covers the same share of the view to 0.03 of a percentage point, and about 3 % of its outline pixels differ, mostly twigs thinner than a pixel. Side by side I can't see a difference.
- **Clean.** At ages 15 and 60: no degenerate faces, no repeated faces, no unused vertices. Stem, roots and leaves have no bad slivers; twigs have some, being thin.

Leaves suit voxels: real outline in the mesh, no alpha to lose, a midrib fold that gives them some depth, area exactly the model's.

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

Age 60's nearest level needed about 5 GB of memory and took about 100 seconds, of which the Nanite build 16 seconds. Unreal's own estimate was 3.1 GB. Import one heavy variant per run, as `import_all.py` does.

### What the game's scripts would need added

None of this has been changed in the game. Numbers 1-4 let the tree in. The rest make it better.

| # | File | What to add | Why |
|---|---|---|---|
| 1 | `Tools/Assets/import_all.py` | Look for `.gltf` as well as `.fbx` (lines 54, 67-68, 104-105) | It only lists `.fbx`. Running `import_world_assets.py` by hand with `GAME_FILES` works today |
| 2 | `Tools/Assets/measure_trunks.py` | Nothing: use `fragments/trunks.json` | It needs Blender and FBX. The export measures the trunk the same way |
| 3 | `build_materials.py`, `WIND` and `NANITE_SHAPE` | `"betula_pendula_grown": (1100.0, 0.16, 0.30)`, and the name in the voxelized list | Without `WIND` it doesn't sway. Same numbers as the game's birch |
| 4 | `Content/Data/Science/flora.json` | A rule with these variants and `sink_m: 0.10` | The game seats a tree by its lowest point, which here is 10 cm below the ground line |
| 5 | `Source/<Game>/World/WorldGenerator.cpp` line 1176 | Don't add `root_flare_tile` to a rule that has its own roots | Otherwise a made-up flare sits over the real one |
| 6 | `set_tree_looks.py`, `BRANCH` | `"betula_pendula_grown": (1.6, 3.0)` | Same branch sway and flutter as the game's birch |
| 7 | `build_materials.py`, M_Foliage | A `ThroughGain` parameter on line 562, default 0.25 | Fixed at 0.25 of the leaf's colour. Our measured leaves pass about as much light as they reflect, so 1.0 would be right for them |
| 8 | `build_materials.py`, M_Foliage | Section 6's one line, and `MPC_Season` | Season change while the game runs |
| 9 | M_Surface | A third bark layer from UV3 (white, rough) | Full white-to-black from our ageing rules. See section 8 |
| 10 | `build_materials.py`, `rounded_normal` | A separate switch from `PlantKitWind` | Turning on the `COLOR_0` wind (Kit 1) also turns on "round mound" shading, made for ground plants. Until then leave Kit at 0, as the game's birch does |

## 4. What Unreal keeps

| What the plain export carried | Kept or lost | Where it goes now |
|---|---|---|
| Positions, normals, triangles | Kept, **tested**: 16,000, 341,940 and 1,616,160 triangles come back exactly | Same. Metres become cm, y-up becomes z-up |
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
| Leaf | Leaf atlas: column by chlorophyll level | x + 1024 y = node id | x days later or earlier to colour; y light, 0 shade to 1 sun | x chlorophyll on the export's day; y leaf area, cm² | R flex, G phase, B 1, A leaf id 0-254 |
| Bark strip | Strip atlas: column by opacity | x + 1024 y = node id | x birth year; y wood radius, cm | x opacity | R flex, G phase, B 0, A 255 |
| Leaf card | Card atlas: column by chlorophyll | Unused | x mean delay; y mean light | x mean chlorophyll; y leaf area it stands for, cm² | R flex, G phase, B 1, A card id |
| Root | Root atlas: column by circumference | Bark wrap | x birth year; y wood radius, cm | x 0; y how rough | R 0, so a wind that reads it leaves roots still |

A part's age in a material is `stage age - UV2.x`. Vertex colour alpha is overwritten when Nanite voxelizes a mesh (**documented**), so don't rely on the leaf id in voxelized clusters.

## 5. Roots

The roots are the model's own (`treegen/roots.py`). No generic flare is added.

- **With the tree:** the stem's foot and the thick roots (over 1 cm radius), down to 10 cm below the ground line. That reach is what the game's own flare uses, so uneven ground meets them without a gap.
- **In `_roots`:** everything else. It shares its cut vertices with the tree, so no seam. It isn't for drawing above the ground, because the thin roots would show as hairs. It's for a dug-up view, a cross-section, or a game system that needs them.

| Age | Root length, m | Thickest, cm | Deepest, m | Spread, m | Above model's zero, m | Ground line, cm below zero | Thick root above that line, m | Reaching, m | Triangles with the tree | Triangles below |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 26 | 2.4 | 0.81 | 2.2 | 0.00 | 6 | 0.1 | 0.06 | 138 | 4,494 |
| 15 | 96 | 5.3 | 0.96 | 4.1 | 0.05 | 10 | 0.5 | 0.26 | 1,322 | 15,908 |
| 30 | 369 | 9.6 | 1.17 | 7.7 | 0.10 | 16 | 1.3 | 0.66 | 3,360 | 59,338 |
| 50 | 939 | 12.9 | 1.20 | 10.6 | 0.15 | 20 | 2.7 | 1.10 | 6,571 | 143,969 |
| 60 | 1,250 | 14.1 | 1.22 | 11.7 | 0.25 | 20 | 3.1 | 1.45 | 7,874 | 190,572 |
| 100 | 2,613 | 18.4 | 1.24 | 18.0 | 0.60 | 20 | 10.8 | 4.87 | 14,760 | 391,979 |

**Why a ground line.** The model keeps its roots under its own z = 0: at age 60 only 0.25 m of root has any part above it. So the ground meets the tree a little lower, 1.4 collar radii and at most 20 cm (`appearance.game.unreal.roots`). Thick roots then break it, in their real shapes. It's a setting; `ground_line_radii: 0` puts the ground at the model's zero.

This moves where the ground meets the tree, not the tree. No growth number changes. To carry the stem down to the ground line without a step, the mesh keeps the stem's radius there instead of the taproot's smaller one, and adds bark to the thick roots. That's in the export only.

**How it looks.** The foot runs into the ground with roots leaving it, no seam. But few roots show, and the thin end of each reads as a small spike that stops where it falls under 1 cm. Keeping those roots to their tips was worse: the model runs them just under its zero, so they hang as threads over the ground at this line. A real old birch has broader roots at the surface that sink along their length. That's a matter for `treegen/roots.py`, not the export.

## 6. Season change while the game runs

**Tested**, with the game's M_Foliage built by its own script and one line added. The mesh doesn't change. The colour is worked out in the material from UV0 and UV2, so a whole forest changes colour with one number. See `tools/unreal/season_example.py`.

One line in `build_master`'s foliage branch of `build_materials.py`:

    colour_out = season_colour(material, colour, colour_out)

Then set the day whenever you like:

    unreal.MaterialLibrary.set_scalar_parameter_value(world, season_collection, "Day", 283.0)

| Same leaf pixels, same camera | Mean colour (sRGB, 0-255) | Red over green |
|---|---|---|
| Baked for day 200 | 87, 102, 63 | 0.86 |
| Live, day 200 | 87, 101, 64 | 0.86 |
| Live, day 270 | 95, 108, 58 | 0.89 |
| Live, day 283 | 141, 134, 60 | 1.05 |

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
| Age 15, nearest | 341,940 | 4 | Yes | 5, on M_Surface and M_Foliage as they should be | -20.1 |
| Age 15, `_lod1` | 16,000 | 4 | Yes | 4 | -16.8 |
| Age 15, `_lod2` | 12 | 1 | Yes | 1 | -17.9 |
| Age 15, `_roots` | 15,908 | 4 | Yes, flex 0 | 1 | -96.3 |
| Age 60, nearest | 1,616,160 | 4 | Yes | 5 | -30.4 |
| Age 60, `_lod1` | 16,000 | 4 | Yes | 4 | -30.4 |
| Age 60, `_lod2` | 12 | 1 | Yes | 1 | -39.1 |
| Age 60, `_roots` | 190,572 | 4 | Yes, flex 0 | 1 | -121.9 |

The game seats each mesh by its own lowest point, so the levels of one age can sit up to 9 cm apart. At the distances where they swap that won't show.

**What I saw:**

- The bark, normal maps, shadows and moss at the foot all work through the game's materials.
- Nanite's fallback mesh is small: under 900 triangles at age 60, 1,336 for the game's birch. Where anything uses the fallback, such as ray tracing that doesn't trace Nanite itself, it sees a rough blob of the crown. Same for both trees. I didn't look further.
- `_lod1`'s leaf cards came out darker than the nearest level's leaves: more of each card sits in other cards' shadow. Not fixed. With Nanite you won't draw them.
- `_lod2` close up shows its crossed sheets, as expected. It's for far away.

**Beside the game's birch.** Same project, same sun, sky and camera. Pictures: `out/unreal_test/sheets/` and `out/unreal_test/shots_final/`, kept out of the repository because they hold scanned textures.

| | Ours, age 15, stand-grown | Ours, age 15, open-grown | The game's birch, `_a` |
|---|---|---|---|
| Size | 12 m tall, 2.5 m wide | 13.4 m tall, 9 m wide | 11 m tall, 7.3 m wide |
| Crown | A pole with a small crown | Heavy flat tiers on a bare stem | Full, with long hanging curtains |
| Leaves | About 6 cm long, from the model's area; 10,436 | Same; 87,234 | About 15 cm by eye; large leaves make up the mass |
| Bark | Clean white, a bit too clean | Same | Scanned, rich |

The game's birch looks better, and the crown is why. It isn't close. Bark and leaves through the same materials hold up; the tree's shape doesn't yet. The file used is from before the Tree agent's current crown work, so this should change. Open-grown stems are also far too thick: 31 cm at age 15.

**How this differs from the real game:** no clouds, no moving time, no forest around the tree, no terrain or `M_Ground`, a plain ground with one scanned colour map, a fixed exposure instead of the game's eye model, trees as single meshes rather than instances. So wind runs from each tree's own position. Sun, atmosphere, sky light, fog density, Lumen, virtual shadow maps and Nanite settings are the game's. Shaded sides look darker here than they would among other trees and under cloud.

**Not tested:**

- A voxelized Nanite build, of ours or the game's. It needs 11 GB free on this PC by the agreed limit, and free memory never passed about 8.5 GB. So "leaves voxelize well" is from Epic's guidance and the mesh's shape, not seen.
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

Pictures need real frames, which a command-line run doesn't have, so `render` runs the editor itself with `-RenderOffScreen`. Texture streaming is off in the test project, because a scene capture doesn't tell the streamer where it's looking.
