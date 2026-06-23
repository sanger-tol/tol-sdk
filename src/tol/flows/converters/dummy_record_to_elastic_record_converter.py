# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class DummyRecordToElasticRecordConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        if data_object.id is None:
            return
        to_cat = data_object.to_one_relationships.get('category')
        to_sub = data_object.to_one_relationships.get('sub_category')

        to_one = {
            'category': (
                self._data_object_factory(type_='category', id_=to_cat.id)
                if to_cat is not None and to_cat.id is not None else None
            ),
            'sub_category': (
                self._data_object_factory(type_='category', id_=to_sub.id)
                if to_sub is not None and to_sub.id is not None else None
            ),
        }

        ret = self._data_object_factory(
            type_='record',
            id_=str(data_object.id),
            attributes=dict(data_object.attributes),
            to_one=to_one,
        )

        yield ret
