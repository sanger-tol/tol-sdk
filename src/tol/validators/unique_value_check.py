# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import Validator
from tol.core.data_object import DataObject


class UniqueValueCheckValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances.
    For each data object (sample) it checks if the GAL column has only one value
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field: str

    __slots__ = ['__config', '_cached']
    __config: Config
    _cached: str | None

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()
        self.__config = config
        self._cached = None

    def _validate_data_object(self, obj: DataObject) -> None:
        # This function is used to check if the data object has a single value for GAL column

        if not self._cached:
            self._cached = obj.attributes.get(self.__config.field)

        else:
            if obj.attributes.get(self.__config.field) != self._cached:
                self.add_error(
                    object_id=obj.id,
                    detail=f'More than one value detected in {self.__config.field}',
                    field=self.__config.field,
                )
