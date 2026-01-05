# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import Validator
from tol.core.data_object import DataObject


class ValueCheckValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) it checks if it is a SYMBIONT
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field: str
        value: str

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function is used to check if the data object is SYMBIONT or not

        if obj.attributes.get(self.__config.field) == self.__config.value:
            self.add_error(
                object_id=obj.id,
                detail=f'{self.__config.value} is detected',
                field=self.__config.field,
            )
