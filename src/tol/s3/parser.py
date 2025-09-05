# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Iterable

from minio.datatypes import Object as MinioObject

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


S3ApiResource = MinioObject
"""
The type of the response from S3 via minio
"""


class Parser(ABC):
    """
    Parses S3 API transfer resource `dict`s to `DataObject`
    instances
    """

    def parse_iterable(
        self,
        transfers: Iterable[S3ApiResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of S3 API transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: S3ApiResource) -> DataObject:
        """
        Parses an individual S3 transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):
    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(self, transfer: S3ApiResource) -> DataObject:
        # The name minio assigns to an S3 bucket response
        type_ = 'object'

        # Extract this object from the DataSource dict
        data_source = self.__get_data_source(type_)

        # Directly map each minio attribute to a DataSource attribute
        attributes = {
            'bucket_name': transfer.bucket_name,
            'last_modified': transfer.last_modified
        }

        # Construct and return the parsed DataSource using its factory
        return data_source.data_object_factory(
            type_,
            id_=transfer.object_name,
            attributes=attributes
        )

    def __get_data_source(self, type_: str) -> DataSource:
        return self.__dict[type_]
