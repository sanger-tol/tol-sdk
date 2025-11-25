# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Tuple, cast

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
        # Get condition
        condition = cast(
            ConditionConfig, self.__extract_config_value(obj, self.__config, 'condition')
        )

        # Check condition attribute
        # (only perform the assertions if the condition passes)
        if self.__check_condition(*self.__get_condition(obj, condition)):
            # Perform each assertion
            for assertion in self.__config['assert']:
                self.__perform_assertion(obj, cast(AssertConfig, assertion))

    def __get_condition(self, obj: DataObject, condition: Dict) -> Tuple[str, Any, str, Any]:
        # condition = cast(
        #     ConditionConfig, self.__extract_config_value(obj, self.__config, key)
        # )
        condition_field = cast(
            str, self.__extract_config_value(obj, condition, 'field')
        )
        condition_field_value = obj.attributes.get(condition_field)
        if condition_field_value is None:
            # TODO ERROR THAT THERE'S NO FIELD
            pass
        operator = cast(
            str, self.__extract_config_value(obj, condition, 'operator')
        )
        expected_value = cast(
            Any, self.__extract_config_value(obj, condition, 'value')
        )

        return (condition_field, condition_field_value, operator, expected_value)

    def __perform_assertion(self, obj: DataObject, assertion: AssertConfig) -> None:
        # Extract data from assertion
        field, field_value, operator, expected_value = self.__get_condition(obj, assertion)

        # There's only an error or warning if the assertion condition fails
        if not self.__check_condition(field, field_value, operator, expected_value):
            # Check whether this is an error or a warning (defaulting to an error)
            is_error = assertion.get('is_error', True)

            if is_error:
                self.add_error(
                    object_id=obj.id,
                    detail=f'Expected {field} {operator} {expected_value}',
                    field=field,
                )
            else:
                self.add_warning(
                    object_id=obj.id,
                    detail=f'Expected {field} {operator} {expected_value}',
                    field=field,
                )

    def __check_condition(self, field: str, left: Any, operator: str, right: Any) -> bool:
        # TODO: In total, which operators are supported? Is it more than/different to these?
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
            case 'in':
                return left in right
            case _:
                # TODO: Error invalid config
                # Operator is unsupported or invalid
                return False

    def __extract_config_value(self, obj: DataObject, dictionary: Dict, key: str):
        try:
            return dictionary[key]
        except KeyError:
            # TODO: Figure out how to handle config errors. A custom exception? self.add_error?
            # Although if exceptions are used instead of a detailed error why not just use
            # [] to access in the first place?
            raise Exception(f'CONFIG ERROR IN VALIDATOR: {key} is None in {dictionary} dict')
