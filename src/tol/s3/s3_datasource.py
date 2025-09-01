# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Callable, Iterable, Optional

from more_itertools import seekable

from ..services.s3_client import S3Client
from .converter import (
    S3ApiConverter
)
from ..core import (
    DataObject,
    DataSource,
)
from ..core.operator import (
    ListGetter
)

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession

ClientFactory = Callable[[], S3Client]
S3ConverterFactory = Callable[[], S3ApiConverter]


class S3DataSource(
    DataSource,

    # the supported operators
    ListGetter,
):
    """
    A `DataSource` that connects to a remote S3 API.

    Developers should likely use `create_s3_datasource`
    instead of this directly.
    """

    def __init__(
        self,
        client_factory: ClientFactory,
        s3_converter_factory: S3ConverterFactory,
    ) -> None:

        self.__client_factory = client_factory
        self.__gc_factory = s3_converter_factory
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
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        objects = self.__client_factory().list_objects(self.bucket_name)
        converted_objects = self.__gc_factory().convert_list(objects)
        return converted_objects
