# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import DataObject, DataSource
from tol.core.validate import Validator
from tol.sources.sts import sts


class StsFieldsValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains fields that observe the validations in STS
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        project_code: str

    __slots__ = ['__config', '__datasource', '__fields']
    __config: Config
    __datasource: DataSource
    __fields: List[str | int | float]

    def __init__(
        self,
        config: Config,
        datasource: DataSource = sts(),  # For testing
        **kwargs
    ) -> None:

        super().__init__()

        self.__config = config
        self.__datasource = datasource
        self.__fields = self.__initialize_fields_from_datasource()

    def __initialize_fields_from_datasource(self) -> List[str | int | float]:
        return {
            field.get('data_input_key'): field
            for field in self.__datasource.get_one(
                'project', self.__config.project_code
            ).template.get('data_fields', [])
            if field.get('in_manifest')
        }

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        for field in self.__fields.values():
            # Get the value from the data object
            field_value = obj.get_field_by_name(field.get('data_input_key'))
            if field.get('mandatory_validation') and (field_value is None or field_value == ''):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} is required '
                           f'for project {self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
            elif field.get('allowed_values'):
                allowed_values = [
                    value.get('value') for value in field.get('allowed_values', [])
                ]
                if field_value not in allowed_values:
                    self.add_error(
                        object_id=obj.id,
                        detail=f'Field {field.get("data_input_key")} value '
                               f'"{field_value}" not found in allowed values '
                               f'{allowed_values} for project '
                               f'{self.__config.project_code}',
                        field=field.get('data_input_key'),
                    )
            elif field.get('min') and field.get('type') == 'String' \
                    and field_value is not None and len(field_value) < field.get('min'):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" is shorter than minimum length '
                           f'"{field.get("min")}" for project '
                           f'{self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
            elif field.get('max') and field.get('type') == 'String' \
                    and field_value is not None and len(field_value) > field.get('max'):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" is longer than maximum length '
                           f'"{field.get("max")}" for project '
                           f'{self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
