# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import wraps
from typing import Any, Callable

from ..core import DataSourceError

if typing.TYPE_CHECKING:
    from .api_datasource import ApiDataSource


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


def validate(operation_name: str):
    """
    Performs several pre-flight checks:

    - the operation on `ApiDataSource` is supported
    """

    def decorator(operation: Callable) -> Callable:

        @wraps(operation)
        def wrapper(
            ds: ApiDataSource,
            object_type: str,
            *args,
            **kwargs
        ) -> Any:

            _validate_type_supported(ds, object_type)
            _validate_operation(ds, object_type, operation_name)

            return operation(ds, object_type, *args, **kwargs)

        return wrapper

    return decorator
