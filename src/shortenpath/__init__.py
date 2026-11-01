"""Abbreviate a filesystem path for display within a terminal column budget."""

from __future__ import annotations

from ._parts import Flavor
from ._shorten import shorten
from ._width import display_width

__version__ = "1.0.0"

__all__ = ["Flavor", "display_width", "shorten"]

del annotations
