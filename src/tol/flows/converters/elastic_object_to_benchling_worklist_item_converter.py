# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from .benchling_entity_to_benchling_worklist_item_converter_factory import (
    BenchlingEntityToBenchlingWorklistItemConverterFactory
)
from .elastic_sample_to_benchling_tissue_converter import ElasticSampleToBenchlingTissueConverter
from ...core import (
    ChainedConverter,
    DataObject,
    DataObjectToDataObjectOrUpdateConverter,
    DefaultDataObjectToDataObjectConverter,
)

_OBJECT_TYPE_MAPPING = {
    'sample': 'tissue',
    'extraction': 'dna_extract',
    'extraction_container': 'tube',
}


class ElasticObjectToBenchlingWorklistItemConverter(
        DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        object_type: str
        worklist: object  # DataObject — kept as `object` to avoid circular imports

    _config: Config

    def __init__(self, data_object_factory, config: Config):
        super().__init__(data_object_factory)
        self._config = config
        self._chain = self._build_chain(data_object_factory)

    @property
    def config(self) -> Config:
        return self._config

    def _build_chain(self, data_object_factory) -> ChainedConverter:
        object_type = self._config.object_type
        worklist = self._config.worklist
        destination_object_type = _OBJECT_TYPE_MAPPING.get(object_type, object_type)

        converters = []

        if worklist.worklist_type == 'bioentity' or object_type == 'extraction_container':
            if object_type == 'sample':
                converters.append(
                    ElasticSampleToBenchlingTissueConverter(
                        data_object_factory,
                        config=ElasticSampleToBenchlingTissueConverter.Config()
                    )
                )
            else:
                converters.append(
                    DefaultDataObjectToDataObjectConverter(
                        data_object_factory,
                        config=DefaultDataObjectToDataObjectConverter.Config(
                            destination_object_type=destination_object_type
                        )
                    )
                )
        elif worklist.worklist_type == 'container':
            converters.append(
                DefaultDataObjectToDataObjectConverter(
                    data_object_factory,
                    config=DefaultDataObjectToDataObjectConverter.Config(
                        destination_object_type='tube',
                        id_field='benchling_fluidx_container_id'
                    )
                )
            )

        converter_class = (
            BenchlingEntityToBenchlingWorklistItemConverterFactory(worklist)
            .get_converter_class()
        )
        converters.append(converter_class(data_object_factory, config=converter_class.Config()))

        return ChainedConverter(*converters)

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        return self._chain.convert_iterable([data_object])
