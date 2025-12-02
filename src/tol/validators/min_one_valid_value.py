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

    @dataclass
    class Config:
        blank_values: list[str]
        keys: list[str]

    def __init__(
        self,
        config: Config,
    ) -> None:

        super().__init__()
        self._config = config

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:

        found_valid_value = False

        for key in self._config.keys:
            value = obj.attributes[key]

            if value is not None and value not in self._config.blank_values:
                found_valid_value = True
                break

        if not found_valid_value:
            self.add_error(
                object_id=obj.id,
                detail=(
                    f'None of the specified columns {self._config.keys} '
                    'contain a valid value.'
                ),
                field=', '.join(self._config.keys),
            )
