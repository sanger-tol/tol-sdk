# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import Validator
from tol.core.data_object import DataObject


class UniqueWellsCheckValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances obtained
    from a converter which maps sample[PLATE_ID] to sample[WELL_ID]
    For each data object (sample) it checks specific regex pattern
    followed by count off wells along with duplicate wells check
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        plate_id: str
        regex: list[str]

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function is used to check count of wells and if duplicates are present

        wells = obj.get_field_by_name(self.__config.plate_id)

        for pattern in self.__config.regex:
            if pattern in wells:
                if len(wells) > 1:
                    self.add_error(
                        object_id=obj.id,
                        detail=f'expected only one entry in'
                        f' PLATE_ONLY plate {self.__config.plate_id}',
                        field=self.__config.field,
                    )
            elif len(wells) < 96:
                self.add_warning(
                    object_id=obj.id,
                    detail=f'incomplete plate {self.__config.plate_id}'
                    f' contains {len(wells)} of 96 expected wells',
                    field=self.__config.field,
                )
            if len(set(wells)) < len(wells):
                self.add_warning(
                    object_id=obj.id,
                    detail=f'duplicate well IDs found in plate {self.__config.plate_id}',
                    field=self.__config.field,
                )
