# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations


class ItemTypeError(ValueError): ...


class ItemStatusError(ValueError): ...


class DataSourceError(ValueError): ...


PlannedItemTypeError = ItemTypeError
PlannedItemStatusError = ItemStatusError
PlannedItemDataSourceError = DataSourceError
