# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class MlwhRunDataToElasticRunDataConverter(
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

        attributes = {
            k: v
            for k, v in data_object.attributes.items()
            if k not in ['supplier_name', 'taxon_id', 'sample_ref', 'tolid', 'study_id']
        }
        to_one_relations = {
            'specimen': self._data_object_factory(
                'specimen',
                data_object.supplier_name),
            'species': self._data_object_factory(
                'species',
                str(data_object.taxon_id)
            ),
            'sequencing_request': self._data_object_factory(
                'sequencing_request',
                data_object.sample_ref
            ),
            'tolid': self._data_object_factory(
                'tolid',
                data_object.tolid
            ),
            'study': self._data_object_factory(
                'study',
                str(data_object.study_id)
            )
        }
        ret = self._data_object_factory(
            'run_data',
            data_object.id,
            attributes=attributes,
            to_one=to_one_relations
        )
        yield ret
