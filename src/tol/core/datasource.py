# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, List, Tuple

from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter


DataId = str
DataObject = Dict[str, Any]
DataSourceUpdate = Tuple[DataId, DataObject]
DataSourceConfig = Dict[str, Any]


class UnsupportedMethodException(NotImplementedError):
    def __init__(self, obj: DataSource, method: Callable):
        super().__init__(
            f'The method {method.__name__} is '
            f'unsupported on {obj.__class__.__name__}.'
        )


def unsupported(method: Callable) -> Callable:
    """
    Indicates that an abstract method on ABC DataSource is
    unsupported on the decorated inherited class's method.
    """
    method._unsupported = True

    @wraps(method)
    def wrapper(obj: DataSource, *args, **kwargs) -> None:
        raise UnsupportedMethodException(
            obj,
            method
        )
    return wrapper


class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources
    """

    DEFAULT_PAGE_SIZE = 20

    __METHODS = [
        'get_by_id',
        'get_list_page'
    ]

    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    def supported_methods(self) -> List[str]:
        return [
            method_name for method_name in self.__METHODS
            if self.__method_is_supported(method_name)
        ]

    def __method_is_supported(self, method_name) -> bool:
        method = getattr(self, method_name)
        return (
            hasattr(method, '_unsupported') and
            method._unsupported == True
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
    def get_by_id(self, object_type: str, id_: str, **kwargs):
        pass

    @abstractmethod
    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        **kwargs
    ):
        pass

    def get_page_size(self) -> int:
        if hasattr(self, 'page_size'):
            return self.page_size
        else:
            return self.DEFAULT_PAGE_SIZE


class ReadOnlyError(Exception):
    def __init__(self, data_source: DataSource):
        super().__init__(
            f'The DataSource {data_source.__name__} is read-only.'
        )
