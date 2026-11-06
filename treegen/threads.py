"""One maths-library thread per run: the standard setting (the maintainer, 2026-11-06;
DECISIONS.md row 26).

Results depend slightly on the OpenBLAS thread count (out/bench/m1/parallel_proof_
one_thread.txt: up to 0.03 % at age 60), so a run on a PC with a different number of
cores could differ.  One thread gives the same bits everywhere it runs, and costs
about 6 % in speed (47 s against 50 s for the seed-1 tree).

Importing treegen sets this.  A library reads the environment variables only when
it loads, and a script may have imported numpy first, so the loaded OpenBLAS copies
(numpy and scipy each bundle their own) are also set directly.  actual_threads()
reads the count back from the libraries; the run manifest records that.
"""
from __future__ import annotations

import ctypes
import glob
import importlib.util
import os
import sys
from pathlib import Path

THREADS = 1
ENV_VARS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS")
# package -> (set function, get function) of the OpenBLAS it bundles
OPENBLAS = {"numpy": ("scipy_openblas_set_num_threads64_", "scipy_openblas_get_num_threads64_"),
            "scipy": ("scipy_openblas_set_num_threads", "scipy_openblas_get_num_threads")}


def _library(package: str):
    """The package's bundled OpenBLAS, without importing the package; None if there isn't one here."""
    spec = importlib.util.find_spec(package)
    if spec is None or spec.origin is None:
        return None
    windows = sys.platform == "win32"
    files = glob.glob(str(Path(spec.origin).parent.parent / f"{package}.libs" / ("*openblas*.dll" if windows else "*openblas*.so*")))
    if not files:
        return None
    return (ctypes.WinDLL if windows else ctypes.CDLL)(files[0])


def set_threads() -> None:
    for name in ENV_VARS:
        os.environ[name] = str(THREADS)
    if "numpy" not in sys.modules:
        return   # nothing loaded yet: the libraries will read the variables above
    for package, (setter, _) in OPENBLAS.items():
        lib = _library(package)
        if lib is not None:
            getattr(lib, setter)(THREADS)


def actual_threads() -> dict:
    """The thread count each OpenBLAS really has now; None where it can't be read."""
    out = {}
    for package, (_, getter) in OPENBLAS.items():
        lib = _library(package)
        out[f"{package}_openblas"] = None if lib is None else int(getattr(lib, getter)())
    return out


def library_versions() -> dict:
    import numba
    import numpy
    import scipy

    def blas(mod):
        try:
            d = mod.show_config(mode="dicts")["Build Dependencies"]["blas"]
            return f"{d.get('name')} {d.get('version')}"
        except Exception:
            return None

    return {"numpy": numpy.__version__, "scipy": scipy.__version__, "numba": numba.__version__,
            "numpy_blas": blas(numpy), "scipy_blas": blas(scipy), "python": sys.version.split()[0]}
