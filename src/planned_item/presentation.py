# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import datetime
from typing import Dict, List, Tuple

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.model import PlannedItem, PlannedItemGroup
from src.planned_item.display.renderers import TextTreeRenderer

params = ParameterLoader()
today: datetime.date = params.get("TODAY")


def print_grouped_items(
    all_groups: Dict[PlannedItemGroup, Tuple[Period, List[PlannedItem]]],
    renderer: TextTreeRenderer,
    is_valid_group_func,
) -> None:
    first_group = True
    for group, (period, group_items) in all_groups.items():
        if not is_valid_group_func(group, period, group_items):
            continue
        if not first_group:
            print()
        else:
            first_group = False
        print(f"=== {group.label} ===")
        if group == PlannedItemGroup.DUED:
            print(f"Before {today}")
        elif group == PlannedItemGroup.FUTURE:
            print(f"Starting from {period.start}")
        elif group not in [PlannedItemGroup.ON_GOING]:
            name: str = "Date"
            if period.duration > 1:
                name = "Period"
            if (
                group
                in [
                    PlannedItemGroup.TODAY,
                    PlannedItemGroup.TOMORROW,
                    PlannedItemGroup.THIS_FRIDAY,
                    PlannedItemGroup.THIS_SUNDAY,
                ]
                and period.start == period.end
            ):
                print(f"{name}: {period.start}")
            elif group in [
                PlannedItemGroup.REST_OF_THIS_WEEK,
                PlannedItemGroup.THIS_WEEKEND,
                PlannedItemGroup.NEXT_WEEK,
                PlannedItemGroup.REST_OF_THIS_MONTH,
                PlannedItemGroup.NEXT_MONTH,
            ]:
                print(f"{name}: {period.start} → {period.end}")
        print(renderer.render(group_items))
