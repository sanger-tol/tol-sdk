# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any

from ..core import Converter, DataObject, DataObjectFactory


ObjectDump = dict[str, Any]


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
