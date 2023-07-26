# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import typing
from abc import ABC

from ..core import Converter, DataObject, DataObjectFactory

if typing.TYPE_CHECKING:
    from .client import ObjectDump


class ObjectParser(Converter[ObjectDump, DataObject], ABC):
    """Converts object-dumps back to `DataObject` instances"""


class DefaultObjectParser(ObjectParser):
    def __init__(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:

        self.__data_object_factory = data_object_factory

    def convert(self, input_: ObjectDump) -> DataObject:
        return super().convert(input_)
