# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from .data_object import DataObject


class DataSourceError(Exception):
    """Raise to indicate that an error has occured with a DataSource."""

    def __init__(self, title: str = None, detail: str = None,
                 status_code: int = 500):
        self.title = title
        self.detail = detail
        self.status_code = status_code

    def __str__(self) -> str:
        return f'{self.title} - "{self.detail}"'


class UnknownObjectTypeException(DataSourceError):
    def __init__(self, object_type: str) -> None:
        super().__init__(
            title='Unknown Object Type',
            detail=f'The object type "{object_type}" is unknown.',
            status_code=404
        )


class NoDataObjectFactoryError(DataSourceError):
    def __init__(self, detail: str) -> None:
        super().__init__(
            'DataSource Configuration error',
            detail,
            status_code=500
        )


class NotRelationalError(DataSourceError):
    """
    Raised when trying to load exceptions on a DataObject hosted
    by a DataSource that does not implement Relational.
    """

    def __init__(self, source: DataObject) -> None:
        ds_name = type(source._host).__name__
        message = (
            f'The type "{source.type}" is hosted by a DataSource '
            f'({ds_name}) that does not support relationships.'
        )
        super().__init__(
            'DataSource Not Relational',
            message,
            status_code=500
        )
