# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, cast, Dict, List

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
    __slots__ = ['__config']
    __config: Config

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__config = config

    def _validate_data_object(self, obj: DataObject) -> None:
        """
        Called for each DataObject in the validation stream
        """
        # Extract the condition from the config
        condition = cast(ConditionConfig, self.__config['condition'])
        condition_attribute_value = obj.attributes.get(condition['field'])
        if condition_attribute_value is None:
            # TODO: Config validation?
            return

        # Check condition attribute
        # (only perform the assertions if the condition passes)
        if self.__check_condition(
            condition_attribute_value, condition['operator'], condition['value']
        ):
            # Perform each assertion
            for assertion in self.__config['assert']:
                self.__perform_assertion(obj, cast(AssertConfig, assertion))

    def __perform_assertion(self, obj: DataObject, assertion: AssertConfig) -> None:
        # Extract data from assertion
        # TODO: Use .get instead of square brackets in all these situations
        attribute = cast(str, assertion['field'])
        attribute_value = obj.attributes.get(attribute)
        if attribute_value is None:
            # TODO validation here
            return
        # TODO: Validation where cast is used too
        operator = cast(str, assertion['operator'])
        expected_value = assertion['value']

        # Only an error or warning if the assertion condition fails
        if not self.__check_condition(attribute_value, operator, expected_value):
            # Check whether this is an error or a warning
            is_error = assertion.get('is_error', True)
            # message = cast(str, assertion['message'])  # TODO Allow optional

            if is_error:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Expected {attribute} {operator} {expected_value}',
                    field=attribute,
                )
            else:
                self.add_warning(
                    object_id=obj.id,
                    detail=f'Expected {attribute} {operator} {expected_value}',
                    field=attribute,
                )

    def __check_condition(self, left: Any, operator: str, right: Any) -> bool:
        # TODO: In total, which operators are supported? Is it more than these?
        match operator:
            case '==':
                return left == right
            case '!=':
                return left != right
            case '<':
                return left < right
            case '<=':
                return left <= right
            case '>':
                return left > right
            case '>=':
                return left >= right
            # TODO: Use == with [] instead?
            case 'in':
                return left in right
            case _:
                # TODO: Error invalid config
                # Operator is unsupported or invalid
                return False
