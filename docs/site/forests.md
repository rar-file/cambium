# Forests

A forest is a plot of separate trees. Each tree is its own simulation, with its own seed, germination year and growth vigour. All trees share one light field and one soil, so they shade each other and compete for water. The plot repeats at its edges, so it has no edge trees.

The plot is left to itself: nobody thins it. Trees die of crowding, suppression, background causes, old age or lack of carbon, and of damage such as wind and snow.

## In Python

```python
import cambium

forest = cambium.forest(species="betula_pendula", seed=1, years=60)
last = forest.stats[-1]
print(last["stems_per_ha"], last["basal_area_ob_m2_ha"], last["top_height_m"])
forest.save("out/forest1")
```

All arguments, with their defaults:

```python
cambium.forest(species="betula_pendula", seed=1, years=60, environment="sweden_open_field",
               area_m2=1000.0, stems_per_ha=16000.0, mortality=True, spread=False,
               regeneration=False, tree_list_years=(), verbose=False, **settings)
```

| Argument | Meaning |
|---|---|
| `area_m2` | Size of the square plot, m² |
| `stems_per_ha` | Stems per hectare at the start |
| `mortality` | Self-thinning, suppression, background and old-age mortality. With `False`, trees still die when their carbon no longer pays the upkeep of their living wood, and of damage |
| `spread` | Regeneration that spreads: seed rain, light and open ground decide where new trees come up |
| `regeneration` | Plain regeneration: new trees come up from seed |
| `tree_list_years` | Years at which to keep a list of every tree, for example `(20, 40, 60)` |
| `**settings` | Changes to species values, as for [`cambium.grow`](grow.md#change-settings) |

## What you get

- `forest.stats`: one record (a dict) per year for the whole stand. See the table below.
- `forest.trees`: the trees alive at the end, plus those that died in the last 10 years.
- `forest.tree_lists`: `{year: [trees]}` for the years in `tree_list_years`.
- `forest.save(folder)`: writes `forest.json`, `stats.csv` and `trees.csv`.

Each tree in `forest.trees` and `forest.tree_lists` has:

| Field | Meaning |
|---|---|
| `id` | The tree's number in the plot |
| `x_m`, `y_m` | Position in metres from the plot's centre. The plot repeats at its edges, so a list tiles |
| `species` | Scientific name |
| `age_years` | Age |
| `height_m` | Height, m |
| `dbh_cm` | Stem diameter at 1.3 m, over bark, cm; empty below 1.3 m |
| `crown_base_m` | Height where the crown starts, m |
| `crown_width_m` | Crown width, m: the mean of the widths along x and y |
| `alive` | `True`, or `False` for a tree that died. A dead tree also has `died_year` and `cause`, and is given as it was in its last year. The model has no standing dead wood or fallen trunks |

Forest trees keep only what growth needs, so they can't be exported as meshes. To get meshes, grow single trees with [`cambium.grow`](grow.md).

## Command line

```
cambium forest --species birch --seed 1 --years 60 [--area 1000] [--stems 16000]
               [--no-mortality] [--spread] [--regeneration] [--tree-lists 20,40,60]
               [--set KEY=JSON ...] [--out DIR] [--quiet]
```

The options match the Python arguments above.

## What the stand statistics mean

| Key | Meaning |
|---|---|
| `year` | Years since the stand began |
| `trees`, `stems_per_ha` | Living trees on the plot, and per hectare. Seedlings count |
| `stems_bh_per_ha` | Stems per hectare taller than 1.3 m, as a forester counts them |
| `basal_area_ob_m2_ha` | Basal area over bark, m² per hectare: the cross-section of all stems at 1.3 m |
| `dg_ob_cm` | Quadratic mean diameter over bark, cm, of the stems past 1.3 m |
| `top_height_m` | Mean height of the 100 thickest stems per hectare |
| `dbh_mean_cm`, `dbh_sd_cm`, `dbh_min_cm`, `dbh_max_cm` | Stem diameters of the living trees, wood only (the model grows no bark) |
| `height_mean_m`, `height_max_m` | Heights of the living trees |
| `lai` | Leaf area index: all leaf area over the plot's area |
| `subcanopy_light_pct` | Light at 1-2 m under the canopy, % of full light |
| `subcanopy_diffuse_light_pct` | The same under the overcast sky alone. This is how the light target is measured |
| `gap_fraction` | Share of the ground with no leaf above 2 m directly over it (canopy gaps) |
| `relative_density` | How crowded the stand is: Reineke's stand density index over its maximum, averaged over the trees' neighbourhoods. Self-thinning starts above 0.7 |
| `stopped_share` | Share of stems that have all but stopped laying wood (rings under 0.1 mm a year) |
| `died_total` | Trees that have died since the start |
| `dead_this_year` | Deaths this year by cause, for example `self-thinned`, `suppressed` or `old age` |
| `basal_area_lost_m2_ha` | Basal area lost to deaths this year |
| `new_trees` | New trees that came up this year (with regeneration on) |

With regeneration on, records also carry `recruits_alive` and the year's seed rain.

## How long it takes

A forest is many trees, so it takes much longer than one tree. Start with a short run, such as `--years 20`, before a 60-year one. See [How real is it](how-real.md) for how the forests compare with real stands.
