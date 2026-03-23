# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject
from tol.core.validate import Validator


class MinOneValidValueValidator(Validator):
    """
    Validates that a stream of `DataObject` instances
    have at least one valid value present in a list of specified keys.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        non_valid_values: list[str]
        keys: list[str]

    __slots__ = ['__config']
    __config: Config

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:

        super().__init__()
        self.__config = config

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        found_valid_value = False

        for key in self.__config.keys:
            value = obj.attributes[key]

            if value is not None and value not in self.__config.non_valid_values:
                found_valid_value = True
                break

        if not found_valid_value:
            self.add_error(
                object_id=obj.id,
                detail=(
                    f'At least one of: {self.__config.keys} '
                    'must not be: ' + ', '.join(self.__config.non_valid_values)
                    + ' or empty.'
                ),
                field=', '.join(self.__config.keys),
            )
