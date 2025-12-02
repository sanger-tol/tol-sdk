# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass

from tol.core import DataObject, Validator


@dataclass(slots=True, frozen=True)
class MutuallyExclusiveConfig:
    pass


class MutuallyExclusiveValidator(Validator):
    __slots__ = ['__config']
    __config: MutuallyExclusiveConfig
    
    def __init__(self, config: MutuallyExclusiveConfig) -> None:
        super().__init__()
    
    def _validate_data_object(self, obj: DataObject) -> None:
        pass
