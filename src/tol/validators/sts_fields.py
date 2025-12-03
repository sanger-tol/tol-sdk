# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, DataSource
from tol.core.validate import Validator
from tol.sources.sts import sts


class StsFieldsValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    contains fields that observe the validations in STS
    """

    @dataclass
    class Config:
        project_code: str

    def __init__(
        self,
        config: Config,
        datasource: DataSource = sts(),  # For testing
    ) -> None:

        super().__init__()

        self._config = config
        self.__datasource = datasource
        self.__fields = self.__initialize_fields_from_datasource()

    def __initialize_fields_from_datasource(self) -> list[str | int | float]:
        return {
            field.get('data_input_key'): field
            for field in self.__datasource.get_one(
                'project', self._config.project_code
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
            if field.get('mandatory_input') and (field_value is None or field_value == ''):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} is required '
                           f'for project {self._config.project_code}',
                    field=field.get('data_input_key'),
                )
            elif field.get('allowed_values') and field_value not in field.get('allowed_values'):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" not found in allowed values '
                           f'{field.get("allowed_values")} for project '
                           f'{self._config.project_code}',
                    field=field.get('data_input_key'),
                )
            elif field.get('min') and field_value < field.get('min'):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" is less than minimum value '
                           f'"{field.get("min")}" for project '
                           f'{self._config.project_code}',
                    field=field.get('data_input_key'),
                )
            elif field.get('max') and field_value > field.get('max'):
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" is greater than maximum value '
                           f'"{field.get("max")}" for project '
                           f'{self._config.project_code}',
                    field=field.get('data_input_key'),
                )
