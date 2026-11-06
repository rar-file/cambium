"""Procedural tree generator core (engine-agnostic)."""
from . import threads as _threads

_threads.set_threads()   # before anything below loads the maths libraries

__version__ = "0.1.0"
