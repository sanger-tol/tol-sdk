# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass

from tol.core import DataSource
from tol.core.data_object import DataObject
from tol.core.validate import Validator
from tol.sources.ena import ena


@dataclass
class EnaChecklistConfig:
    ena_checklist_id: list[str]


class EnaChecklistValidator(Validator):
    """
    validates the ENA_CHECKLIST for each samples
    """
    __slots__ = ['__config']

    def __init__(self, config: EnaChecklistConfig, datasource: DataSource = ena()) -> None:
        super().__init__()
        self._config = config
        self._datasource = datasource

    def _validate_data_object(self, obj: DataObject) -> None:
        ena_datasource = self._datasource
        ena_checklist = ena_datasource.get_by_id('checklist', self._config.ena_checklist_id)

        for checklist in ena_checklist:
            validations = checklist.attributes['checklist']
            for key in validations:
                field_name = key
                if 'field' in validations[key]:
                    field_name = validations[key]['field']
                print(obj.attributes)
                if 'mandatory' in validations[key] and key not in obj.attributes:
                    self.add_error(object_id=obj.id, detail='Must be given', field=[field_name])
                    continue
                if 'mandatory' in validations[key] and obj.attributes[key] is None:
                    self.add_error(object_id=obj.id, detail='Must be given', field=[field_name])
                    continue
                if 'mandatory' in validations[key] and obj.attributes.get(key) == '':
                    self.add_error(object_id=obj.id,
                                   detail='Must not be empty', field=[field_name])

                if 'restricted text' in validations[key] and key in obj.attributes:
                    for condition in validations[key]:
                        if type(condition) == str and '(' in condition:
                            regex = condition
                    compiled_re = re.compile(regex)
                    if not compiled_re.search(obj.attributes.get(key)):
                        self.add_error(object_id=obj.id,
                                       detail='Must match specific pattern', field=[field_name])

                # Check against allowed values
                if 'text choice' in validations[key] and key in obj.attributes:
                    for condition in validations[key]:
                        if type(condition) == list:
                            allowed_values = condition
                    if obj.attributes.get(key).lower() not in \
                            [x.lower() for x in allowed_values]:
                        self.add_error(object_id=obj.id,
                                       detail='Must be in allowed values', field=[field_name])
