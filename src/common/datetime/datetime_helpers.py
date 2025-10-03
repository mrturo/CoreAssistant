# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Any, Mapping, Optional

from src.common.data.utilities import is_event, is_true
from src.common.datetime.date_converter import DateConverter
from src.common.datetime.formatting_types import EndContext, StartContext


def start_context_from_kwargs(kwargs: Mapping[str, Any]) -> StartContext:
    return StartContext(
        is_all_day=kwargs.get("is_all_day"),
        calendar_days=kwargs.get("calendar_days"),
        is_today_or_tomorrow=kwargs.get("is_today_or_tomorrow"),
        is_on_going=kwargs.get("is_on_going"),
        item_type=kwargs.get("item_type"),
    )


def end_context_from_kwargs(kwargs: Mapping[str, Any]) -> EndContext:
    return EndContext(
        is_all_day=kwargs.get("is_all_day"),
        calendar_days=kwargs.get("calendar_days"),
    )


def human_start(
    start_rfc3339: Optional[str],
    tz: Optional[str] = None,
    **kwargs: Any,
) -> Optional[str]:
    converter = DateConverter(tz)
    context = start_context_from_kwargs(kwargs)
    return converter.convert_start(start_rfc3339=start_rfc3339, context=context)


def human_end(
    end_rfc3339: Optional[str],
    tz: Optional[str] = None,
    **kwargs: Any,
) -> str:
    converter = DateConverter(tz)
    context = end_context_from_kwargs(kwargs)
    return converter.convert_end(end_rfc3339=end_rfc3339, context=context)


__all__ = [
    "start_context_from_kwargs",
    "end_context_from_kwargs",
    "human_start",
    "human_end",
    "is_true",
    "is_event",
]
