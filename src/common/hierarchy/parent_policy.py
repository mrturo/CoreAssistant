# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from enum import Enum, auto


class ParentPolicy(Enum):
    LENIENT = auto()
    STRICT = auto()
