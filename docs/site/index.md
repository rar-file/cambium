# Cambium

<img src="assets/logo.svg" alt="" width="96">

Cambium grows silver birch (*Betula pendula*), crown and roots, one year at a time. Each year the tree gets light, water and carbon, and those decide where it grows. The model follows the self-organising tree model of Palubicki et al. (2009) and adds water transport, roots and mechanics.

You get:

- **Yearly statistics** for each tree: height, stem diameter, crown, leaves, water, carbon, roots. You can save them as CSV or JSON.
- **Meshes for game engines**: glTF (`.glb`) files with textures, three levels of detail, several ages of one tree, and five seasons.
- **Research meshes**: USD files where every vertex records its birth year, death year, branch order, radius and node id.
- **Forests**: many trees that share one light field and one soil, and that thin themselves as they grow.

Every value in the species file says where it came from: a source, a worked step from a source, a tuning target, or "not checked yet". See [Species and sources](species.md).

## Version 0.9

At ages 50 and 60, the birch matches the targets it was tuned against: light under the canopy and leaf area. Height follows a published growth curve by design. Young trees are still wrong: their crowns reach almost to the ground and they grow too few roots. Version 1.0 is planned to fix young trees. [How real is it](how-real.md) gives the numbers.

## Quick start

```
pip install pycambium
cambium grow --species birch --seed 1 --years 25
```

This grows one birch for 25 years in the open. It writes `stats.json` and `stats.csv` to `cambium_out/betula_pendula_seed1_open/`.

The same in Python:

```python
import cambium

tree = cambium.grow(species="birch", seed=1, years=25)
print(tree.height_m, tree.dbh_cm, tree.crown_width_m)
tree.save("out/birch1")
```

The same seed always gives the same tree. A 25-year tree takes seconds to a minute. A 60-year open-grown birch is much bigger: it has well over a million leaves, takes several minutes and needs a few GB of memory.

## Pages

- [Install](install.md): Python versions, a source checkout, reproducible results.
- [Grow a tree](grow.md): the Python API and the command line, statistics, settings, outputs.
- [Forests](forests.md): many trees on one plot, and what the stand statistics mean.
- [Use in game engines](game-engines.md): levels of detail, growth stages, seasons, materials, Unreal.
- [Species and sources](species.md): how each value is labelled, and how to add a species.
- [How real is it](how-real.md): what has been checked, what passes and what is wrong.
- [How it works](how-it-works.md): the yearly cycle, in brief.
- [Contributing](contributing.md): issues, pull requests, tests.
- [3D viewer](viewer.md): coming soon.

## Licence

Apache-2.0. Source code: [github.com/rar-file/cambium](https://github.com/rar-file/cambium).
