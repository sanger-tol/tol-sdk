# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any, Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class JsonConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        destination_type: str = 'genome_note'
        wrapped_data_key: str = 'data'
        strict_missing_relation_fields: bool = False

    __schema_top_level_keys = (
        'metadata',
        'software_tools',
        'references',
        'methods',
        'assembly_stats',
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

        # Keep the DataObject attributes aligned with the schema top-level keys.
        output_attributes = {
            key: payload.get(key)
            for key in self.__schema_top_level_keys
            if key in payload
        }

        assembly_accession = self.__first_non_empty(
            self.__get_nested(payload, 'assembly_stats', 'sequence_report', 'assembly_accession'),
            attributes.get('assembly_accession'),
        )
        taxid = self.__first_non_empty(
            self.__extract_first_species_taxid(payload),
            attributes.get('taxid'),
        )
        tolid = self.__first_non_empty(
            self.__extract_first_sample_tolid(payload),
            attributes.get('tolid'),
        )

        missing = []
        if not assembly_accession:
            missing.append('assembly_accession')
        if not taxid:
            missing.append('taxid')
        if not tolid:
            missing.append('tolid')

        if self.__config.strict_missing_relation_fields and missing:
            raise ValueError(
                f'Missing required Genome Notes relation field(s): {", ".join(missing)}'
            )

        if assembly_accession is not None:
            output_attributes['assembly_accession'] = assembly_accession
        if taxid is not None:
            output_attributes['taxid'] = taxid
        if tolid is not None:
            output_attributes['tolid'] = tolid

        output_id = self.__first_non_empty(
            self.__get_nested(payload, 'metadata', 'doi'),
            assembly_accession,
            self.__get_nested(payload, 'metadata', 'title'),
            data_object.id,
        )
        if output_id is None:
            raise ValueError('Unable to determine output id for JsonConverter')

        yield self._data_object_factory(
            self.__config.destination_type,
            str(output_id),
            attributes=output_attributes,
        )

    def __extract_payload(self, attributes: dict[str, Any]) -> dict[str, Any]:
        if self.__config.wrapped_data_key in attributes:
            wrapped = attributes.get(self.__config.wrapped_data_key)
            if not isinstance(wrapped, dict):
                raise ValueError(
                    f'Expected "{self.__config.wrapped_data_key}" to contain a JSON object'
                )
            return wrapped
        return attributes

    @staticmethod
    def __get_nested(obj: Any, *path: str) -> Any:
        current = obj
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def __extract_first_species_taxid(self, payload: dict[str, Any]) -> str | None:
        species = self.__get_nested(payload, 'assembly_stats', 'species')
        if not isinstance(species, list):
            return None
        for species_entry in species:
            if isinstance(species_entry, dict):
                value = species_entry.get('ncbi_taxonomy_id')
                if value not in (None, ''):
                    return str(value)
        return None

    def __extract_first_sample_tolid(self, payload: dict[str, Any]) -> str | None:
        samples = self.__get_nested(payload, 'assembly_stats', 'samples')
        if not isinstance(samples, list):
            return None
        for sample in samples:
            if isinstance(sample, dict):
                value = sample.get('tolid')
                if value not in (None, ''):
                    return str(value)
        return None

    @staticmethod
    def __first_non_empty(*values: Any) -> Any:
        for value in values:
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == '':
                continue
            return value
        return None
