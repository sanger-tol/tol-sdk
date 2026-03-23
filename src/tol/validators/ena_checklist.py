# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass

from tol.core import DataSource
from tol.core.data_object import DataObject
from tol.core.validate import Validator
from tol.sources.ena import ena


class EnaChecklistValidator(Validator):
    ENA_TO_INTERNAL_FIELD_MAP = {
        'geographic location (longitude)': 'DECIMAL_LONGITUDE',
        'geographic location (latitude)': 'DECIMAL_LATITUDE',
    }

    """
    validates the ENA_CHECKLIST for each samples
    """

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        ena_checklist_id: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, datasource: DataSource = ena(), **kwargs) -> None:
        super().__init__()
        self.__config = config
        self._datasource = datasource
        self.__ena_checklist = datasource.get_one(
            'checklist',
            self.__config.ena_checklist_id
        ).checklist

    def _validate_data_object(self, obj: DataObject) -> None:
        for key, validation in self.__ena_checklist.items():
            field_name = key
            if 'field' in validation:
                field_name = validation['field']
            internal_field = self.ENA_TO_INTERNAL_FIELD_MAP.get(field_name, field_name)

            if 'mandatory' in validation and key not in obj.attributes:
                self.add_error(object_id=obj.id, detail='Must be given', field=[internal_field])
                continue
            if 'mandatory' in validation and obj.attributes[key] is None:
                self.add_error(object_id=obj.id, detail='Must be given', field=[internal_field])
                continue
            if 'mandatory' in validation and obj.attributes.get(key) == '':
                self.add_error(
                    object_id=obj.id,
                    detail='Must not be empty', field=[internal_field]
                )

            if 'restricted text' in validation and key in obj.attributes:
                for condition in validation:
                    if isinstance(condition, str) and '(' in condition:
                        regex = condition
                compiled_re = re.compile(regex)
                if not compiled_re.search(obj.attributes.get(key)):
                    if internal_field in ('DECIMAL_LONGITUDE', 'DECIMAL_LATITUDE'):
                        self.add_error(
                            object_id=obj.id,
                            detail=(
                                f'Value for {internal_field} must be a valid decimal in the'
                                f' format required by ENA (e.g. 12.3456). '
                                f'See ENA checklist for accepted format.',
                            ),
                            field=[internal_field]
                        )
                    else:
                        self.add_error(
                            object_id=obj.id,
                            detail=(
                                f'Value for {internal_field} must match the required pattern.'
                            ),
                            field=[internal_field]
                        )

            if 'text choice' in validation and key in obj.attributes:
                for condition in validation:
                    if isinstance(condition, list):
                        allowed_values = condition
                if obj.attributes.get(key).lower() not in \
                        [x.lower() for x in allowed_values]:
                    self.add_error(
                        object_id=obj.id,
                        detail='Must be in allowed values', field=[internal_field]
                    )
