# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class IncomingGenomeNoteToGenomeNoteJsonConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        destination_type: str = 'genome_note'
        wrapped_data_key: str = 'data'
        wrapped_properties_key: str = 'properties'

    __schema_top_level_keys = (
        'metadata',
        'software_tools',
        'references',
        'methods',
        'assembly_stats',
        'reviewer_reports',
        'publication_metadata'
    )

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        attributes = dict(data_object.attributes)
        payload = self.__extract_payload(attributes)

        if not isinstance(payload, dict):
            raise ValueError('JsonConverter expects payload to be a JSON object')

        output_attributes = {
            key: payload.get(key)
            for key in self.__schema_top_level_keys
            if key in payload
        }

        taxonomy_id = None
        assembly_stats = payload.get('assembly_stats', {})
        if isinstance(assembly_stats, dict):
            species = assembly_stats.get('species')
            if isinstance(species, list) and species:
                first_species = species[0]
                if isinstance(first_species, dict):
                    taxonomy_id = first_species.get('ncbi_taxonomy_id')
        if not taxonomy_id:
            raise ValueError(
                'Missing taxonomy id (assembly_stats.species[0].ncbi_taxonomy_id) in input payload'
            )

        yield self._data_object_factory(
            self.__config.destination_type,
            taxonomy_id,
            attributes=output_attributes,
        )

    def __extract_payload(self, attributes: dict[str, Any]) -> dict[str, Any]:
        if self.__config.wrapped_data_key in attributes:
            wrapped = attributes.get(self.__config.wrapped_data_key)
            if not isinstance(wrapped, dict):
                raise ValueError(
                    f'Expected "{self.__config.wrapped_data_key}" to contain a JSON object'
                )
            if self.__config.wrapped_properties_key in wrapped:
                properties = wrapped.get(self.__config.wrapped_properties_key)
                if not isinstance(properties, dict):
                    raise ValueError(
                        f'Expected "{self.__config.wrapped_properties_key}" '
                        'to contain a JSON object'
                    )
                return properties
            return wrapped
        return attributes
