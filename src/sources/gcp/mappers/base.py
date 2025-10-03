# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Protocol, TypeVar

from src.model import PlannedItem

__all__ = [
    "MappingError",
    "BaseItemMapper",
    "FieldSpec",
    "get_value",
    "as_bool",
    "identity",
    "GoogleBaseMapper",
    "map_to_planned_item",
]
T = TypeVar("T")


class MappingError(ValueError): ...


class BaseItemMapper(Protocol):
    def to_entity(self, raw: Mapping[str, Any]) -> PlannedItem: ...


@dataclass(frozen=True)
class FieldSpec:
    source: str
    transform: Callable[[Any], Any] = lambda v: v
    default: Any = None
    required: bool = False


def get_value(raw: Mapping[str, Any], path: str) -> Any:
    current: Any = raw
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "t"}
    return bool(value)


def identity(v: T) -> T:
    return v


def map_to_planned_item(
    raw: Mapping[str, Any],
    field_specs: Mapping[str, FieldSpec],
) -> PlannedItem:
    if not isinstance(raw, Mapping):
        raise TypeError("raw must be a Mapping[str, Any].")
    mapped: Dict[str, Any] = {}
    for dest_attr, spec in field_specs.items():
        try:
            raw_value = get_value(raw, spec.source)
            base_value = raw_value if raw_value is not None else spec.default
            transformed = spec.transform(base_value)
            value = base_value if transformed is None else transformed
        except Exception as exc:  # noqa: BLE001
            raise MappingError(
                f"Error mapping field '{dest_attr}' from source '{spec.source}': {exc}"
            ) from exc
        if spec.required and value is None:
            raise MappingError(
                f"Required field '{dest_attr}' (source '{spec.source}') is missing."
            )
        mapped[dest_attr] = value
    return PlannedItem(**mapped)


class GoogleBaseMapper(BaseItemMapper):
    def __init__(self, field_specs: Dict[str, FieldSpec]):
        self._field_specs = field_specs

    def to_entity(self, raw: Mapping[str, Any]) -> PlannedItem:
        return map_to_planned_item(raw, self._field_specs)
