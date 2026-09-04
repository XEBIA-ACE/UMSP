"""UMSP application package (Python 3.10+)."""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 10)

if sys.version_info[:2] < MIN_PYTHON:
    raise RuntimeError(
        f"UMSP requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+, "
        f"found {sys.version.split()[0]}"
    )

__version__ = "0.1.0"


def runtime_info() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "implementation": sys.implementation.name,
        "umsp": __version__,
    }
