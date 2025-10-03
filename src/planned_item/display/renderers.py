# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from typing import Iterable, List, Optional

from src.model.protocols import ItemLike, ItemLineFormatter, ItemRenderer
from src.planned_item.display.formatters import TextItemLineFormatter


class TreeRenderer(ItemRenderer):
    def __init__(
        self,
        indent_step: int = 2,
        formatter: Optional[ItemLineFormatter] = None,
        newline: str = "\n",
        detect_cycles: bool = True,
    ) -> None:
        if indent_step < 0:
            raise ValueError("indent_step must be >= 0")
        if not newline:
            raise ValueError("newline must be non-empty")
        self._indent_step = indent_step
        self._formatter = formatter or TextItemLineFormatter()
        self._newline = newline
        self._detect_cycles = detect_cycles

    def render(self, items: Iterable[ItemLike]) -> str:
        lines: List[str] = []
        seen: set[int] = set()
        stack: List[tuple[ItemLike, int]] = []
        roots = list(items)
        for t in reversed(roots):
            stack.append((t, 1))
        while stack:
            item, level = stack.pop()
            if self._detect_cycles:
                obj_id = id(item)
                if obj_id in seen:
                    lines.append(
                        self._formatter.format_line(item, level, self._indent_step)
                        + "  [cycle]"
                    )
                    continue
                seen.add(obj_id)
            lines.append(self._formatter.format_line(item, level, self._indent_step))
            subitems = getattr(item, "subitems", ()) or ()
            if subitems:
                for sub in reversed(list(subitems)):
                    stack.append((sub, level + 1))
        return self._newline.join(lines)


class TextTreeRenderer(TreeRenderer):
    def __init__(self, indent_step: int = 2) -> None:
        super().__init__(indent_step=indent_step, formatter=TextItemLineFormatter())


__all__ = ["TreeRenderer", "TextTreeRenderer"]
