# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List

from tol.core import DataObject, Validator


ConditionConfig = Dict[str, str]
AssertConfig = Dict[str, str | List[Any]]
Config = Dict[str, ConditionConfig | List[AssertConfig]]


class AssertOnConditionValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances,
    using a condition to check a specific attrbiute. If this
    condition passes, then the assertions will be run, which must
    all pass.
    """
    __slots__ = ["__config"]
    __config: Config

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        pass
