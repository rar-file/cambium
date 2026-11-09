# Grow a tree

## In Python

```python
import cambium

tree = cambium.grow(species="betula_pendula", seed=7, years=60)
print(tree.age, tree.height_m, tree.dbh_cm, tree.crown_width_m)
```

All arguments, with their defaults:

```python
cambium.grow(species="betula_pendula", seed=1, years=60, stand=False,
             environment="sweden_open_field", stages=(), verbose=False, **settings)
```

| Argument | Meaning |
|---|---|
| `species` | A species name, an alias such as `"birch"`, or a path to your own species `.yaml` file. `cambium.species()` lists what is installed. |
| `seed` | The random seed. The same seed gives the same tree. |
| `years` | How many years to grow. |
| `stand` | `False`: the tree grows alone in the open. `True`: it grows among neighbours, as in a forest. See below. |
| `environment` | The site: latitude, season, sky and soil. The one shipped is `sweden_open_field`. |
| `stages` | Earlier ages to keep, so they can be exported as well, for example `stages=(15, 30)`. See [Use in game engines](game-engines.md#growth-stages). |
| `verbose` | Print progress while growing. |
| `**settings` | Changes to species values. See [Change settings](#change-settings). |

`cambium.species()` returns one `Species` per installed species, with `name`, `common_name`, `scientific_name`, `aliases`, `labels` (how many values are sourced, DERIVED, TUNED or VERIFY) and `file`.

## Open-grown or in a stand

- **Open** (`stand=False`, the default): one tree alone on open ground. It grows a wide crown and a thick stem.
- **Stand** (`stand=True`): the tree grows among neighbours, so it is taller for its diameter and has a narrow crown. The neighbours are copies of the tree itself, placed at random and each turned and scaled, so light arrives unevenly. Stem density follows a Swedish birch thinning programme keyed to top height.

A stand tree is much smaller than an open-grown tree of the same age, so it grows faster and needs less memory.

For a forest of separate trees, each with its own seed, use [`cambium.forest`](forests.md) instead.

## Read the results

| Property | Meaning |
|---|---|
| `tree.age` | Years grown |
| `tree.height_m` | Height, m |
| `tree.dbh_cm` | Stem diameter at 1.3 m, cm; `None` while the tree is shorter than 1.3 m |
| `tree.crown_width_m` | Crown width, m: the mean of the widths along x and y |
| `tree.stats` | One record (a dict) per year, from year 0 to `tree.age` |

Each record in `tree.stats` holds, among others:

| Key | Meaning |
|---|---|
| `year` | The year of the record |
| `height_m`, `dbh_cm`, `crown_width_m` | As above |
| `crown_base_height_m`, `crown_ratio`, `lowest_live_branch_m` | Where the crown starts, and the share of the height that is crown |
| `leaves`, `leaf_area_m2` | Leaves and their area |
| `lai` | Leaf area index. In a stand: leaf area times stems per hectare. In the open: leaf area over the crown's projected area |
| `subcanopy_light_pct` | Stand runs only: light at 1-2 m under the canopy, % of full light |
| `water` | Water status, for example `psi_collar_mpa` (water potential at the stem base) and `stomatal_opening` |
| `carbon` | Carbon fixed and spent this year, in the model's resource units |
| `roots` | Root length, depth and spread, for example `root_max_depth_m` and `root_spread_max_m` |
| `scaffold` | Every 5 years and every year from age 50: limbs over 5 and 10 cm, limb-to-trunk ratios, leaf area by height and by distance from the trunk |

`tree.stats[-1]` is the last year.

!!! note "Wood, not bark"
    The model grows wood and no bark, so `dbh_cm` is the diameter of the wood. Published diameters are usually over bark, which is thicker. Forest tree lists give diameters over bark (see [Forests](forests.md)).

## Save the results

```python
tree.stats.to_csv("growth.csv")    # one row a year
tree.stats.to_json("growth.json")  # the records as the engine made them
text = tree.stats.to_csv()         # without a path, you get the text back
tree.save("out/birch7")            # writes stats.json and stats.csv
```

`tree.to_csv(...)` and `tree.to_json(...)` do the same as the `tree.stats` versions.

In CSV, nested values become dotted columns, such as `water.psi_collar_mpa`. Lists are written as JSON text. A year with no value for a column gets an empty cell.

`tree.save(folder)` writes `stats.json` and `stats.csv`. `stats.json` also holds the published reference heights for the tree's age and its anchorage numbers: the critical turning moment, root-plate overturning resistance and breaking force per main root.

## Change settings

Any value in the species file can be changed for one run, by its dotted path:

```python
tree = cambium.grow(seed=1, years=30, **{"resource.alpha": 4.5})
tree = cambium.grow(seed=1, years=30, resource__alpha=4.5)   # the same: __ for each dot
```

On the command line, use `--set KEY=JSON`, once for each value:

```
cambium grow --species birch --seed 1 --years 30 --set resource.alpha=4.5
```

!!! warning
    A changed value gives a different tree, not the published birch. Some values have to move together. For example, `light.leaf_area_m2`, `shoot.internode_length` and `resource.alpha` are linked: a bigger leaf with the same `alpha` gives a seedling that never grows, with no error. See [Species and sources](species.md).

## Command line

```
cambium --version
cambium species
cambium grow --species birch --seed 7 --years 60 [--forest] [--environment NAME]
             [--set KEY=JSON ...] [--export glb|usd] [--lod lod0,lod1]
             [--seasons summer,autumn] [--out DIR] [--quiet]
```

- `--forest` (or `--stand`) grows the tree among neighbours instead of in the open.
- `--export glb` or `--export usd` writes meshes as well. `--lod` and `--seasons` choose what the export writes; see [Use in game engines](game-engines.md).
- `cambium grow` writes `DIR/stats.json` and `DIR/stats.csv`, plus the export. Without `--out`, `DIR` is `cambium_out/<species>_seed<seed>_<open|stand>`, for example `cambium_out/betula_pendula_seed7_open`.
- `--quiet` prints less.

`cambium species` lists the installed species, their aliases and their label counts. `cambium forest` and `cambium export` are on the [Forests](forests.md) and [game engines](game-engines.md) pages.

## Research meshes (USD)

```python
tree.export("out/birch7_usd", format="usd")
```

This writes the full research meshes:

- `tree.usdc`, Z-up, in metres: `/Tree/Living`, `/Tree/Roots` and `/Tree/PrunedHistory` (hidden; the branches the tree has shed). The parts sit in `tree_parts/` and load as payloads.
- `tree_reduced.usdc`: twigs under a radius threshold dropped, under 10 % of the triangles. At 60 years the threshold is about 1 cm radius, so a reduced tree has no fine twigs at all.
- Untextured `.glb` copies: `tree.glb`, `tree_roots.glb`, `tree_pruned.glb`, `tree_reduced.glb`, `tree_reduced_roots.glb`.

Every vertex carries `birth_year`, `death_year`, `branch_order`, `radius` and `node_id`. Root vertices also carry `depth_below_ground`. The `Roots` prim carries the anchorage numbers. Crown and roots share the ring of the stem at the ground line, so together they are one surface.

`lod="lod0"` is the full detail and `lod="lod1"` the reduced one. Both are always written.

For textured meshes with levels of detail, use `format="glb"`: see [Use in game engines](game-engines.md).

## The research command

A source checkout also has `python cli.py`, the research command:

```
python cli.py --species betula_pendula --seed 1 --years 60           # open-grown
python cli.py --species betula_pendula --seed 1 --years 60 --stand   # in a stand
```

It writes everything to `out/<seed>/` (or `out/<seed>_stand/`): the meshes above, `stats.json`, `manifest.json` (file sizes, triangle counts, run time and peak memory), `previews/` (silhouettes, shaded views, roots), and the full growth history in `timeline.json` and `timeline.npz`. The history holds every node's parent, birth and death year, order and position, its radius over time, and the width of each annual ring for wood over 1 cm thick.

It grows the same tree: `cambium.grow(seed=s, years=y)` gives exactly the statistics of `python cli.py --seed s --years y`.
