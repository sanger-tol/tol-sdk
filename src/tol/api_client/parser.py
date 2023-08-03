# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC

from .dumper import RelationDict
from ..api_base2.parser import JsonApiResource
from ..core.converter import Converter
from ..core import DataObject, DataObjectFactory


class Parser(Converter[JsonApiResource, DataObject], ABC):
    """
    Deserializes `DataObject` instances from `JsonApiResource`
    dumps.
    """


class DefaultParser(Parser):
    def __init__(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:
        super().__init__()

    def convert(self, dump: JsonApiResource) -> DataObject:
        return super().convert(dump)
