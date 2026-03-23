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
        if obj.attributes.get(self.__config.field) != self.__config.value:
            self.add_error(
                object_id=obj.id,
                detail=(
                    f"Expected '{self.__config.value}' for field "
                    f"'{self.__config.field}', but got '{obj.attributes.get(self.__config.field)}'"
                ),
                field=self.__config.field,
            )
