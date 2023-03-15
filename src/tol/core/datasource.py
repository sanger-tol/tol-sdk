# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter


DataId = str
DataObject = Dict[str, Any]
DataSourceUpdate = Tuple[DataId, DataObject]
DataSourceConfig = Dict[str, Any]


class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources
    """
    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    def __validate_config(
        self,
        config: DataSourceConfig,
        expected: List[str]
    ):
        if expected is None:
            return
        for k in expected:
            if k not in config:
                raise DataSourceError(
                    title='Incorrect configuration',
                    detail=f'{k} missing in config dict'
                )

    @abstractmethod
    def get_list_page(
        self,
        object_type: str,
        page: int,
        data_filter: DataSourceFilter = None,
        **kwargs
    ) -> List[DataObject]:
        """
        Gets a page of results. Supports filtering by adding
        a DataSourceFilter filter keyword argument.
        """


class ReadOnlyError(Exception):
    def __init__(self, data_source: DataSource):
        super().__init__(
            f'The DataSource {data_source.__name__} is read-only.'
        )
