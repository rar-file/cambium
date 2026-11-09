"""Cambium: a self-organising growth model of trees, crown and roots, year by year.

    import cambium
    tree = cambium.grow(species="birch", seed=7, years=60)
    tree.height_m, tree.dbh_cm, tree.stats[-1]
    tree.stats.to_csv("birch7.csv")
    tree.export("birch7", format="glb")
    plot = cambium.forest(seed=1, years=40, area_m2=1000)
    cambium.species()

Cambium is the public face of the ``treegen`` engine: it adds nothing to the model and changes
nothing in it.  The same seed and settings give the same tree as ``python cli.py`` in a checkout.

Importing it sets the maths libraries to one thread (``treegen.threads``), so a run gives the same
bits on every machine.
"""
import treegen as _treegen  # noqa: F401  (first: one maths thread, before numpy loads)

from ._forest import Forest, forest
from ._species import Species, species
from ._stats import Stats
from ._tree import Tree, grow

__version__ = "0.9.0"
__all__ = ["Forest", "Species", "Stats", "Tree", "__version__", "forest", "grow", "species"]
