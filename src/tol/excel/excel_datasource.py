# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import numpy as np

import pandas as pd

from ..core import (
    DataObject,
    DataSource,
    DataSourceError,
    core_data_object,
)
from ..core.operator import ListGetter


class ExcelDataSource(
    DataSource,
    ListGetter,
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

        self.__object_type = object_type

        self.__mappings = self.__get_mappings(
            type_mapping,
        )

        self.__df = self.__get_dataframe(
            filepath,
            sheet_name,
            engine,
        )

        core_data_object(self)

    @property
    def supported_types(self) -> list[str]:
        return [self.__object_type]

    def get_list(
        self,
        *args,
        **kwargs
    ) -> Iterable[DataObject]:

        return (
            self.__marshal_row(row_index + 1, row)
            for row_index, row
            in self.__df.iterrows()
        )

    def __get_dataframe(
        self,
        filepath: str | Path,
        sheet_name: str,
        engine: str,
    ) -> pd.DataFrame:

        __df: pd.DataFrame = pd.read_excel(
            filepath,
            sheet_name,
            engine=engine,
        )

        return __df.replace(np.nan, None)

    def __marshal_row(
        self,
        row_index: int,
        row: pd.Series,
    ) -> DataObject:

        attributes = self.__format_attributes(row)

        return self.data_object_factory(
            self.__object_type,
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

        if __k not in self.__mappings:
            return __v

        type_ = self.__mappings[__k]
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
