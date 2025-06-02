# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any

from tol.core.validate import Validator


@dataclass(frozen=True, kw_only=True)
class AllowedValues:
    key: str
    values: list[Any]

    is_error: bool = True

    def is_allowed(self, __v: Any) -> bool:
        return __v in self.values


class AllowedValuesValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """

    def __init__(
        self,
        config: list[AllowedValues]
    ) -> None:
        pass
