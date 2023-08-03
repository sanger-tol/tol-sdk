# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC

from ..api_base2.parser import JsonApiResource
from ..core.converter import Converter
from ..core import DataObject


class Dumper(Converter[DataObject, JsonApiResource], ABC):
    """
    Serializes `DataObject` instances to `JsonApiResource`
    dumps.
    """


RelationDict = dict[str, JsonApiResource]


class DefaultDumper(Dumper):
    def convert(self, data_object: DataObject) -> JsonApiResource:
        dump = {
            'type': data_object.type,
            'id': data_object.id
        }
        dump = self.__add_attributes(data_object, dump)
        dump = self.__add_one_relationships(data_object, dump)

        return dump

    def __add_attributes(
        self,
        data_object: DataObject,
        dump: JsonApiResource
    ) -> JsonApiResource:

        attributes = data_object.attributes
        if attributes:
            dump['attributes'] = attributes
        return dump

    def __add_one_relationships(
        self,
        data_object: DataObject,
        dump: JsonApiResource
    ) -> JsonApiResource:

        ones = data_object._to_one_objects
        if ones:
            dump['relationships'] = {
                k: self.__dump_one_relationship(v)
                for k, v in ones.items()
            }
        return dump

    def __dump_one_relationship(self, relation_object) -> RelationDict:
        return {
            'data': self.convert(relation_object)
        }
