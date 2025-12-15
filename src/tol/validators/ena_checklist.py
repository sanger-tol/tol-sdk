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
            if 'mandatory' in validation and key not in obj.attributes:
                self.add_error(object_id=obj.id, detail='Must be given', field=[field_name])
                continue
            if 'mandatory' in validation and obj.attributes[key] is None:
                self.add_error(object_id=obj.id, detail='Must be given', field=[field_name])
                continue
            if 'mandatory' in validation and obj.attributes.get(key) == '':
                self.add_error(
                    object_id=obj.id,
                    detail='Must not be empty', field=[field_name]
                )

            if 'restricted text' in validation and key in obj.attributes:
                for condition in validation:
                    if isinstance(condition, str) and '(' in condition:
                        regex = condition
                compiled_re = re.compile(regex)
                if not compiled_re.search(obj.attributes.get(key)):
                    self.add_error(
                        object_id=obj.id,
                        detail='Must match specific pattern', field=[field_name]
                    )

            # Check against allowed values
            if 'text choice' in validation and key in obj.attributes:
                for condition in validation:
                    if isinstance(condition, list):
                        allowed_values = condition
                if obj.attributes.get(key).lower() not in \
                        [x.lower() for x in allowed_values]:
                    self.add_error(
                        object_id=obj.id,
                        detail='Must be in allowed values', field=[field_name]
                    )
