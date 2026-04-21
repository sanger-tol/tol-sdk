# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingTissuePrepToElasticTissuePrepConverter(
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
        ret = self._data_object_factory(
            'tissue_prep',
            data_object.id,
            attributes={
                **{k: v
                   for k, v in data_object.attributes.items()
                   if k not in ['sts_id',
                                'taxon_id',
                                'programme_id']}
            },
            to_one={
                'sample': self._data_object_factory(
                    'sample',
                    data_object.sts_id
                ) if data_object.sts_id is not None else None,
                'species': self._data_object_factory(
                    'species',
                    data_object.taxon_id
                ) if data_object.taxon_id is not None else None,
                'tolid': self._data_object_factory(
                    'tolid',
                    data_object.programme_id
                ) if data_object.programme_id is not None else None,
            }
        )
        return iter([ret])
