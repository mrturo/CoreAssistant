# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import datetime
from typing import Dict, List, Tuple

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.model import PlannedItem, PlannedItemGroup
from src.model.validation import is_valid_group
from src.planned_item.display.renderers import TextTreeRenderer
from src.planned_item.presentation import print_grouped_items

params = ParameterLoader()
today: datetime.date = params.get("TODAY")


class ConsolePresenter:
    def __init__(self, indent_step: int = 2) -> None:
        self.renderer = TextTreeRenderer(indent_step=indent_step)

    def print_planned_items(
        self, all_groups: Dict[PlannedItemGroup, Tuple[Period, List[PlannedItem]]]
    ) -> None:
        print_grouped_items(all_groups, self.renderer, is_valid_group)
