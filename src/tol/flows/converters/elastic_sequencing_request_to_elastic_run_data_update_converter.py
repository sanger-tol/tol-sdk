# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from ...core import (
    DataObject,
    DataObjectToDataObjectOrUpdateConverter
)
from ...core.operator.updater import DataObjectUpdate


class ElasticSequencingRequestToElasticRunDataUpdateConverter(
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

    def convert(self, data_object: DataObject) -> Iterable[DataObjectUpdate]:
        to_ones = {}
        if 'sample' in data_object.to_one_relationships:
            sample = data_object.to_one_relationships['sample']
            if sample is not None:
                to_ones['sample'] = self._data_object_factory(
                    'sample',
                    sample.id
                )
        if 'extraction' in data_object.to_one_relationships:
            extraction = data_object.to_one_relationships['extraction']
            if extraction is not None:
                to_ones['extraction'] = self._data_object_factory(
                    'extraction',
                    extraction.id
                )
        if 'extraction_container' in data_object.to_one_relationships:
            extraction_container = \
                data_object.to_one_relationships['extraction_container']
            if extraction_container is not None:
                to_ones['extraction_container'] = self._data_object_factory(
                    'extraction_container',
                    extraction_container.id
                )
        yield (None, to_ones | {
            'sequencing_request.id': data_object.id})  # The candidate key
