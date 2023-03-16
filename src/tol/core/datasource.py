# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, List, Tuple

from .datasource_error import DataSourceError


DataId = str
DataObject = Dict[str, Any]
DataSourceUpdate = Tuple[DataId, DataObject]
DataSourceConfig = Dict[str, Any]


class UnsupportedMethodException(NotImplementedError):
    def __init__(self, obj: DataSource, method: Callable):
        super().__init__(
            f'The method {method.__name__} is '
            f'unsupported on {obj.__name__}.'
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
    def get_by_id(self, object_type: str, id_: str, **kwargs):
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
