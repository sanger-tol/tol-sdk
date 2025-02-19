# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import wraps
from typing import Any, Callable, Union

from ..core import DataObject, DataSourceError

if typing.TYPE_CHECKING:
    from .api_datasource import ApiDataSource


def _get_object_type(
    object_or_type: Union[str, DataObject],
    direct_object: bool
) -> str:
    """
    Gets the `object_type` either:

    - as directly given (if not `direct_object`)
    - from the `.type` (if `direct_object`)
    """

    return (
        object_or_type.type if direct_object
        else object_or_type
    )


def _validate_type_supported(
    ds: ApiDataSource,
    object_type: str
) -> None:

    if object_type not in ds.supported_types:
        detail = (
            f'The type "{object_type}" is unrecognised.'
        )

        raise DataSourceError(
            title='Unknown Type',
            detail=detail,
            status_code=400
        )


def _validate_operation(
    ds: ApiDataSource,
    object_type: str,
    operation_name: str
) -> None:

    supported_operations = ds.supported_operations.get(
        object_type,
        []
    )

    if operation_name not in supported_operations:
        detail = (
            f'The operation {operation_name} is '
            f'unsupported on {object_type}.'
        )
        raise DataSourceError(
            'Unsupported Operation',
            detail,
            400
        )


def validate(
    operation_name: str,
    direct_object: bool = False,
):
    """
    Performs several pre-flight checks:

    - the operation on `ApiDataSource` is supported
    - the `data_object` type is supported

    Set `direct_object` to `True` if the operation
    gives an instance of `DataObject` as its first
    arg.
    """

    def decorator(operation: Callable) -> Callable:

        @wraps(operation)
        def wrapper(
            ds: ApiDataSource,
            data_object_or_type: Union[DataObject, str],
            *args,
            **kwargs
        ) -> Any:

            object_type = _get_object_type(data_object_or_type, direct_object)

            _validate_type_supported(ds, object_type)
            _validate_operation(ds, object_type, operation_name)

            return operation(ds, data_object_or_type, *args, **kwargs)

        return wrapper

    return decorator


def _check_id_is_not_none(source: DataObject) -> None:
    if source.id is None:
        raise DataSourceError(
            title='Unset Source ID',
            detail='The given object has no value set for its ID.',
            status_code=400
        )


def validate_id(operation: Callable) -> Callable:
    """
    Validates that the given instance of `DataObject`
    has a non-`None` ID.
    """

    @wraps(operation)
    def wrapper(
        ds: ApiDataSource,
        source: DataObject,
        *args,
        **kwargs
    ) -> Any:

        _check_id_is_not_none(source)

        return operation(ds, source, *args, **kwargs)

    return wrapper
