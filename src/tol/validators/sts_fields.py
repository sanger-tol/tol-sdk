# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from datetime import datetime, timedelta
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
            # Ignore inactive fields
            if field.get('status') == 'Inactive':
                continue
            # Get the value from the data object
            field_value = obj.get_field_by_name(field.get('data_input_key'))
            if isinstance(field_value, list):
                field_value = ' | '.join(str(v) for v in field_value)

            # mandatory_input fields must be present
            if field.get('mandatory_input') and field.get('data_input_key') not in obj.attributes:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} is required '
                           f'for project {self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
                continue

            # Skip further validations if validation is not mandatory
            if not field.get('mandatory_validation'):
                continue

            # Mandatory validation fields must have a value
            if field_value is None or field_value == '':
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} is required to have a value '
                           f'for project {self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
                continue

            # Allowed values
            if field.get('allowed_values'):
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

            if field.get('type') in ['String', 'TextArea']:
                self.__validate_string(obj, field, field_value)

            if field.get('type') in ['Integer', 'Decimal', 'Percentage']:
                self.__validate_number(obj, field, field_value)

            if field.get('type') in ['Boolean']:
                self.__validate_boolean(obj, field, field_value)

            if field.get('type') in ['Date']:
                self.__validate_date(obj, field, field_value)

    def __validate_string(
        self,
        obj: DataObject,
        field: dict,
        field_value: str | int | float | None
    ) -> None:
        # Check type is a string
        # if not isinstance(field_value, str):
        #     self.add_error(
        #         object_id=obj.id,
        #         detail=f'Field {field.get("data_input_key")} value '
        #                 f'"{field_value}" is not a string for project '
        #                 f'{self.__config.project_code}',
        #         field=field.get('data_input_key'),
        #     )
        #     return

        # Min/Max validations for string
        if field.get('min') and len(field_value) < field.get('min'):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is shorter than minimum length '
                       f'"{field.get("min")}" for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )
        if field.get('max') and len(field_value) > field.get('max'):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is longer than maximum length '
                       f'"{field.get("max")}" for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )

    def __validate_number(
        self,
        obj: DataObject,
        field: dict,
        field_value: str | int | float | None
    ) -> None:
        # Check type is a number
        if not isinstance(field_value, (int, float)):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is not a number for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )
            return

        # Min/Max validations for number
        if field.get('min') is not None and field_value < field.get('min'):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is less than minimum value '
                       f'"{field.get("min")}" for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )
        if field.get('max') is not None and field_value > field.get('max'):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is greater than maximum value '
                       f'"{field.get("max")}" for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )

    def __validate_boolean(
        self,
        obj: DataObject,
        field: dict,
        field_value: str | int | float | None
    ) -> None:
        # Check type is a boolean
        if field_value not in ['Y', 'N']:
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is not a boolean (Y/N) for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )

    def __validate_date(
        self,
        obj: DataObject,
        field: dict,
        field_value: str | int | float | None
    ) -> None:
        if not isinstance(field_value, datetime):
            self.add_error(
                object_id=obj.id,
                detail=f'Field {field.get("data_input_key")} value '
                       f'"{field_value}" is not a date string for project '
                       f'{self.__config.project_code}',
                field=field.get('data_input_key'),
            )
            return
        if field.get('range_limit'):
            earliest_date = datetime.now() - timedelta(days=field.get('min'))
            latest_date = datetime.now() + timedelta(days=field.get('max'))
            if field_value < earliest_date or field_value > latest_date:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Field {field.get("data_input_key")} value '
                           f'"{field_value}" is not within the allowed date '
                           f'range for project {self.__config.project_code}',
                    field=field.get('data_input_key'),
                )
