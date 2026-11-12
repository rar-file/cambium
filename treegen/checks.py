"""Checks a command makes on its arguments before anything grows, so a slip costs a second, not a run.

Each raises ValueError with a plain message.  A command catches it and calls ``stop``: one line on
stderr and exit code 2, as argparse does for the arguments it checks itself.
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

# A plot gives its k-th recruit the seed seed * 1_000_000 + k (treegen/plot.py); up to 2**32 - 1 that stays
# well inside a 64-bit integer, wherever a seed is stored or hashed.  No run in the repo uses a larger one.
SEED_MAX = 2**32 - 1
YEARS_MAX = 1000


def whole(name: str, value, lo: int, hi: int | None = None) -> int:
    """A whole number from lo to hi (no upper limit when hi is None)."""
    try:
        v = int(str(value).strip())
    except ValueError:
        v = None
    if v is None or v < lo or (hi is not None and v > hi):
        raise ValueError(f"{name} must be a whole number {f'from {lo} to {hi}' if hi is not None else f'of at least {lo}'}, not {value!r}")
    return v


def seed(value, name: str = "--seed") -> int:
    return whole(name, value, 0, SEED_MAX)


def years(value, name: str = "--years") -> int:
    return whole(name, value, 1, YEARS_MAX)


def positive(name: str, value) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = math.nan
    if not (math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be a number above 0, not {value!r}")
    return v


def wholes(name: str, text, lo: int, hi: int | None = None) -> list[int]:
    """Comma-separated whole numbers, e.g. --ages 15,30,60; an empty text gives []."""
    parts = [x.strip() for x in str(text or "").split(",") if x.strip()]
    try:
        return [whole(name, x, lo, hi) for x in parts]
    except ValueError:
        span = f"from {lo} to {hi}" if hi is not None else f"of at least {lo}"
        raise ValueError(f"{name} must be whole numbers {span}, separated by commas, not {text!r}") from None


def folder(path) -> Path:
    """The output folder, made if it isn't there, and written to once, so a run can't fail at its end."""
    p = Path(path)
    if p.exists() and not p.is_dir():
        raise ValueError(f"the output folder {p} is a file")
    try:
        p.mkdir(parents=True, exist_ok=True)
        tempfile.TemporaryFile(dir=p).close()
    except OSError as exc:
        raise ValueError(f"can't write to the output folder {p}: {exc.strerror or exc}") from None
    return p


def inputs(species, environment, items=()) -> dict:
    """The species and site files load (each name in them is known) and every --set item applies to a
    fresh copy of the species' values.  The run itself loads them again.  Returns the species file."""
    from .checkpoint import set_values
    from .params import load_environment, load_species

    sp, raw = load_species(species)
    load_environment(environment)
    set_values(sp, list(items))
    return raw


class Parser(argparse.ArgumentParser):
    """argparse, but a slip it finds itself (a letter for a number, a choice it doesn't have) is one
    plain line and exit code 2, as the checks above give, not the usage block first.  --help still
    shows the usage.  Its sub-commands get the same class."""

    def error(self, message: str):
        self.exit(2, f"{self.prog}: {message} (--help lists the options)\n")


def stop(prog: str, exc: BaseException) -> SystemExit:
    """One line on stderr; raise what it returns, for exit code 2."""
    print(f"{prog}: {exc}", file=sys.stderr)
    return SystemExit(2)
