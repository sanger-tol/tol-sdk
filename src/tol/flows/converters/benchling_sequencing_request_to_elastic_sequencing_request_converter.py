# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)


class BenchlingSequencingRequestToElasticSequencingRequestConverter(
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
        if data_object.sts_id and data_object.id:
            extraction = None
            extraction_container = None
            tissue_prep = None
            if 'extraction_id' in data_object.attributes:
                extraction = self._data_object_factory(
                    'extraction',
                    data_object.extraction_id
                )
            if 'fluidx_container_id' in data_object.attributes:
                extraction_container = self._data_object_factory(
                    'extraction_container',
                    data_object.fluidx_container_id
                )
            if 'tissue_prep_id' in data_object.attributes:
                tissue_prep = self._data_object_factory(
                    'tissue_prep',
                    data_object.tissue_prep_id
                )
            ret = self._data_object_factory(
                'sequencing_request',
                data_object.id,
                attributes={
                    **{k: v
                       for k, v in data_object.attributes.items()
                       if k not in ['sanger_sample_id', 'sts_id',
                                    'specimen_id', 'taxon_id', 'extraction_id',
                                    'programme_id', 'tissue_prep_id', 'fluidx_container_id']}
                },
                to_one={
                    'sample': self._data_object_factory(
                        'sample',
                        data_object.sts_id
                    ) if data_object.sts_id is not None else None,
                    'specimen': self._data_object_factory(
                        'specimen',
                        data_object.specimen_id
                    ) if data_object.specimen_id is not None else None,
                    'species': self._data_object_factory(
                        'species',
                        data_object.taxon_id
                    ) if data_object.taxon_id is not None else None,
                    'tolid': self._data_object_factory(
                        'tolid',
                        data_object.programme_id
                    ) if data_object.programme_id is not None else None,
                    'extraction': extraction,
                    'extraction_container': extraction_container,
                    'tissue_prep': tissue_prep,
                })
            yield ret
