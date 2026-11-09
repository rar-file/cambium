# Species and sources

A species is data, not code. Three files describe it:

| File | What it holds |
|---|---|
| `species/<name>.yaml` | Every value the model reads, each with a comment on where it came from |
| `reference/<name>/labels.yaml` | A label for each value: where it came from, in a form the tools can check |
| `reference/<name>/targets.yaml` | Published measurements the grown tree is scored against (birch's are in `reference/targets.yaml`) |

Today there is one species: silver birch, `betula_pendula` (aliases `birch` and `silver_birch`).

## The four labels

Every value carries one of four labels.

| Label | Means | Must say |
|---|---|---|
| `sourced` | A source gives it for this species | The source. `checked: page` once someone has read the page and it supports the value |
| `DERIVED` | Worked out from a source with a stated step: a mean, a ratio, a conversion, a reading of a figure | The source, with the step |
| `TUNED` | No direct source. It was set to make the tree match a stated target | `against`: what it was tuned against |
| `VERIFY` | Neither yet: estimated, borrowed from elsewhere, or unchecked | A note, if there is something to say |

A TUNED value that doesn't say what it was tuned against is an error, and so is a sourced or DERIVED value with no source. If a value in the species file changes and its label doesn't, the value counts as unchecked until someone looks.

Three real lines from birch's `labels.yaml`:

```yaml
light.extinction_coefficient: {status: sourced, value: 0.37, source: 'Hagemeier & Leuschner 2019, Forests 10:925, Table 5: K_PAR 0.37, B. pendula', checked: page}
resource.maintenance_per_internode: {status: TUNED, value: 0.5, against: whole-tree carbon use efficiency about 0.47 (Waring 1998); natural plot 0.42 from age 20}
shoot.internode_length: {status: VERIFY, value: 0.025, note: 'borrowed: US plant patent PP15768'}
```

## Birch today

| Label | Values |
|---|---|
| sourced | 92 |
| DERIVED | 21 |
| TUNED | 54 |
| VERIFY | 213 |
| **Total** | **380** |

Most values are still VERIFY. Checking them against sources is open work, and help is welcome: see [Contributing](contributing.md).

The look of the tree (bark colour, leaf colour, textures: the `appearance` block) has labels of its own. Most of its values are TUNED, about half of those by eye on renders, and most of the look is not checked against data.

To see the counts yourself:

```python
import cambium
for s in cambium.species():
    print(s.name, s.labels)
```

or `cambium species` on the command line.

## Targets are never loosened

A target is a published measurement with a range, such as light under the canopy or height at an age. Once a target is approved, it is not loosened to make a run pass. The scoring tool reads the targets at a git tag (`targets-approved` for birch), with no fallback to the working copy, so a target can't change quietly. [How real is it](how-real.md) shows how birch scores.

## Adding a species

This needs a source checkout (see [Install](install.md#from-a-source-checkout)). Open a "New species or source" issue first, so the work can be agreed before you start.

1. **Copy the template.** Copy `species/_template.yaml` to `species/<name>.yaml`. It lists every value with its meaning, unit and a sensible range, and birch's value as a starting point.
2. **Start the labels.** This marks every value as unchecked:
   ```
   python tools/species_report.py --species <name> --init-labels
   ```
3. **Replace values, and label each one you replace,** in `reference/<name>/labels.yaml`, in the form shown above.
4. **Write the targets** in `reference/<name>/targets.yaml`, in the same form as `reference/targets.yaml`. Any key of a year's record can be a metric.
5. **Check it,** and fix anything marked ERROR:
   ```
   python tools/species_report.py --species <name>
   ```
6. **Grow it.** Start small, and check that it is more than a few leaves at age 10. Then grow several seeds: one seed proves nothing.
   ```
   cambium grow --species <name> --seed 1 --years 10 --forest
   ```

Once it is set up you can also grow it from Python by path: `cambium.grow(species="path/to/<name>.yaml")`.

!!! warning "Three values move together"
    `light.leaf_area_m2`, `shoot.internode_length` and `resource.alpha` are linked. One model node carries one leaf, and `alpha` is the carbon of one leaf. Birch with leaves 4 times the size and nothing else changed gives a seedling that never grows, with no error. Tune `alpha` again whenever you change either of the others.

The full guide is `docs/adding_a_species.md` in the repository.

### What data can't change yet

These are written into the model, so a species that differs here needs code first:

- **Leaves fall every year.** Evergreen species can't be made yet.
- **One side bud per node.** Opposite or whorled branching (ash, maple, pine) can't be made yet.
- **Bark colour and leaf look** are written for birch.
- **Over-bark diameter and stem taper** in the scoring use birch's equations.
- **Climate lives in the species file** (rain, evaporation, storm direction). It belongs to the site and should move to the environment file.
- **Height curves** are expected in the Hossfeld IV form.
- **A forest holds one species.**

## Citing sources

Cite each source so others can open it: a publisher page, a PubMed Central (PMC) page, or the author's repository. Say where in the source the value is (table, figure, page). For a DERIVED value, give the step.
