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
        'reviewer_reports',
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

        yield self._data_object_factory(
            self.__config.destination_type,
            data_object.id,
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
