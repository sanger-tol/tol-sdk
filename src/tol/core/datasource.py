# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from .data_object import DataDict
from .datasource_error import DataSourceError, NoDataObjectFactoryError
from .factory import DataObjectFactory
from .operator import Operator


DataId = str
DataSourceUpdate = Tuple[DataId, DataDict]
DataSourceConfig = Dict[str, Any]


class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources.
    """

    DEFAULT_PAGE_SIZE = 20

    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__data_object_factory: Optional[DataObjectFactory] = None
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        """
        The list of types of DataObject supported by this DataSource instance.

        This can either be a static list, or dynamically generated.
        """

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

    def get_page_size(self) -> int:
        return getattr(self, 'page_size', self.DEFAULT_PAGE_SIZE)

    @abstractmethod
    def get_attribute_types(self, object_type: str) -> Dict:
        """
        The types (str, int, etc) of the attributes of an object_type.

        This can either be a static list, or dynamically generated.
        """

    @property
    def data_object_factory(self) -> Optional[DataObjectFactory]:
        """A callable that returns a new DataObject for the given type."""

        if self.__data_object_factory is None:
            raise NoDataObjectFactoryError(
                'The `data_object_factory` setter must be called before a '
                'DataSource instance can be used. The standard way to do '
                'this is to collect all of the DataSource instances, and '
                'provide them to the `core_data_object` function.'
            )

        return self.__data_object_factory

    @data_object_factory.setter
    def data_object_factory(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:
        """Sets the factory for creating new DataObject instances"""

        self.__data_object_factory = data_object_factory


OperableDataSource = TypeVar(
    'OperableDataSource',
    DataSource,
    Operator
)
"""A type hint. For inheriting, use DataSource"""
