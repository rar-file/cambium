"""Yearly records, as Python dicts, JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path


def _flat(record: dict, prefix: str = "") -> dict:
    """Nested dicts become dotted columns; lists stay whole, as JSON text."""
    out = {}
    for k, v in record.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flat(v, key + "."))
        elif isinstance(v, (list, tuple)):
            out[key] = json.dumps(v)
        else:
            out[key] = v
    return out


class Stats(list):
    """One record (a dict) per year, oldest first: ``stats[-1]`` is the last year.

    ``to_json()`` gives the records exactly as the engine made them; ``to_csv()`` gives one row a
    year, nested values as dotted columns (``water.psi_collar_mpa``), lists as JSON text, and an
    empty cell where a year has no value."""

    def to_json(self, path: str | Path | None = None, indent: int | None = 1) -> str:
        text = json.dumps(list(self), indent=indent, allow_nan=False)
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(text, encoding="utf-8")
        return text

    def to_csv(self, path: str | Path | None = None) -> str:
        rows = [_flat(r) for r in self]
        columns = list(dict.fromkeys(k for r in rows for k in r))
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        text = buf.getvalue()
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(text, encoding="utf-8")
        return text
