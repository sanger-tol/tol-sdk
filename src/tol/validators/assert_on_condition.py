# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import List

from tol.core import DataObject, Validator

from .interfaces import Condition, ConditionDict, ConditionEvaluator


class AssertOnConditionValidator(Validator, ConditionEvaluator):
    """
    Validates an incoming stream of `DataObject` instances,
    using a condition to check a specific attrbiute. If this
    condition passes, then the assertions will be run, which must
    all pass.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        condition: ConditionDict
        assertions: List[ConditionDict]

    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config, **kwargs) -> None:
        super().__init__()

        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        # Check condition atribute
        # (only perform the assertions if the condition passes)
        if self._does_condition_pass(Condition.from_dict(self.__config.condition), obj):
            # Perform each assertion
            for assertion in self.__config.assertions:
                self.__perform_assertion(obj, Condition.from_dict(assertion))

    def __perform_assertion(self, obj: DataObject, assertion: Condition) -> None:
        # There's only an error or warning if the assertion condition fails
        condition_passed, found_value = self._evaluate_condition(assertion, obj)
        if not condition_passed:
            if assertion.is_error:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Expected {assertion} (found value {found_value})',
                    field=assertion.field,
                )
            else:
                self.add_warning(
                    object_id=obj.id,
                    detail=f'Expected {assertion} (found value {found_value})',
                    field=assertion.field,
                )
