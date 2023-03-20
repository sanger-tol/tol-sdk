# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Tuple

from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter


DataId = str
DataObject = Dict[str, Any]
DataSourceUpdate = Tuple[DataId, DataObject]
DataSourceConfig = Dict[str, Any]


class UnsupportedOperationException(NotImplementedError):
    def __init__(self, obj: DataSource, method: Callable):
        super().__init__(
            f'The operation {method.__name__} is '
            f'unsupported on {obj.__class__.__name__}.'
        )


def unsupported(method: Callable) -> Callable:
    """
    Indicates that an abstract operation on ABC DataSource is
    unsupported on the inherited class and will raise an
    UnsupportedOperationException if called.
    """
    method._unsupported = True

    @wraps(method)
    def wrapper(obj: DataSource, *args, **kwargs) -> None:
        raise UnsupportedOperationException(
            obj,
            method
        )
    return wrapper


class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources
    """

    DEFAULT_PAGE_SIZE = 20

    __OPERATIONS = [
        'get_by_id',
        'get_list_page'
    ]

    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    def supported_operations(self) -> List[str]:
        return [
            operation for operation in self.__OPERATIONS
            if self.__operation_is_supported(operation)
        ]

    def __operation_is_supported(self, name) -> bool:
        operation = getattr(self, name)
        return (
            hasattr(operation, '_unsupported')
            and operation._unsupported is True
        ) is False

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
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ):
        """
        Gets a List of DataObjet instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable.
        """

    @abstractmethod
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        **kwargs
    ):
        """
        Gets a page of DataObject instances, of specified object_type, of
        the given page_size and page_number (starting from 1).
        """

    def get_page_size(self) -> int:
        if hasattr(self, 'page_size'):
            return self.page_size
        else:
            return self.DEFAULT_PAGE_SIZE
