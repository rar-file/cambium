"""Try a tree export in Unreal 5.8, in an empty project of our own, with no window.

    python tools/unreal_test.py import tools/unreal/job.json     # import and read back (see tools/unreal/import_check.py)
    python tools/unreal_test.py render tools/unreal/job.json     # draw it from inside Unreal (tools/unreal/render_shot.py)
    python tools/unreal_test.py route JOB --export out/game/unreal # the game's own scripts pick up an export (tools/unreal/game_route.py)

Only touches out/unreal_test/ (git-ignored) and Epic's shared cache.  It starts nothing while any Unreal
editor or game is open, nor with under ORIGIN_UE_MIN_GB free (6 by default, 11 for a voxel build), and
stops Unreal if free memory falls under 1.5 GB.  One instance at a time.

Unreal 5.8 logs this PC's Visual C++ runtime as outdated, which alone makes a commandlet exit 1, so a
run is judged by its other errors and by the results file its script writes.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from batch import free_gb  # noqa: E402

EDITOR = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
TEST = ROOT / "out" / "unreal_test"
PROJECT = TEST / "TreeTest" / "TreeTest.uproject"
STOP_GB = 1.5

UPROJECT = {
    "FileVersion": 3,
    "EngineAssociation": "5.8",
    "Category": "",
    "Description": "An empty project for trying tree exports. Nothing of the game's is in it.",
    "Plugins": [
        {"Name": "PythonScriptPlugin", "Enabled": True},
        {"Name": "EditorScriptingUtilities", "Enabled": True},
        {"Name": "GeometryScripting", "Enabled": True},
    ],
}

# The game's rendering settings, so a comparison lights the same way: Nanite, Nanite Foliage, Lumen with hardware
# ray tracing, virtual shadow maps, TSR, DX12. Shader workers held down for this 16 GB PC.
DEFAULT_ENGINE = """[/Script/EngineSettings.GameMapsSettings]
GameDefaultMap=/Engine/Maps/Entry.Entry
EditorStartupMap=/Engine/Maps/Entry.Entry

[/Script/Engine.RendererSettings]
r.AllowStaticLighting=False
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Shadow.Virtual.Enable=1
r.GenerateMeshDistanceFields=True
r.RayTracing=True
r.Lumen.HardwareRayTracing=True
r.SkinCache.CompileShaders=True
r.AntiAliasingMethod=4
r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True
r.DefaultFeature.AutoExposure=True
r.Nanite.ProjectEnabled=True
r.DefaultFeature.MotionBlur=False
r.Nanite.Foliage=True

