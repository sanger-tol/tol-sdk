# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from more_itertools import peekable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class BufferingConverter(DataObjectToDataObjectOrUpdateConverter):
    """
    A converter that buffers objects until the next object with a different ID is seen, at which
    point it yields the buffered object.
    If the next object has the same ID, it merges the attributes of the two objects together.
    """

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert_iterable(self, inputs):
        it = peekable(inputs)
        for data_object in it:
            while True:
                try:
                    if it.peek().id == data_object.id:
                        data_object = self.__merge_objects(data_object, next(it))
                    else:
                        break
                except StopIteration:
                    break
            yield data_object

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        No actual converting is done
        """
        yield data_object

    def __merge_objects(self, obj1: DataObject, obj2: DataObject) -> DataObject:
        """
        Merges the attributes of two objects together, with the attributes of obj2 taking
        precedence over those of obj1. Deals with list attributes by concatenating them together.
        """
        if obj1.id != obj2.id:
            raise ValueError(f'Cannot merge objects with different IDs: {obj1.id} and {obj2.id}')

        merged = {}
        for key in obj1.attributes.keys() | obj2.attributes.keys():
            v1 = obj1.attributes.get(key)
            v2 = obj2.attributes.get(key)
            if isinstance(v1, list) and isinstance(v2, list):
                merged[key] = v1 + v2
            else:
                merged[key] = v2 if key in obj2.attributes else v1

        return self._data_object_factory(
            type_=obj1.type,
            id_=obj1.id,
            attributes=merged
        )
