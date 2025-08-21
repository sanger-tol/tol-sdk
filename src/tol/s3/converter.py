# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from minio.datatypes import Object as MinioObject

from .parser import Parser
from ..core import DataObject


S3ApiObject = MinioObject
S3ApiTransfer = Iterable[S3ApiObject]


class S3ApiConverter():
    """
    Converts from S3 API transfers to instances of
    `DataObject`.
    """

    def __init__(
        self,
        parser: Parser
    ) -> None:
        self.__parser = parser

    def convert(self, input_: S3ApiObject) -> DataObject:
        """
        Converts a single S3ApiObject to a DataObject
        """
        return self.__parser.parse(input_)

    def convert_list(
        self,
        input_: S3ApiTransfer
    ) -> Iterable[DataObject]:
        """
        Converts an S3 ApiTransfer containing a list of results
        """
        # S3 buckets can be quite big, so we want to make sure that
        # we're staying in generator land
        for obj in input_:
            yield self.__parser.parse(obj)
