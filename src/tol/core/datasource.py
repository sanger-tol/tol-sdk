# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Tuple

from .data_object import DataDict, DataObject
from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter
from .datasource_session import DataSourceSession


DataId = str
DataSourceUpdate = Tuple[DataId, DataDict]
DataSourceConfig = Dict[str, Any]


class UnsupportedOperationException(NotImplementedError):
    def __init__(
        self,
        obj: DataSource,
        method: Callable,
        message: str = None
    ):
        rendered_message = self.__render_message(
            obj,
            method,
            message
        )
        super().__init__(rendered_message)

    def __render_message(
        self,
        obj: DataSource,
        method: Callable,
        message: str
    ) -> str:
        auto_message = (
            f'The operation {method.__name__} '
            f'is unsupported on {obj.__class__.__name__}.'
        )
        if message is None:
            return auto_message
        else:
            return f'{auto_message}\n\n{message}'


def unsupported(message: str = None) -> Callable:
    """
    Indicates that an abstract operation on ABC DataSource is
    unsupported on the inherited class and will raise an
    UnsupportedOperationException if called.

    This decorator must be used with parentheses after,
    in which an optional message may be provided to
    any UnsupportedOperationException resulting from an
    operation invocation.

    Usage:

    @unsupported()
    def get_by_id(self, *args, **kwargs):
        pass

    or (to raise an exception with a custom message)

    @unsupported(message='This DataSource is readonly.')
    def upsert(self, *args, **kwargs):
        pass
    """

    def decorator(operation: Callable) -> Callable:
        @wraps(operation)
        def wrapper(obj: DataSource, *args, **kwargs) -> None:
            raise UnsupportedOperationException(
                obj,
                operation,
                message=message
            )
        wrapper._unsupported = True
        return wrapper
    return decorator


def operation(method: Callable) -> Callable:
    """
    Indicates a central operation on a DataSource. Only to be used
    on the base DataSource, for operations common to all (or
    unsupported)
    """

    @wraps(method)
    @abstractmethod
    def wrapper(obj: DataSource, *args, **kwargs) -> None:
        return method(obj, *args, **kwargs)

    wrapper._operation = True
    return wrapper


def setup_operations(ds_class: DataSource) -> DataSource:

    def __member_is_operation(member: Any) -> bool:
        return getattr(member, '_operation', False) is True

    members = {
        m: v
        for m, v in vars(ds_class).items()
        if not m.startswith('_')
    }
    ds_class._operations = [
        m for m, v in members.items()
        if __member_is_operation(v)
    ]
    return ds_class


@setup_operations
class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources.

    All operations called directly on a DataSource instance will be executed
    immediately.

    To batch calls, use the session() method.
    """

    DEFAULT_PAGE_SIZE = 20

    _operations: List[str]

    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    def supported_operations(self) -> List[str]:
        return [
            operation for operation in self._operations
            if self.__operation_is_supported(operation)
        ]

    def session(
        self,
        multi_type: bool = False
    ) -> DataSourceSession:
        """
        Returns a DataSourceSession object for batching upserts.

        Parameters:
        - multi_type - whether to call mutli_type_upsert once, or
                       call upsert for each iterable of each
                       object_type
        """
        return DataSourceSession(self, multi_type)

    def __operation_is_supported(self, name) -> bool:
        operation = getattr(self, name)
        return getattr(operation, '_unsupported', False) is False

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

    @operation
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> Iterable[DataObject]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable.
        """

    @operation
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:
        """
        For a specified object_type, of the given page_size
        and page_number (starting from 1), returns a tuple of:

        - An Iterable of DataObject instances
        - The total number of DataObjects that matches the filter
        """

    @operation
    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[DataObject]:
        """
        Gets a generator of DataObject instances
        """

    @operation
    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        **kwargs
    ) -> None:
        """
        Takes an iterable of DataObjects of the same object_type,
        and for each, performs either:

        - an insert (if they don't exist already)
        - an update (if they do)
        """

    @operation
    def multi_type_upsert(
        self,
        objects: Iterable[DataObject],
        **kwargs
    ) -> None:
        """
        Takes an iterable of DataObjects of any (and mixed) object_type,
        and for each, performs either:

        - an insert (if they don't exist already)
        - an update (if they do)
        """

    def get_page_size(self) -> int:
        return getattr(self, 'page_size', self.DEFAULT_PAGE_SIZE)


class ReadOnlyDataSource(DataSource, ABC):
    """
    A DataSource that supports only get operations
    """

    @unsupported('This DataSource is readonly.')
    def upsert(self, object_type: str, *args, **kwargs) -> None:
        pass

    @unsupported('This DataSource is readonly.')
    def multi_type_upsert(self, *args, **kwargs) -> None:
        pass
