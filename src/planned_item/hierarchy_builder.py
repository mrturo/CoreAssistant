# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Mapping, Optional, Protocol, runtime_checkable


class ItemNotFoundError(KeyError): ...


class DuplicateItemIdError(ValueError): ...


@runtime_checkable
class ItemNode(Protocol):
    id: str
    parent: Optional[str]
    title: str
    position: Optional[str]
    subitems: list[ItemNode]

    def add_subitem(self, subitem: ItemNode) -> None: ...
    def is_root(self) -> bool: ...


class ItemMapperProtocol(Protocol):
    def to_entity(self, raw: Mapping[str, object]) -> ItemNode: ...


class ItemSorter(Protocol):
    def sort(self, items: list[ItemNode]) -> None: ...


def _default_sort_key(item: ItemNode) -> tuple[str, str]:
    pos = item.position if item.position is not None else "\uffff"
    ttl = item.title if item.title is not None else ""
    return pos, ttl


@dataclass(frozen=True)
class DefaultItemSorter:
    def sort(self, items: list[ItemNode]) -> None:
        items.sort(key=_default_sort_key)


class ParentPolicy(Enum):
    LENIENT = auto()
    STRICT = auto()


@dataclass
class HierarchyBuilder:
    parent_policy: ParentPolicy = ParentPolicy.LENIENT
    sorter: ItemSorter = DefaultItemSorter()

    def build(
        self, items: Iterable[Mapping[str, object]], mapper: ItemMapperProtocol
    ) -> list[ItemNode]:
        items_by_id: dict[str, ItemNode] = {}
        roots: list[ItemNode] = []
        for raw in items:
            node = mapper.to_entity(raw)
            if not node.id:
                continue
            if node.id in items_by_id:
                continue
            items_by_id[node.id] = node
        for node in items_by_id.values():
            parent_id = node.parent
            if parent_id:
                parent = items_by_id.get(parent_id)
                if parent:
                    parent.add_subitem(node)
                elif self.parent_policy is ParentPolicy.STRICT:
                    raise ItemNotFoundError(
                        f"Parent {parent_id} not found for item {node.id}"
                    )
                else:
                    roots.append(node)
            else:
                roots.append(node)
        self._sort_tree(roots, items_by_id)
        return roots

    def _sort_tree(
        self, roots: list[ItemNode], items_by_id: dict[str, ItemNode]
    ) -> None:
        self.sorter.sort(roots)
        for node in items_by_id.values():
            if node.subitems:
                self.sorter.sort(node.subitems)