[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
-D3D12TargetedShaderFormats=PCD3D_SM5
+D3D12TargetedShaderFormats=PCD3D_SM6

[ConsoleVariables]
r.AutoExposure.LuminanceMethod=2
r.SkyAtmosphere.MultiScatteringLUT.HighQuality=1
r.Shadow.Virtual.Clipmap.WPODisableDistance.LodBias=0
; a scene capture with no viewport doesn't tell the streamer where it looks: keep every mip in memory for pictures
r.TextureStreaming=0

[DevOptions.Shaders]
NumUnusedShaderCompilingThreads=11
NumUnusedShaderCompilingThreadsDuringGame=11
"""


# What the game's scripts need in the test project, copied once.  Read only from the game's folder; all
# of it stays under out/unreal_test, which git ignores.  Licences: Poly Haven and ambientCG, all CC0.
GAME = Path(os.environ.get("CAMBIUM_GAME_DIR", "../game"))
FROM_GAME = ["Tools/Editor/build_materials.py", "Tools/Editor/import_world_assets.py", "Tools/Editor/set_tree_looks.py", "Content/Data/Science/water.json",
             "SourceArt/PolyHaven/fern_02", "SourceArt/PolyHaven/bark_debris_01", "SourceArt/PolyHaven/lichen_rock", "SourceArt/PolyHaven/forrest_ground_01", "SourceArt/ambientCG/Moss001/Moss001_diff_2k.jpg"]
FROM_GAME_BIRCH = ["SourceArt/PolyHaven/betula_pendula", "SourceArt/PolyHaven_split/betula_pendula/betula_pendula_a.fbx"]


def copy_from_game(items: list) -> None:
    project = PROJECT.parent
    for item in items:
        src = GAME / item
        if item.startswith("Tools/Editor/"):
            dst = project / "GameScripts" / src.name
        else:
            dst = project / item
        if src.is_dir():
            for f in src.rglob("*"):
                if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".exr") and "_2k." in f.name.lower():
                    t = dst / f.relative_to(src)
                    if not t.exists():
                        t.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, t)
        elif not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def copy_export(export: Path) -> None:
    for f in (export / "SourceArt").rglob("*"):
        if f.is_file():
            t = PROJECT.parent / f.relative_to(export)
            t.parent.mkdir(parents=True, exist_ok=True)
            if not t.exists() or t.stat().st_mtime < f.stat().st_mtime:
                shutil.copy2(f, t)


def unreal_running() -> list:
    out = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    names = ("unrealeditor", "ue5editor", os.environ.get("CAMBIUM_GAME_PROCESS", "game").lower(), "shadercompileworker", "unrealbuildtool")
    return sorted({line.split()[0] for line in out.splitlines() if line.split() and any(line.startswith(n) for n in names)})


INIT_UNREAL = """import os

script = os.environ.get("TREEGEN_UE_RENDER")
if script:
    exec(compile(open(script, encoding="utf-8").read(), script, "exec"), {"__name__": "treegen_render"})
"""


def make_project() -> None:
    PROJECT.parent.mkdir(parents=True, exist_ok=True)
    if not PROJECT.exists():
        PROJECT.write_text(json.dumps(UPROJECT, indent=1), encoding="utf-8")
    starter = PROJECT.parent / "Content" / "Python" / "init_unreal.py"
    starter.parent.mkdir(parents=True, exist_ok=True)
    starter.write_text(INIT_UNREAL, encoding="utf-8")
    cfg = PROJECT.parent / "Config" / "DefaultEngine.ini"
    cfg.parent.mkdir(exist_ok=True)
    if not cfg.exists():
        cfg.write_text(DEFAULT_ENGINE, encoding="utf-8")


def wait_for_memory(min_gb: float, minutes: float) -> None:
    """Hold on until enough memory is free, or the time is up; run() then decides."""
    end = time.time() + minutes * 60.0
    while time.time() < end and free_gb() < min_gb:
        time.sleep(10.0)


def run(script: Path, job: dict, extra: list, min_gb: float, label: str, timeout_s: int = 3600, windowless_editor: bool = False) -> int:
    running = unreal_running()
    if running:
        print(f"NOT STARTED: Unreal is open ({', '.join(running)})", flush=True)
        return 3
    free = free_gb()
    if free < min_gb:
        print(f"NOT STARTED: {free:.2f} GB free, this run needs {min_gb:.1f}", flush=True)
        return 4
    make_project()
    job_file = TEST / f"job_{label}.json"
    results = TEST / f"results_{label}.json"
    results.unlink(missing_ok=True)
    job_file.write_text(json.dumps({**job, "results": str(results)}, indent=1), encoding="utf-8")
    log_path = TEST / f"log_{label}.txt"
    # A commandlet has no frames, and drawing needs them, so it runs the editor itself, with no window.
    # -ExecutePythonScript quits as soon as its script returns, so the test project's init_unreal.py starts it.
    how = ["-RenderOffScreen"] if windowless_editor else ["-run=pythonscript", f"-script={script}"]
    cmd = [str(EDITOR), str(PROJECT), *how, "-ini:Engine:[ConsoleVariables]:Editor.AsyncStaticMeshCompilationMaxConcurrency=1",
           "-unattended", "-nosplash", "-nopause", "-stdout", "-FullStdOutLogOutput", *extra]
    env = dict(os.environ, TREEGEN_UE_JOB=str(job_file))
    if windowless_editor:
        env["TREEGEN_UE_RENDER"] = str(script)
    print(f"starting Unreal with {free:.2f} GB free: {label}", flush=True)
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        low = [free]
        stopped = {"why": None}

        def watch():
            while proc.poll() is None:
                now = free_gb()
                low[0] = min(low[0], now)
                if now < STOP_GB:
                    stopped["why"] = f"free memory fell to {now:.2f} GB"
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
                    return
                if time.time() - t0 > timeout_s:
                    stopped["why"] = f"over {timeout_s} s"
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
                    return
                time.sleep(2.0)

        w = threading.Thread(target=watch, daemon=True)
        w.start()
        code = proc.wait()
        w.join(5)
    text = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    errors = sorted({line.split("] ", 2)[-1].strip()[:220] for line in text if ("Error:" in line or "LogPython: Error" in line) and "Visual C++ redistributable" not in line and "Warning/Error Summary" not in line})
    print(f"{label}: exit {code} in {time.time() - t0:.0f} s; lowest free memory {low[0]:.2f} GB; results {'written' if results.exists() else 'NOT written'}; {stopped['why'] or 'not stopped'}", flush=True)
    for e in errors[:15]:
        print("  ERROR", e, flush=True)
    print(f"  log: {log_path}", flush=True)
    return 0 if results.exists() and not stopped["why"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("what", choices=("import", "render", "route"))
    ap.add_argument("--export", default=None, help="route: an export folder to copy into the test project")
    ap.add_argument("--with-game-birch", action="store_true", help="route: copy the game's birch, one variant, too")
    ap.add_argument("job", help="a JSON file describing the run, or inline JSON")
    ap.add_argument("--label", default="run")
    ap.add_argument("--min-gb", type=float, default=float(os.environ.get("ORIGIN_UE_MIN_GB", 6.0)))
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--wait-minutes", type=float, default=0.0, help="wait this long for enough free memory before giving up")
    a = ap.parse_args()
    job = json.loads(a.job) if a.job.lstrip().startswith("{") else json.loads(Path(a.job).read_text(encoding="utf-8"))
    scripts = {"import": "import_check.py", "render": "render_shot.py", "route": "game_route.py"}
    if a.what == "route":
        make_project()
        copy_from_game(FROM_GAME + (FROM_GAME_BIRCH if a.with_game_birch else []))
        if a.export:
            copy_export(Path(a.export))
        project = PROJECT.parent
        job["files"] = [str(project / f) for f in job.get("files", [])]
    job["here"] = str(ROOT / "tools" / "unreal")
    if job.get("voxelize"):
        a.min_gb = max(a.min_gb, 11.0)
    extra = []
    end = time.time() + a.wait_minutes * 60.0
    while True:
        wait_for_memory(a.min_gb, (end - time.time()) / 60.0)
        code = run(ROOT / "tools" / "unreal" / scripts[a.what], job, extra, a.min_gb, a.label, a.timeout, windowless_editor=a.what == "render")
        # memory came and went in the moment between: wait again while there's time
        if code != 4 or time.time() >= end:
            return code


if __name__ == "__main__":
    sys.exit(main())
