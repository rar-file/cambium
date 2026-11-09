"""The ``cambium`` command.

    cambium grow --species birch --seed 7 --years 60 [--forest] [--export glb|usd] [--out DIR]
    cambium forest --species birch --seed 1 --years 60 --area 1000 [--out DIR]
    cambium export --species birch --seed 5 --ages 15,30,60 --out DIR
    cambium species
    cambium --version
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__

EXAMPLES = """examples:
  cambium grow --species birch --seed 7 --years 60                 # one open-grown birch: stats.json, stats.csv
  cambium grow --species birch --seed 7 --years 60 --forest        # the same tree's life among neighbours
  cambium grow --seed 7 --years 30 --export glb --out trees/b7     # game-ready .glb files, three levels of detail
  cambium export --seed 5 --ages 15,30,60 --seasons summer,autumn --out trees/b5   # growth stages
  cambium forest --seed 1 --years 40 --area 1000 --tree-lists 20,40 --out stands/f1
  cambium species
"""


def _ints(text: str) -> list:
    return [int(x) for x in str(text).split(",") if x.strip()]


def _words(text: str) -> list:
    return [x.strip() for x in str(text).split(",") if x.strip()]


def _common(p: argparse.ArgumentParser, seed: int = 1) -> None:
    p.add_argument("--species", default="betula_pendula", help="a species name, an alias (birch) or a .yaml file; see 'cambium species'")
    p.add_argument("--seed", type=int, default=seed, help="random seed: the same seed and settings give the same result, bit for bit")
    p.add_argument("--environment", default="sweden_open_field", help="an environment name or .yaml file")
    p.add_argument("--set", action="append", default=[], metavar="KEY=JSON",
                   help="change a species value from the start, e.g. --set resource.alpha=4.5 (repeatable)")
    p.add_argument("--out", default=None, help="output folder")
    p.add_argument("--quiet", action="store_true", help="print only the result")


def _stand(p: argparse.ArgumentParser) -> None:
    p.add_argument("--forest", "--stand", dest="stand", action="store_true",
                   help="grow the tree among neighbours, as in a forest, instead of in the open")


def _export_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--lod", default=None, help="levels of detail to write, e.g. lod0,lod1 (default: all)")
    p.add_argument("--seasons", default="summer", help="glb: any of spring,summer,early_autumn,autumn,winter")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="cambium", description="Cambium: a self-organising growth model of trees, crown and roots.",
                                 epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"cambium {__version__}")
    sub = ap.add_subparsers(dest="command", required=True, metavar="{grow,forest,export,species}")

    g = sub.add_parser("grow", help="grow one tree and write its yearly stats (and meshes with --export)")
    _common(g)
    g.add_argument("--years", type=int, default=60)
    _stand(g)
    g.add_argument("--export", choices=("glb", "usd"), default=None, help="also write the tree's meshes in this format")
    _export_options(g)

    f = sub.add_parser("forest", help="grow a forest plot from a dense natural start")
    _common(f)
    f.add_argument("--years", type=int, default=60)
    f.add_argument("--area", type=float, default=1000.0, help="a square plot of this many m2 (default 1000)")
    f.add_argument("--stems", type=float, default=16000.0, help="stems per hectare at the start (default 16000)")
    f.add_argument("--no-mortality", dest="mortality", action="store_false", help="trees die only when carbon runs out")
    f.add_argument("--spread", action="store_true", help="regeneration that spreads: seed, light, open ground")
    f.add_argument("--regeneration", action="store_true", help="the plain regeneration")
    f.add_argument("--tree-lists", default="", help="years at which to keep a list of every tree, e.g. 20,40,60")

    e = sub.add_parser("export", help="grow one tree and write it at several ages, as game-ready files")
    _common(e, seed=5)
    e.add_argument("--ages", default="15,30,60", help="ages to write, e.g. 15,30,60; the tree grows to the oldest")
    _stand(e)
    e.add_argument("--format", choices=("glb", "usd"), default="glb")
    _export_options(e)

    sub.add_parser("species", help="list the species, with where their values come from")
    return ap


def _say(quiet: bool):
    return (lambda s: None) if quiet else (lambda s: print(s, flush=True))


def _describe(tree) -> str:
    dbh = "-" if tree.dbh_cm is None else f"{tree.dbh_cm:.1f} cm"
    return f"age {tree.age}: height {tree.height_m:.2f} m, dbh {dbh}, crown {tree.crown_width_m:.2f} m"


def cmd_grow(a) -> int:
    from ._species import species_file
    from ._tree import _grow

    name = species_file(a.species).stem
    out = Path(a.out or Path("cambium_out") / f"{name}_seed{a.seed}_{'stand' if a.stand else 'open'}")
    say = _say(a.quiet)
    t0 = time.time()
    tree = _grow(a.species, a.seed, a.years, a.stand, a.environment, a.set, verbose=not a.quiet)
    files = tree.save(out)
    if a.export:
        say(f"exporting {a.export} ...")
        files += tree.export(out, format=a.export, lod=a.lod, seasons=_words(a.seasons), log=say)
    print(f"{_describe(tree)}; {time.time() - t0:.0f} s -> {out}")
    say(f"{len(files)} files: " + ", ".join(sorted({p.name for p in files})[:8]) + (" ..." if len(files) > 8 else ""))
    return 0


def cmd_export(a) -> int:
    from ._tree import _grow

    ages = sorted(set(_ints(a.ages)))
    if not ages or a.out is None:
        raise SystemExit("cambium export: give --ages and --out")
    say = _say(a.quiet)
    t0 = time.time()
    tree = _grow(a.species, a.seed, ages[-1], a.stand, a.environment, a.set, stages=ages[:-1])
    say(f"grown: {_describe(tree)}; {time.time() - t0:.0f} s")
    if a.format == "usd":
        if len(ages) > 1:
            raise SystemExit("cambium export: --format usd writes one age; give one --ages value")
        files = tree.export(a.out, format="usd", lod=a.lod)
    else:
        files = tree.export(a.out, format="glb", lod=a.lod, ages=ages, seasons=_words(a.seasons), log=say)
    print(f"{len(files)} files, {time.time() - t0:.0f} s -> {a.out}")
    return 0


def cmd_forest(a) -> int:
    from ._forest import _forest
    from ._species import species_file

    name = species_file(a.species).stem
    out = Path(a.out or Path("cambium_out") / f"{name}_forest_seed{a.seed}")
    t0 = time.time()
    f = _forest(a.species, a.seed, a.years, a.environment, a.area, a.stems, a.mortality, a.spread, a.regeneration,
                _ints(a.tree_lists), not a.quiet, a.set)
    f.save(out)
    s = f.stats[-1] if f.stats else {}
    print(f"year {f.year}: {s.get('stems_per_ha', 0)} stems/ha, basal area {s.get('basal_area_ob_m2_ha', '-')} m2/ha, "
          f"top height {s.get('top_height_m', '-')} m; {time.time() - t0:.0f} s -> {out}")
    return 0


def cmd_species(a) -> int:
    from ._species import LABELS, species

    rows = species()
    for sp in rows:
        aliases = f" (also: {', '.join(sp.aliases)})" if sp.aliases else ""
        print(f"{sp.name}{aliases}: {sp.common_name}, {sp.scientific_name}")
        if sp.labels:
            total = sum(sp.labels.values())
            print(f"  {total} values labelled: " + ", ".join(f"{sp.labels.get(k, 0)} {k}" for k in LABELS))
    return 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):   # a stream that can't change: leave it
        pass
    a = parser().parse_args(argv)
    try:
        return {"grow": cmd_grow, "forest": cmd_forest, "export": cmd_export, "species": cmd_species}[a.command](a)
    except (ValueError, FileNotFoundError) as exc:
        print(f"cambium {a.command}: {exc}", file=sys.stderr)
        return 2
    except KeyError as exc:
        if "no such" not in str(exc):     # a --set or look key that isn't there; anything else is a bug
            raise
        print(f"cambium {a.command}: {exc.args[0]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
