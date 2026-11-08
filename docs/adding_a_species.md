# Adding a species

A species is data: a file of values, a file saying where each value came from, and a file of what the tree must measure up to. No model code is written for it, within the limits at the end.

## The three files

For a species called `quercus_robur`:

| File | What it holds |
|---|---|
| `species/quercus_robur.yaml` | Its values |
| `reference/quercus_robur/labels.yaml` | Where each value came from |
| `reference/quercus_robur/targets.yaml` | Published measurements the grown tree is scored against |

Birch's targets stay in `reference/targets.yaml`, and `reference/betula_pendula/accuracy.yaml` points to them.

## The steps

1. **Copy the template.** `species/_template.yaml` to `species/quercus_robur.yaml`. It lists every value, what it means, its unit and a sensible range, with birch's value as a starting point. Give the species its name at the top.

2. **Start the labels.** This marks every value as unchecked:
   ```
   python tools/species_report.py --species quercus_robur --init-labels
   ```

3. **Replace values, and label each one you replace,** in `labels.yaml`:
   ```yaml
   light.extinction_coefficient: {status: sourced, value: 0.5, source: "Author 2010, Table 3", checked: page}
   resource.alpha: {status: TUNED, value: 5.2, against: "height at age 30, 8 seeds"}
   shoot.internode_length: {status: VERIFY, value: 0.03, note: "from a related species"}
   ```
   | Label | Means | Must say |
   |---|---|---|
   | `sourced` | A published source gives it for this species | `source`; add `checked: page` once someone has read the page and it supports the value |
   | `DERIVED` | Worked out from a source with a stated step: a mean, a ratio, a conversion, a reading of a figure | `source`, with the step |
   | `TUNED` | No direct source; it was set to make the tree match something | `against`: what it was tuned to match |
   | `VERIFY` | Neither yet: a guess, or borrowed from elsewhere | A `note`, if there's something to say |

   If you tune a value later, you can write `# TUNED against ...` above it in the species file instead. That comes first. If a value changes and its label doesn't, the report counts it as unchecked.

   **Three values have to move together:** `light.leaf_area_m2`, `shoot.internode_length` and `resource.alpha`. One model node carries one leaf, and `alpha` is the carbon of one leaf. Birch's file with leaves 4 times the size and nothing else changed gives a seedling that never grows, with no error (0 m and 3 leaves at age 10, 3 seeds). With `alpha` 4 times as large as well, it grows. Tune `alpha` again whenever you change either of the others.

4. **Write the targets.** Same form as `reference/targets.yaml`. A target with a name the scorecard knows, such as `tree_allometry.site_index_curves`, is scored by it. For anything else, name a saved value and a range:
   ```yaml
   growth:
     height_at_age:
       metric: height_m
       target_range: [18.0, 24.0]
       source: "Author 2010, Table 2"
       conditions:
         scenario: [stand-tree]
         age_years: [50, 60]
   ```
   Any key of a year's record in `stats.json` or `plot.json` can be a metric. A target can't be loosened once approved: tag it `targets-approved-quercus_robur` when approved, and the report reads it from there. Until then, the report says "targets not approved".

5. **Check it.** Fix anything marked ERROR:
   ```
   python tools/species_report.py --species quercus_robur
   ```

6. **Grow it.** Start small, and check that it's more than a few leaves at age 10. Then use several seeds, because one seed proves nothing:
   ```
   python cli.py --species quercus_robur --seed 1 --years 10 --stand --no-preview
   python tools/ensemble.py trees --label oak_1 --seeds 8 --species quercus_robur
   ```

7. **Read its accuracy:**
   ```
   python tools/species_report.py --species quercus_robur --ensemble out/bench/ensemble/oak_1
   ```
   The last line is the species' accuracy in a sentence. For birch, today:
   > `betula_pendula: 0 of 3 scored targets pass at ages 50 and 60, over 20 runs; 0 of 6 age checks pass; 78 of 296 values sourced, 23 tuned, 195 unchecked.`

## Blocks a species can leave out

`leader_damage`, `damage`, `germination`, `field_layer_competition`, `soil_water_balance` can go if they don't apply. `plot` and `regeneration` can go if the species won't be grown in plots. Everything else is required, and the check says which values are missing.

The `damage` block's numbers for wind are from a study of birch. A new species needs its own, or `damage.enabled: false`.

## Limits: what data can't change yet

These are written into the model, so a species that differs here needs code first:

- **Leaves fall every year.** Evergreen species can't be made: every node's leaves are rebuilt each season.
- **One side bud per node.** Opposite or whorled branching (ash, maple, pine) can't be made.
- **Bark colour and leaf look** are written for birch in `treegen/preview.py` and `treegen/export.py`.
- **Over-bark diameter and stem taper** in the scorecard's crown target use birch's equations, in `tools/bark.py`.
- **Climate lives in the species file:** the rain and evaporation in `soil_water_balance`, and storm direction in `damage.wind`. They belong to the site, and should move to `environments/`.
- **Height curves:** `reference.height` and the scorecard expect the Hossfeld IV form.

## Keeping the template current

When a setting is added to `treegen/species_schema.py`, rewrite the template:
```
python tools/species_report.py --write-template
```
