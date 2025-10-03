# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from src.common.hierarchy.default_item_sorter import DefaultItemSorter
from src.common.hierarchy.item_mapper_protocol import ItemMapperProtocol
from src.common.hierarchy.item_node import ItemNode
from src.common.hierarchy.item_not_found_error import ItemNotFoundError
from src.common.hierarchy.item_sorter import ItemSorter
from src.common.hierarchy.parent_policy import ParentPolicy


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
