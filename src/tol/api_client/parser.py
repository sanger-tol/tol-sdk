# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from collections.abc import Mapping
from typing import Any

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

        self.__factory = data_object_factory

    def convert(self, dump: JsonApiResource) -> DataObject:
        type_ = dump['type']
        id_ = dump.get('id')
        attributes = dump.get('attributes', {})
        to_one_objects = self.__get_to_one_objects(dump)

        return self.__factory(
            type_,
            id_,
            data=attributes | to_one_objects
        )

    def __get_to_one_objects(
        self,
        dump: JsonApiResource
    ) -> dict[str, DataObject]:

        relationships = dump.get('relationships', {})

        return {
            k: self.convert(v)
            for k, v in relationships.items()
            if self.__is_to_one(v)
        }

    def __is_to_one(self, relationship: Any) -> bool:
        return isinstance(relationship, Mapping)
