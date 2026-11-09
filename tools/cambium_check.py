"""Checks that the cambium package changes nothing, and that it installs.

    python tools/cambium_check.py same --seeds 1,2 --years 25 --label node_prod_same
        cambium.grow(seed=s, years=y) against `python cli.py --seed s --years y --no-mesh`, open and in a
        stand: the yearly stats must be identical.  Also grow(stages=...) for the first seed, and
        cambium.forest() against `python tools/forest.py run` for a small plot.
    python tools/cambium_check.py wheel --label node_prod_wheel
        Builds the wheel in a throwaway environment, lists it, installs it there, and runs the
        `cambium` command from outside the checkout: version, species, a short tree against cli.py,
        and both exports.  Also compiles the shipped code with the oldest Python claimed (3.12), if
        that interpreter is on the machine.
    python tools/cambium_check.py docs --label node_prod_docs
        Builds the docs site with `mkdocs build --strict`, as .github/workflows/docs.yml does.

Each case runs in its own process.  Results go to out/bench/ensemble/<label>/report.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "bench" / "ensemble"

GROW = """import sys, cambium
s, y, stand, stages, path = sys.argv[1:6]
t = cambium.grow(seed=int(s), years=int(y), stand=stand == "1", stages=[int(a) for a in stages.split(",") if a])
t.to_json(path)
"""
FOREST = """import sys, cambium
s, y, area, path = sys.argv[1:5]
cambium.forest(seed=int(s), years=int(y), area_m2=float(area)).to_json(path)
"""


def run(cmd: list, cwd: Path = ROOT, env: dict | None = None) -> tuple:
    t0 = time.time()
    p = subprocess.run([str(c) for c in cmd], cwd=str(cwd), capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))[:200]} failed:\n{p.stdout[-1500:]}\n{p.stderr[-3000:]}")
    return p.stdout, round(time.time() - t0, 1)


def first_difference(a: list, b: list) -> str | None:
    if len(a) != len(b):
        return f"{len(a)} years against {len(b)}"
    for ra, rb in zip(a, b):
        if ra != rb:
            keys = [k for k in sorted(set(ra) | set(rb), key=str) if ra.get(k) != rb.get(k)]
            return f"year {rb.get('year')}: {keys[:6]}"
    return None


def compare(name: str, ours: list, theirs: list, seconds: dict) -> dict:
    diff = first_difference(ours, theirs)
    same = diff is None and json.dumps(ours) == json.dumps(theirs)
    last = theirs[-1] if theirs else {}
    row = {"case": name, "identical": same, "years": len(theirs), "difference": diff, "seconds": seconds,
           "final": {k: last.get(k) for k in ("year", "height_m", "dbh_cm", "crown_width_m", "trees", "stems_per_ha", "top_height_m") if k in last}}
    print(f"{name}: {'IDENTICAL' if same else 'DIFFERENT ' + str(diff)}  {row['final']}  {seconds}", flush=True)
    return row


def cmd_same(a) -> list:
    rows = []
    seeds = [int(x) for x in a.seeds.split(",")]
    with tempfile.TemporaryDirectory(prefix="cambium_same_") as tmp:
        tmp = Path(tmp)
        for i, s in enumerate(seeds):
            for stand in (False, True):
                mode = "stand" if stand else "open"
                cli_out = tmp / f"cli_{mode}"
                cmd = [sys.executable, "cli.py", "--seed", s, "--years", a.years, "--no-mesh", "--quiet", "--out", cli_out]
                _, t_cli = run(cmd + (["--stand"] if stand else []))
                theirs = json.loads((cli_out / (f"{s}_stand" if stand else str(s)) / "stats.json").read_text(encoding="utf-8"))["per_year"]
                variants = [("", "grow")] + ([(a.stages, f"grow(stages={a.stages})")] if i == 0 and a.stages else [])
                for stages, label in variants:
                    path = tmp / f"cambium_{s}_{mode}_{len(stages)}.json"
                    _, t = run([sys.executable, "-c", GROW, s, a.years, int(stand), stages, path])
                    ours = json.loads(path.read_text(encoding="utf-8"))
                    rows.append(compare(f"seed {s} {mode}: cambium.{label} vs cli.py", ours, theirs, {"cli": t_cli, "cambium": t}))
        if a.forest_years:
            out = tmp / "forest"
            _, t_tool = run([sys.executable, "tools/forest.py", "run", "--seed", seeds[0], "--years", a.forest_years,
                             "--area", a.forest_area, "--out", out])
            theirs = json.loads((out / "plot.json").read_text(encoding="utf-8"))["stats"]
            path = tmp / "cambium_forest.json"
            _, t = run([sys.executable, "-c", FOREST, seeds[0], a.forest_years, a.forest_area, path])
            rows.append(compare(f"forest seed {seeds[0]}, {a.forest_area} m2: cambium.forest vs tools/forest.py run",
                                json.loads(path.read_text(encoding="utf-8")), theirs, {"tools/forest.py": t_tool, "cambium": t}))
    return rows


def _shipped_files() -> list:
    files = sorted((ROOT / "cambium").rglob("*.py")) + sorted((ROOT / "treegen").rglob("*.py"))
    return files + [ROOT / "cli.py", ROOT / "tools" / "game_export.py", ROOT / "tools" / "tree_list.py"]


def check_old_python(rows: list) -> None:
    old = shutil.which("python3.12")
    if not old:
        rows.append({"case": "compile with Python 3.12", "identical": None, "difference": "no python3.12 here"})
        return
    code = "import sys\nfor f in sys.argv[1:]:\n    compile(open(f, encoding='utf-8').read(), f, 'exec')\nprint(sys.version.split()[0])"
    out, _ = run([old, "-c", code, *_shipped_files()])
    rows.append({"case": f"compile {len(_shipped_files())} shipped files with Python {out.strip()}", "identical": True, "difference": None})
    print(rows[-1]["case"] + ": OK", flush=True)


def _environment(tmp: Path) -> Path:
    """A throwaway venv that sees this one's packages (numpy, numba, ...) but installs into itself."""
    venv = tmp / "venv"
    run([sys.executable, "-m", "venv", venv])
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    out, _ = run([py, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"])
    ours = [p for p in sys.path if p.endswith("site-packages") and Path(p).is_dir()]
    (Path(out.strip()) / "shared_packages.pth").write_text("\n".join(ours) + "\n", encoding="utf-8")
    return py


def cmd_wheel(a) -> list:
    rows = []
    check_old_python(rows)
    with tempfile.TemporaryDirectory(prefix="cambium_wheel_") as tmp:
        tmp = Path(tmp)
        py = _environment(tmp)
        dist = tmp / "dist"
        run([py, "-m", "pip", "wheel", "--no-deps", "--quiet", "-w", dist, ROOT])
        wheel = next(dist.glob("pycambium-*.whl"))
        with zipfile.ZipFile(wheel) as z:
            names = z.namelist()
            meta = next(z.read(n).decode() for n in names if n.endswith(".dist-info/METADATA"))
            entry = next(z.read(n).decode() for n in names if n.endswith(".dist-info/entry_points.txt"))
        top = sorted({n.split("/")[0] for n in names})
        images = [n for n in names if n.lower().endswith((".jpg", ".jpeg", ".png", ".heic"))]
        wanted = ["cambium/data/species/betula_pendula.yaml", "cambium/data/environments/sweden_open_field.yaml",
                  "cambium/data/reference/betula_pendula/labels.yaml", "cambium/data/reference/targets.yaml",
                  "cambium/_scripts/cli.py", "cambium/_scripts/game_export.py", "cambium/_scripts/tree_list.py", "treegen/growth.py"]
        missing = [n for n in wanted if n not in names]
        rows.append({"case": f"wheel {wheel.name}", "identical": not missing and not images, "size_mb": round(wheel.stat().st_size / 2**20, 2),
                     "files": len(names), "top_level": top, "missing": missing, "images": images,
                     "requires_python": [ln for ln in meta.splitlines() if ln.startswith("Requires-Python")],
                     "requires_dist": [ln for ln in meta.splitlines() if ln.startswith("Requires-Dist")],
                     "license": [ln for ln in meta.splitlines() if ln.startswith("License")], "entry_points": entry.strip()})
        print(json.dumps(rows[-1], indent=1), flush=True)
        run([py, "-m", "pip", "install", "--no-deps", "--quiet", wheel])
        cambium = py.parent / ("cambium.exe" if os.name == "nt" else "cambium")
        work = tmp / "work"       # outside the checkout, so only the installed package can be found
        work.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        out, _ = run([py, "-c", "import cambium, cambium._engine as e; print(cambium.__file__, e.SOURCE, e.DATA)"], cwd=work, env=env)
        installed = "site-packages" in out and " False " in out
        rows.append({"case": "imports from the installed wheel, not the checkout", "identical": installed, "difference": out.strip()})
        print(rows[-1]["case"], out.strip(), flush=True)
        version, _ = run([cambium, "--version"], cwd=work, env=env)
        species, _ = run([cambium, "species"], cwd=work, env=env)
        rows.append({"case": "cambium --version / species", "identical": version.strip() == "cambium 0.9.0",
                     "difference": version.strip() + " | " + species.strip()})
        print(version.strip(), "|", species.strip(), flush=True)
        y = str(a.years)
        _, t_inst = run([cambium, "grow", "--species", "birch", "--seed", "3", "--years", y, "--out", work / "g", "--quiet"], cwd=work, env=env)
        _, t_cli = run([sys.executable, "cli.py", "--seed", "3", "--years", y, "--no-mesh", "--no-preview", "--quiet", "--out", tmp / "cli"])
        ours = json.loads((work / "g" / "stats.json").read_text(encoding="utf-8"))["per_year"]
        theirs = json.loads((tmp / "cli" / "3" / "stats.json").read_text(encoding="utf-8"))["per_year"]
        rows.append(compare(f"installed `cambium grow --seed 3 --years {y}` vs cli.py", ours, theirs, {"cambium": t_inst, "cli": t_cli}))
        for fmt in ("glb", "usd"):
            _, t = run([cambium, "grow", "--seed", "3", "--years", y, "--export", fmt, "--out", work / fmt, "--quiet"], cwd=work, env=env)
            files = sorted(p.name for p in (work / fmt).iterdir())
            ok = any(f.endswith(".glb") for f in files) if fmt == "glb" else "tree.usdc" in files and "tree_reduced.usdc" in files
            rows.append({"case": f"installed `cambium grow --export {fmt}`", "identical": ok, "files": files, "seconds": t})
            print(f"export {fmt}: {'OK' if ok else 'MISSING'} {files} {t} s", flush=True)
        _, t = run([cambium, "export", "--seed", "3", "--ages", f"{max(int(y) - 2, 1)},{y}", "--lod", "lod1",
                    "--seasons", "summer,autumn", "--out", work / "stages", "--quiet"], cwd=work, env=env)
        files = sorted(p.name for p in (work / "stages").iterdir())
        rows.append({"case": "installed `cambium export` (two ages, lod1, two seasons)", "identical": len([f for f in files if f.endswith(".glb")]) == 4,
                     "files": files, "seconds": t})
        print(f"export stages: {files} {t} s", flush=True)
        _, t = run([cambium, "forest", "--seed", "1", "--years", "5", "--area", "100", "--out", work / "f", "--quiet"], cwd=work, env=env)
        files = sorted(p.name for p in (work / "f").iterdir())
        rows.append({"case": "installed `cambium forest`", "identical": files == ["forest.json", "stats.csv", "trees.csv"], "files": files, "seconds": t})
        print(f"forest: {files} {t} s", flush=True)
    return rows


def cmd_docs(a) -> list:
    """The docs site built as its workflow builds it, in a venv of its own (nothing shared)."""
    with tempfile.TemporaryDirectory(prefix="cambium_docs_") as tmp:
        tmp = Path(tmp)
        run([sys.executable, "-m", "venv", tmp / "venv"])
        py = tmp / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run([py, "-m", "pip", "install", "--quiet", "mkdocs-material>=9.5,<10"])
        p = subprocess.run([str(py), "-m", "mkdocs", "build", "--strict", "-f", str(ROOT / "mkdocs.yml"), "-d", str(tmp / "site")],
                           cwd=str(ROOT), capture_output=True, text=True)
        log = (p.stdout + p.stderr).strip()
        pages = sorted(str(f.relative_to(tmp / "site")) for f in (tmp / "site").rglob("index.html")) if p.returncode == 0 else []
        row = {"case": "mkdocs build --strict", "identical": p.returncode == 0, "pages": pages, "log": log[-4000:]}
        print(log[-4000:], flush=True)
        print(f"docs: {'OK' if p.returncode == 0 else 'FAILED'}, {len(pages)} pages", flush=True)
    return [row]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    s = sub.add_parser("same")
    s.add_argument("--seeds", default="1,2")
    s.add_argument("--years", type=int, default=25)
    s.add_argument("--stages", default="10", help="ages for the grow(stages=...) variant, first seed only; empty for none")
    s.add_argument("--forest-years", type=int, default=10)
    s.add_argument("--forest-area", type=float, default=200.0)
    s.add_argument("--label", required=True)
    w = sub.add_parser("wheel")
    w.add_argument("--years", type=int, default=6)
    w.add_argument("--label", required=True)
    d = sub.add_parser("docs")
    d.add_argument("--label", required=True)
    a = ap.parse_args()
    t0 = time.time()
    rows = {"same": cmd_same, "wheel": cmd_wheel, "docs": cmd_docs}[a.what](a)
    out = OUT / a.label
    out.mkdir(parents=True, exist_ok=True)
    ok = all(r.get("identical") is not False for r in rows)
    (out / "report.json").write_text(json.dumps({"ok": ok, "seconds": round(time.time() - t0), "rows": rows}, indent=1), encoding="utf-8")
    print("ALL IDENTICAL" if ok and a.what == "same" else "ALL OK" if ok else "FAILED", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
