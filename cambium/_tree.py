"""One tree: grow it, read its yearly records, export it.

``grow()`` runs the same steps as ``python cli.py`` (``cli.grow``), so the same seed and settings give
the same tree, bit for bit, on the same machine and library versions; another machine grows another
tree from that seed (treegen/threads.py).  Exports go through the same code as ``cli.py`` (USD) and
``tools/game_export.py`` (glTF for game engines).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import _engine
from ._species import species_file
from ._stats import Stats

__all__ = ["Tree", "grow"]

FORMATS = ("glb", "usd")
SEASONS = ("spring", "summer", "early_autumn", "autumn", "winter")
USD_LEVELS = {"lod0": "tree.usdc", "lod1": "tree_reduced.usdc"}   # full detail; under 10 % of its triangles


def settings_items(settings: dict) -> list:
    """Keyword settings as the engine's "dotted.key=JSON" items.  A key may use "__" for ".", so
    ``resource__alpha=4.5`` is ``resource.alpha=4.5``."""
    return [f"{key.replace('__', '.')}={json.dumps(value)}" for key, value in settings.items()]


def _levels(lod, known: list) -> list:
    if lod is None:
        return list(known)
    want = [x.strip() for x in lod.split(",")] if isinstance(lod, str) else [str(x) for x in lod]
    bad = [x for x in want if x not in known]
    if bad or not want:
        raise ValueError(f"unknown level {bad or lod!r}; this export has {', '.join(known)}")
    return [x for x in known if x in want]


def _manifest(sp_file: Path, env_file: Path, params, items: list) -> dict:
    """What a tree was made from: Cambium's version, the species and environment files with their
    SHA-256, the settings, and every option switched on.  In a source checkout, also the engine's own
    run manifest (git commit, uncommitted changes, machine, maths threads)."""
    from treegen.params import option_values, run_manifest

    from . import __version__

    m = {"cambium_version": __version__, "species_file": sp_file.name, "species_sha256": _engine.sha256(sp_file),
         "environment_file": env_file.name, "environment_sha256": _engine.sha256(env_file), "settings": list(items),
         "options_on": sorted(k if v is True else f"{k}={v}" for k, v in option_values(params).items() if v not in (False, 0))}
    if _engine.SOURCE:
        m.update(run_manifest(sp_file, env_file, params)[0])
    return m


class Tree:
    """A grown tree.  ``stats`` holds one record per year, from year 0 to ``age``.

    ``model`` (a ``treegen.growth.GrowthModel``) and ``params`` (the species values used, settings
    applied) are the engine's own objects, there for those who need more than this class gives."""

    def __init__(self, model, params, *, species_file: Path, environment_file: Path, seed: int, stand: bool,
                 settings: list, snapshots: dict | None = None):
        self.model = model
        self.params = params
        self.species_file = Path(species_file)
        self.environment_file = Path(environment_file)
        self.seed = int(seed)
        self.stand = bool(stand)
        self.settings = list(settings)
        self._snapshots = dict(snapshots or {})
        self._stats = Stats(model.stats)

    # -- what it is ----------------------------------------------------------------------------
    @property
    def species(self) -> str:
        return self.species_file.stem

    @property
    def environment(self) -> str:
        return self.environment_file.stem

    @property
    def age(self) -> int:
        return int(self.model.year)

    @property
    def height_m(self) -> float:
        return self._stats[-1]["height_m"]

    @property
    def dbh_cm(self) -> float | None:
        """Diameter at 1.3 m, under bark; None while the tree is shorter than that."""
        return self._stats[-1]["dbh_cm"]

    @property
    def crown_width_m(self) -> float:
        return self._stats[-1]["crown_width_m"]

    @property
    def stats(self) -> Stats:
        return self._stats

    def to_csv(self, path: str | Path | None = None) -> str:
        return self._stats.to_csv(path)

    def to_json(self, path: str | Path | None = None) -> str:
        return self._stats.to_json(path)

    def __repr__(self) -> str:
        dbh = "-" if self.dbh_cm is None else f"{self.dbh_cm:.1f} cm"
        return (f"<Tree {self.species} seed {self.seed} {'stand' if self.stand else 'open'}: age {self.age}, "
                f"height {self.height_m:.2f} m, dbh {dbh}>")

    def metadata(self, generator: str = "") -> dict:
        from . import __version__

        return {"species": self.params.species.scientific_name, "species_file": self.species, "environment": self.environment,
                "mode": "stand" if self.stand else "open", "seed": self.seed,
                "generator": generator or f"cambium {__version__} (treegen engine: Palubicki et al. 2009 self-organising model, roots, hydraulics)",
                "run_manifest": _manifest(self.species_file, self.environment_file, self.params, self.settings)}

    # -- files ---------------------------------------------------------------------------------
    def save(self, folder: str | Path) -> list:
        """stats.json (as ``cli.py`` writes it: the yearly records, published reference heights and
        crown widths, anchorage) and stats.csv.  Returns the paths."""
        from treegen import export
        from treegen.reference import reference_block

        out = Path(folder)
        out.mkdir(parents=True, exist_ok=True)
        cli = _engine.load("cli")
        export.write_stats(out / "stats.json", self.model, self.metadata(), reference_block(self.params, self.model.stats),
                           cli.anchorage_numbers(self.model, self.params))
        self.to_csv(out / "stats.csv")
        return [out / "stats.json", out / "stats.csv"]

    def export(self, path: str | Path, format: str = "glb", lod=None, ages=None, seasons=("summer",), look: dict | None = None,
               log=None, textures: bool = True, timelapse: bool = False) -> list:
        """Write the tree's meshes into the folder ``path``; returns the files written.

        format="glb": glTF 2.0 for game engines, with PBR textures, one file per age, season and level of detail
        (``betula_pendula_age060_summer_lod0.glb``), and game_manifest.json.  The levels come from the
        species file: lod0 full detail, lod1 reduced (a triangle budget), lod2 far cards.  lod=None writes
        all; "lod1" or ["lod0", "lod1"] picks.  lod2 is drawn from lod0's file, so lod0 comes with it.
        ages: default the tree's age; an earlier age needs ``grow(..., stages=[...])``.  seasons: any of
        spring, summer, early_autumn, autumn, winter.  look: appearance values to change for this
        export only, by dotted path (``{"bark.tile_px": 256}``).  textures=False is a quick look at the
        geometry: the same meshes with no textures in the files, and no far level (it is nothing but one).
        Leaves are new each spring: a leaf hangs, rolls and turns colour in its own way that year.  timelapse=True
        is for a film of one frame a year: every leaf then hangs as it did the year before, because new leaves
        in every frame read as shimmer.

        format="usd": the research meshes ``cli.py`` writes: tree.usdc (lod0, full detail; parts in
        tree_parts/) and tree_reduced.usdc (lod1, under 10 % of its triangles), Z-up, with roots, shed
        branches and per-vertex birth year, order, radius and node id; plus the same meshes as plain
        .glb files.  Both levels are always written; ``lod`` picks which are returned.
        """
        fmt = str(format).lower().lstrip(".")
        if fmt not in FORMATS:
            raise ValueError(f"format must be one of {', '.join(FORMATS)}, not {format!r}")
        if self.model.lean:
            raise ValueError("a lean tree keeps nothing an export reads")
        if timelapse and "leaves.each_year" in (look or {}):
            raise ValueError("timelapse sets leaves.each_year itself; leave it out of look")
        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)
        log = log or (lambda s: None)
        ages = [self.age] if ages is None else sorted({int(a) for a in ([ages] if isinstance(ages, int) else ages)})
        if fmt == "usd":
            if ages != [self.age]:
                raise ValueError("format='usd' writes the tree at its own age only")
            return self._export_usd(out, _levels(lod, list(USD_LEVELS)))
        return self._export_glb(out, lod, ages, seasons, look, log, textures, timelapse)

    def _export_usd(self, out: Path, levels: list) -> list:
        cli = _engine.load("cli")
        cli.export_all(self.model, self.params, out, self.metadata(), cli.anchorage_numbers(self.model, self.params),
                       [], 400_000, {}, {})
        return [out / USD_LEVELS[name] for name in levels]

    def _export_glb(self, out: Path, lod, ages: list, seasons, look_values: dict | None, log, textures: bool = True,
                    timelapse: bool = False) -> list:
        from treegen import appearance as ap
        from treegen import textures as tx
        from treegen.params import load_species

        from . import __version__

        ge = _engine.load("game_export")
        seasons = [seasons] if isinstance(seasons, str) else list(seasons)
        bad = [s for s in seasons if s not in SEASONS]
        if bad or not seasons:
            raise ValueError(f"seasons must be some of {', '.join(SEASONS)}, not {bad or seasons!r}")
        missing = [a for a in ages if a != self.age and a not in self._snapshots]
        if missing:
            raise ValueError(f"no leaves kept at age {missing}: grow the tree with stages={missing} to export those ages")
        # the final year's leaves are read now: between years, reading changes nothing
        snaps = {a: self._snapshots[a] if a in self._snapshots else ap.leaf_snapshot(self.model, a) for a in ages}

        look = ap.load_look(load_species(str(self.species_file))[1])
        for key, val in (look_values or {}).items():
            d, parts = look, key.split(".")
            for part in parts[:-1]:
                d = d[part]
            if parts[-1] not in d:
                raise KeyError(f"no such look value: {key}")
            d[parts[-1]] = val
        if timelapse:
            ap.timelapse_look(look)
        lods = [x for x in look["game"]["lods"] if textures or x["kind"] != "far"]
        want = _levels(lod, [x["name"] for x in lods])
        if any(x["kind"] == "far" and x["name"] in want for x in lods) and lods[0]["name"] not in want:
            want.insert(0, lods[0]["name"])     # far cards are drawn from the first level's file
        look["game"]["lods"] = [x for x in lods if x["name"] in want]

        meta = self.metadata(f"cambium {__version__} (treegen tools/game_export.py)")
        tiles = tx.make_tiles(look)
        kept = {}     # what is the same at every age: made once
        stages = [ge.export_stage(self.model, self.params, look, tiles, a, snaps[a], out, seasons, self.species, meta, log=log, kept=kept,
                                  textures=textures) for a in ages]
        doc = {"continuity": ge.continuity(out, stages, self.species, look) if textures else [], "format": "treegen.game/1", **meta,
               **({} if textures else ge.NO_TEXTURES),
               "units": {"length": "m", "up_axis": "Y (glTF)", "ground": "y = 0, stem base at the origin"},
               "levels": look["game"]["lods"], "stages": stages, "checks": ge.check_files(out, log=log), "needs": ge.ENGINE_NOTES}
        (out / "game_manifest.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
        files = [out / info["file"] for s in stages for per_level in s["seasons"].values() for info in per_level.values()]
        return files + [out / "game_manifest.json"]


def grow(species: str = "betula_pendula", seed: int = 1, years: int = 60, stand: bool = False,
         environment: str = "sweden_open_field", *, stages=(), verbose: bool = False, **settings) -> Tree:
    """Grow one tree, year by year, and return it.

    species: a species name ("betula_pendula"), an alias ("birch") or a path to a species .yaml file.
    seed: the tree's random seed; the same seed and settings give the same tree on the same machine and library versions.
    stand: grow among neighbours (shadow volumes around it), as in a forest, instead of in the open.
    stages: earlier ages to keep the leaves at, so ``export(ages=...)`` can write those ages too.
    settings: species values to change from the start, by dotted path:
        ``grow(seed=1, years=30, **{"resource.alpha": 4.5})`` or ``grow(seed=1, years=30, resource__alpha=4.5)``.
    """
    return _grow(species, seed, years, stand, environment, settings_items(settings), stages, verbose)


def _grow(species, seed, years, stand, environment, items: list, stages=(), verbose: bool = False) -> Tree:
    sp_file = species_file(species)
    env_file = _engine.environment_file(environment)
    seed, years = int(seed), int(years)
    if years < 1:
        raise ValueError("years must be at least 1")
    stages = sorted({int(a) for a in stages})
    if any(a < 1 or a > years for a in stages):
        raise ValueError(f"stages must be ages from 1 to {years}")
    snaps = {}
    if stages:
        # the same steps as cli.grow, reading the leaves between years (it changes nothing)
        ge = _engine.load("game_export")
        model, params, _, snaps = ge.grow_with_leaves(str(sp_file), seed, sorted(set(stages) | {years}), str(env_file),
                                                      bool(stand), list(items))
    else:
        cli = _engine.load("cli")
        model, params = cli.grow(str(sp_file), seed, years, str(env_file), stand=bool(stand), verbose=verbose,
                                 scenario=list(items))
    return Tree(model, params, species_file=sp_file, environment_file=env_file, seed=seed, stand=stand,
                settings=items, snapshots=snaps)
