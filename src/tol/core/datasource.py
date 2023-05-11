# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type

from .data_object import DataDict, DataObject
from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter


DataId = str
DataSourceUpdate = Tuple[DataId, DataDict]
DataSourceConfig = Dict[str, Any]


class BadUnsupportedUsageException(Exception):
    def __init__(self):
        super().__init__(
            '@unsupported() has been used improperly. When '
            'specifying an optional message, it must be '
            'specified as a keyword argument, e.g. '
            "@unsupported(message='example')"
        )


class UnsupportedOperationException(NotImplementedError):
    def __init__(
        self,
        data_source: DataSource,
        object_type: str,
        method: Callable,
        message: Optional[str] = None
    ):
        rendered_message = self.__render_message(
            data_source,
            object_type,
            method,
            message
        )
        super().__init__(rendered_message)

    def __render_message(
        self,
        obj: DataSource,
        object_type: str,
        method: Callable,
        message: str
    ) -> str:
        auto_message = (
            f'The operation {method.__name__} is unsupported '
            f'for objects of type {object_type} (on '
            f'{obj.__class__.__name__}).'
        )
        if message is None:
            return auto_message
        else:
            return f'{auto_message}\n\n{message}'


def unsupported(
    operation=None,
    *,
    message: str = None
) -> Callable:
    """
    Indicates that an abstract operation on ABC DataSource is
    unsupported on the inherited class and will raise an
    UnsupportedOperationException if called.

    This decorator can be used with (or without) parentheses
    after, in the former, an optional message may be provided to
    any UnsupportedOperationException resulting from an
    operation invocation. This message MUST be specified as a
    keyword argument!

    Usage:

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    or (to raise an exception with a custom message)

    @unsupported(message='This DataSource is readonly.')
    def upsert(self, *args, **kwargs):
        pass
    """

    def decorator(function: Callable) -> Callable:
        @wraps(function)
        def wrapper(data_source: DataSource, object_type: str, *args, **kwargs) -> None:
            raise UnsupportedOperationException(
                data_source,
                object_type,
                function,
                message=message
            )
        wrapper._unsupported = True
        return wrapper

    if isinstance(operation, str):
        # the user gave message as an arg, not kwarg
        raise BadUnsupportedUsageException()

    if operation is not None:
        return decorator(operation)

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


def setup_operations(ds_class: Type[DataSource]) -> Type[DataSource]:

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
    """

    DEFAULT_PAGE_SIZE = 20
    _operations: List[str]

    def __init__(self, config: DataSourceConfig, expected: List[str] = None):
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    def supported_operations(self) -> List[str]:
        """
        The list of operations (e.g. get_by_id) supported by a DataSource instance.
        """
        return [
            operation for operation in self._operations
            if self.__operation_is_supported(operation)
        ]

    @abstractproperty
    def supported_types(self) -> List[str]:
        """
        The list of types of DataObject supported by this DataSource instance.

        This can either be a static list, or dynamically generated.
        """

    def __operation_is_supported(self, name) -> bool:
        operation = getattr(self, name)
        return getattr(operation, '_unsupported', False) is not True

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
    ) -> Iterable[Optional[DataObject]]:
        """
        Gets an Iterable of DataObject instances, of specified object_type,
        with their id's equal to those given in the object_ids Iterable (or
        None if the id at that position is not found).
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

    def get_page_size(self) -> int:
        return getattr(self, 'page_size', self.DEFAULT_PAGE_SIZE)

    @abstractmethod
    def get_attribute_types(self, object_type: str) -> Dict:
        """
        The types (str, int, etc) of the attributes of an object_type.

        This can either be a static list, or dynamically generated.
        """


class ReadOnlyDataSource(DataSource, ABC):
    """
    A DataSource that supports only get operations
    """
