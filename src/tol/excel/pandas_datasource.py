# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from dateutil import parser

import pandas as pd

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    core_data_object,
)
from ..core.operator import ListGetter


class PandasDataSource(
    DataSource,
    ListGetter,
    ABC
):
    """
    Emits `DataObject` instances from a tabular
    spreadsheet (e.g. `.xlsx`).
    """

    def __init__(
        self,
        filepath: str | Path,
        sheet_name: str,
        *,
        object_type: str = 'sheet_row',
        engine: str = 'openpyxl',
        type_mapping: dict[str, str] | None = None,
    ) -> None:

        super().__init__({})

        self._object_type = object_type

        self._mappings = self.__get_mappings(
            type_mapping,
        )

        self._df = self._get_dataframe(
            filepath,
            sheet_name,
            engine,
        )

        core_data_object(self)

    @property
    def supported_types(self) -> list[str]:
        return [self._object_type]

    def get_list(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Iterable[DataObject]:

        return (
            self.__marshal_row(row_index + 2, row)  # Add 1 for header, 1 for 1-based ID
            for row_index, row
            in self._df.iterrows()
        )

    def __marshal_row(
        self,
        row_index: int,
        row: pd.Series,
    ) -> DataObject:

        attributes = self.__format_attributes(row)

        return self.data_object_factory(
            self._object_type,
            id_=str(row_index),
            attributes=attributes,
        )

    def __format_attributes(
        self,
        row: pd.Series,
    ) -> dict[str, Any]:

        return {
            k: self.__format_attribute(k, v)
            for k, v in row.items()
        }

    def __format_attribute(
        self,
        __k: str,
        __v: Any,
    ) -> Any:

        # Convert pandas Timestamp to Python datetime
        if isinstance(__v, pd.Timestamp):
            __v = datetime.fromtimestamp(__v.timestamp())

        # If float and is whole number, convert to int
        if isinstance(__v, float) and __v.is_integer():
            __v = int(__v)

        if __k not in self._mappings:
            return __v

        type_ = self._mappings[__k]

        if type_ == datetime and not isinstance(__v, datetime):
            return parser.parse(__v)

        return type_(__v)

    def __get_mappings(
        self,
        type_mappings: dict[str, str] | None,
    ) -> dict[str, type]:

        if not type_mappings:
            return {}

        return {
            k: self.__get_mapping(v)
            for k, v in type_mappings.items()
        }

    def __get_mapping(self, __v: str) -> type:
        if __v == 'int':
            return int
        elif __v == 'str':
            return str
        elif __v == 'float':
            return float
        elif __v == 'datetime':
            return datetime
        elif __v == 'bool':
            return bool

        raise DataSourceError(title='Bad Mapping Value')

    @abstractmethod
    def _get_dataframe(
        self,
        filepath: str | Path,
        sheet_name: str,
        engine: str,
    ) -> pd.DataFrame:
        raise NotImplementedError
