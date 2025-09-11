# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, Optional

from .converter import (
    S3Converter
)
from ..core import (
    DataObject,
    DataSource,
)
from ..core.operator import (
    ListGetter
)
from ..services.s3_client import S3Client

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession
    from ..core.datasource_filter import DataSourceFilter

ClientFactory = Callable[[], S3Client]
S3ConverterFactory = Callable[[], S3Converter]


class S3DataSource(
    DataSource,

    # the supported operators
    ListGetter,
):
    """
    A `DataSource` that connects to a remote S3.

    Developers should likely use `create_s3_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        s3_converter_factory: S3ConverterFactory,
        bucket_name: str,
        prefix: str
    ) -> None:

        self.__client_factory = client_factory
        self.__gc_factory = s3_converter_factory
        self.bucket_name = bucket_name
        self.prefix = prefix
        super().__init__({})

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'object': {
                'bucket_name': 'str',
                'last_modified': 'datetime'
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(
            self.attribute_types.keys()
        )

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None
    ) -> Iterable[DataObject]:
        client = self.__client_factory()
        objects = client.list_objects(self.bucket_name, self.prefix)
        converted_objects = self.__gc_factory().convert_list(objects)
        return converted_objects
