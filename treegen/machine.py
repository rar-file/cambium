"""What a run was computed on: CPU, memory, operating system, library versions and
thread counts.  Used by the golden runs and the worker kit, because results can
differ in the last digits between CPUs.  Reads only; changes nothing."""
from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import sys

from . import threads


def _cpu_name() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return str(winreg.QueryValueEx(k, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    try:
        for line in subprocess.run(["lscpu"], capture_output=True, text=True, check=True).stdout.splitlines():
            if line.startswith("Model name"):
                return line.split(":", 1)[1].strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or platform.machine() or "unknown"


def _memory_gb() -> float | None:
    if sys.platform != "win32":
        try:
            return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3, 1)
        except (OSError, ValueError):
            return None

    class M(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return round(m.ullTotalPhys / 1024 ** 3, 1)


def _openblas_kernels() -> dict:
    """The kernel each OpenBLAS picked for this CPU (e.g. Haswell, Zen).  The most
    likely reason for last-digit differences between PCs."""
    out = {}
    names = {"numpy": "scipy_openblas_get_corename64_", "scipy": "scipy_openblas_get_corename"}
    for package, fn in names.items():
        lib = threads._library(package)
        if lib is None:
            out[f"{package}_openblas_kernel"] = None
            continue
        try:
            f = getattr(lib, fn)
            f.restype = ctypes.c_char_p
            out[f"{package}_openblas_kernel"] = f().decode()
        except (AttributeError, OSError):
            out[f"{package}_openblas_kernel"] = None
    return out


def describe_machine() -> dict:
    return {
        "computer": platform.node(),
        "cpu": _cpu_name(),
        "cpu_threads": os.cpu_count(),
        "memory_gb": _memory_gb(),
        "os": platform.platform(),
        "architecture": platform.machine(),
        "math_threads": threads.actual_threads(),
        "math_libraries": threads.library_versions(),
        **_openblas_kernels(),
    }
