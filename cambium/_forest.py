"""A forest plot: many trees sharing one light field and one soil, from a dense natural start.

``forest()`` runs what ``python tools/forest.py run`` runs: the same settings, the same plot, the same
years, so the same seed gives the same stand.  Its trees are lean: they keep what growth reads back and
what the stand's measures need, so thousands can come and go, but none can be exported as a mesh.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import _engine
from ._species import species_file
from ._stats import Stats
from ._tree import _manifest, settings_items

__all__ = ["Forest", "forest"]


def plot_settings(area_m2: float, stems_per_ha: float, mortality: bool, spread: bool, extra: list) -> list:
    """The values a forest run changes, in the order tools/forest.py's settings() lists them."""
    out = ["plot.stand_measures=true", "plot.natural_start.enabled=true", f"plot.natural_start.stems_per_ha={float(stems_per_ha)}"]
    if mortality:
        out.append("mortality.enabled=true")
    out.append(f"plot.natural_start.area_m2={float(area_m2)}")
    if spread:
        out.append("regeneration.spread.enabled=true")
    return out + list(extra)


class Forest:
    """A grown plot.  ``stats``: one record per year for the stand.  ``trees``: the trees standing at
    the end, and those that died in the last 10 years, with positions in metres from the plot's
    centre (the plot repeats at its edges, so a list tiles).  ``tree_lists``: the same list for the
    years asked for.  ``plot`` is the engine's own ``treegen.plot.Plot``."""

    def __init__(self, plot, final: dict, tree_lists: dict, *, species_file: Path, environment_file: Path, seed: int,
                 settings: list, runtime_s: float):
        self.plot = plot
        self.species_file = Path(species_file)
        self.environment_file = Path(environment_file)
        self.seed = int(seed)
        self.settings = list(settings)
        self.trees = final["trees"]
        self.tree_lists = tree_lists
        self.side_x_m, self.side_y_m = final["side_x_m"], final["side_y_m"]
        self.runtime_s = runtime_s
        self._stats = Stats(plot.stats)

    @property
    def species(self) -> str:
        return self.species_file.stem

    @property
    def year(self) -> int:
        return int(self.plot.year)

    @property
    def area_m2(self) -> float:
        return float(self.plot.area)

    @property
    def stats(self) -> Stats:
        return self._stats

    def to_csv(self, path: str | Path | None = None) -> str:
        return self._stats.to_csv(path)

    def to_json(self, path: str | Path | None = None) -> str:
        return self._stats.to_json(path)

    def __repr__(self) -> str:
        s = self._stats[-1] if self._stats else {}
        return (f"<Forest {self.species} seed {self.seed}: year {self.year}, {self.area_m2:.0f} m2, "
                f"{s.get('stems_per_ha', 0)} stems/ha, top height {s.get('top_height_m', '-')} m>")

    def save(self, folder: str | Path) -> list:
        """forest.json (the plot, its settings, the yearly stand records and the tree lists), stats.csv
        and trees.csv.  Returns the paths."""
        out = Path(folder)
        out.mkdir(parents=True, exist_ok=True)
        params = self.plot.species
        doc = {"format": "cambium.forest/1", "species": params.species.scientific_name, "species_file": self.species,
               "environment": self.environment_file.stem, "seed": self.seed, "mode": self.plot.mode, "year": self.year,
               "area_m2": self.area_m2, "side_m": self.side_x_m, "side_y_m": self.side_y_m,
               "run_manifest": _manifest(self.species_file, self.environment_file, params, self.settings),
               "runtime_s": round(self.runtime_s), "stats": list(self._stats), "trees": self.trees,
               "tree_lists": {str(y): t for y, t in self.tree_lists.items()}}
        if getattr(self.plot, "damage_log", None):
            doc["damage_log"] = self.plot.damage_log
        (out / "forest.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
        self.to_csv(out / "stats.csv")
        Stats(self.trees).to_csv(out / "trees.csv")
        return [out / "forest.json", out / "stats.csv", out / "trees.csv"]


def forest(species: str = "betula_pendula", seed: int = 1, years: int = 60, environment: str = "sweden_open_field", *,
           area_m2: float = 1000.0, stems_per_ha: float = 16000.0, mortality: bool = True, spread: bool = False,
           regeneration: bool = False, tree_list_years=(), verbose: bool = False, **settings) -> Forest:
    """Grow a forest plot from a natural start and return it.

    area_m2: a square plot of this much ground.  stems_per_ha: the density the first trees start at.
    mortality: deaths that answer to crowding and vigour, as well as carbon starvation.
    spread: regeneration that spreads (seed, light, open ground); regeneration: the plain regeneration.
    tree_list_years: years at which to keep a list of every tree (``Forest.tree_lists``).
    settings: species values to change from the start, by dotted path, as in ``grow()``.
    """
    return _forest(species, seed, years, environment, area_m2, stems_per_ha, mortality, spread, regeneration,
                   tree_list_years, verbose, settings_items(settings))


def _forest(species, seed, years, environment, area_m2, stems_per_ha, mortality, spread, regeneration, tree_list_years,
            verbose, extra: list) -> Forest:
    import treegen  # noqa: F401  (first: one maths thread)
    from treegen import checkpoint
    from treegen.environment import make_environment, make_soil
    from treegen.params import load_environment, load_species
    from treegen.plot import Plot

    sp_file = species_file(species)
    env_file = _engine.environment_file(environment)
    seed, years = int(seed), int(years)
    if years < 1:
        raise ValueError("years must be at least 1")
    items = plot_settings(area_m2, stems_per_ha, mortality, spread, extra)
    sp, _ = load_species(str(sp_file))
    checkpoint.set_values(sp, items)
    env_p, _ = load_environment(str(env_file))
    t0 = time.time()
    plot = Plot(sp, make_environment(env_p), lambda: make_soil(env_p), seed=seed, mode="natural", lean=True)
    if spread or regeneration:
        plot.enable_regeneration()
    tl = _engine.load("tree_list")
    run = {"overrides": items, "environment": env_file.stem}
    wanted = {int(y) for y in tree_list_years}
    lists = {}
    while plot.year < years and plot.alive:
        plot.step()
        if plot.year in wanted:
            lists[plot.year] = tl.tree_list(plot, run=run)["trees"]
        if verbose and (plot.year % 5 == 0 or plot.year == years):
            s = plot.stats[-1]
            print(f"year {plot.year}: {s.get('stems_per_ha')}/ha, basal area {s.get('basal_area_ob_m2_ha')} m2/ha, "
                  f"top height {s.get('top_height_m')} m, {time.time() - t0:.0f} s", flush=True)
    return Forest(plot, tl.tree_list(plot, run=run), lists, species_file=sp_file, environment_file=env_file, seed=seed,
                  settings=items, runtime_s=time.time() - t0)
