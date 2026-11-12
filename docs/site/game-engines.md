# Use in game engines

Cambium writes self-contained glTF 2.0 files (`.glb`) with PBR textures. Any engine that reads glTF can load them. There is one file for each age, season and level of detail.

## Make the files

```python
import cambium

tree = cambium.grow(species="birch", seed=5, years=60, stages=(15, 30))
tree.export("out/birch5_game", format="glb", ages=(15, 30, 60), seasons=("summer", "autumn"))
```

```python
tree.export(path, format="glb", lod=None, ages=None, seasons=("summer",), textures=True, timelapse=False)
```

| Argument | Meaning |
|---|---|
| `lod` | `None` writes every level. `"lod1"` or `["lod0", "lod1"]` picks some. `lod2` is drawn from `lod0`, so asking for `lod2` writes `lod0` too |
| `ages` | Which ages to write. Ages before the last need `stages=` when you grow the tree |
| `seasons` | Any of `spring`, `summer`, `early_autumn`, `autumn`, `winter` |
| `textures` | `False` is a quick look at the geometry: the same meshes, with no textures in the files and no `lod2`, which is nothing but a texture. On the command line: `--no-textures` |
| `timelapse` | `True` is for a film of one frame a year: leaves are not new each spring. See [Growth stages](#growth-stages). On the command line: `cambium export --timelapse` |

On the command line:

```
cambium grow --species birch --seed 7 --years 60 --export glb --lod lod0,lod1 --seasons summer,autumn
cambium export --species birch --seed 5 --ages 15,30,60 [--forest] [--format glb|usd]
               [--lod ...] [--seasons ...] [--no-textures] [--timelapse] --out DIR [--quiet]
```

`cambium export` grows the tree to the oldest age and writes each age as a stage. Add `--forest` for a tree grown among neighbours (tall and narrow) instead of in the open (wide).

## What you get

Files are named by species, age, season and level:

```
betula_pendula_age060_summer_lod0.glb
betula_pendula_age060_summer_lod1.glb
betula_pendula_age060_summer_lod2.glb
game_manifest.json
```

`game_manifest.json` describes the run (species, seed, open or stand), the units, the levels and their budgets, and for each age: height, stem diameter over bark, leaf count and leaf area, and each file's triangle count. It also lists what an engine material needs (below). Every file is read back through a glTF check before the manifest is written.

**Units and axes:** Y-up, metres. The ground is at y = 0, with the stem base at the origin.

The `.glb` files hold the tree above the ground. For the roots, use the USD export (`format="usd"`, see [Grow a tree](grow.md#research-meshes-usd)).

## Levels of detail

The levels come from the species file (`appearance.game`). Budgets are triangles.

| Level | What it is | Budget |
|---|---|---|
| `lod0` | The full mesh: every branch, single leaf blades, and strips of peeling bark | None |
| `lod1` | Reduced wood, and leaf cards in place of single leaves | 16,000 triangles |
| `lod2` | For far away: three crossed cards, drawn from `lod0` | 12 triangles |

Wire them to the engine's LOD group by file name. `lod2` is alpha-tested sheets, back to back. Close up, its crossed cards show. Don't let `lod2` cast shadows from its cards, because they fall on each other: use `lod1`'s shadow or a blob.

If your engine has Nanite or something like it, `lod0` is the one that matters. `lod1` and `lod2` are there for anything that can't use it.

## Growth stages

To export several ages of one tree, list the earlier ages when you grow it:

```python
tree = cambium.grow(seed=5, years=60, stages=(5, 15, 30))
tree.export("out/stages", format="glb", ages=(5, 15, 30, 60))
```

Each stage is the same tree at a different age, with the same origin and the same node ids. To show a tree growing, swap to the next stage while the player is looking away, or cross-fade (dither) between two stages. Stems move a little between stages, so a swap in plain view shows a small jump.

A stage's leaves are that spring's. From one year to the next a leaf keeps its shoot and its side of the twig, and hangs, rolls and turns colour in its own way; the number of leaves and their area stay the model's. A game that shows one stage for several years shows the same leaves in each of them. For a time-lapse, a film of one frame a year, export with `timelapse=True` (`cambium export --timelapse`): every leaf then hangs as it did the year before, because new leaves in every frame read as shimmer.

## Seasons

`spring`, `summer`, `early_autumn` and `autumn` colour the leaves for a day of that season. Each leaf turns on its own day, so autumn comes in gradually through the crown. `winter` has no leaves. The wood is the same in every season.

## What an engine material needs

- **Core:** glTF 2.0 PBR metallic-roughness, 32-bit indices, embedded PNG and JPEG textures, tangents supplied.
- **Vertex colour:** branches and leaves multiply their base colour by `COLOR_0` (16-bit, linear). Your material must use vertex colour, or the branches all come out one colour.
- **Alpha:** leaves, leaf cards and bark strips use `alphaMode` MASK, cutoff 0.5. Bark strips carry their opacity in the alpha of `COLOR_0`, which multiplies the texture's alpha before the cutoff.
- **Two-sided:** leaves and leaf cards are `doubleSided`, so shade the back as well as the front. Bark strips are two one-sided sheets.
- **Light through leaves (optional):** leaves carry `KHR_materials_diffuse_transmission`. It isn't required: without it, the base colour alone holds the brightness of a leaf lit from both sides.
- **Bark height map (optional):** bark materials name a height map in `extras.heightTexture`, with its range in metres in `extras.heightRange_m`, for parallax or displacement. It isn't a core glTF slot, so importers ignore it.
- **Custom vertex attributes (optional):** `_NODE_ID` (the same id for the same part at every age), `_RADIUS`, `_LEAF_SUN` and `_LEAF_TURN` (how many days later or earlier than the tree's average a leaf turns colour).

Bark materials (`bark_stem`, `bark_branch`) have a base colour, a normal map and one texture for occlusion, roughness and metalness, packed as glTF expects.

## Unreal Engine

These notes come from tests in Unreal Engine 5.8, and from reading its source where a test wasn't possible.

- **Import:** use Unreal's own glTF importer (Interchange). Metres become centimetres and Y-up becomes Z-up on import. Positions, normals and triangles come through exactly.
- **Levels:** import each level and set them up as the LODs of one static mesh, matched by file name. With Nanite, use `lod0`.
- **Vertex colour:** the materials the importer makes don't appear to use vertex colour (read in Unreal's source, not tested). Make your own material that multiplies base colour by Vertex Color. Unreal stores vertex colour at 8 bits, so the smallest step that comes back is 1/255.
- **Leaves:** set the leaf material to Masked, Two Sided, with the opacity mask from the base colour's alpha. The alpha cutoff and the two-sided flag do come through on import.
- **Kept:** base colour and normal maps, the alpha cutoff, two-sided flags, wrap modes and material names (as slot names). Tangents are kept on ordinary meshes; Nanite doesn't store them.
- **Dropped:** `KHR_materials_diffuse_transmission` (the log says the extension is not supported, and the import carries on), the custom attributes (`_NODE_ID` and the rest: Unreal keeps only position, normal, tangent, UVs, colour, joints and weights), and the bark height map.
- **A log error you can ignore:** any masked glTF material logs "Invalid input AlphaMode for material expression node MF_Default_Body". It comes from Unreal's own default material function. It goes away once you use your own materials.
- **Memory:** a full-detail old tree is a heavy import. Import one at a time, with plenty of free memory.
- **Stages at run time:** a shipped Unreal game can't build Nanite meshes; only the editor can. So import each stage in the editor, and swap a tree's mesh for the next stage at run time (for example with `SetStaticMesh`).

The files carry no wind data: any sway comes from your own materials.

Not tested: voxelised Nanite foliage and a packaged game.
