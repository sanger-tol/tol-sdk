# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
# TODO: Change these horrible names

from typing import Any, Dict, List, Tuple, cast

from .interfaces import ConditionEvaluator

from tol.core import DataObject, Validator



"""
NEXT:
- You need two lists. One for where, one for the other
- You need to add a second condition to the config for this other
- Go through each, and if a match occurs, remove them from the lists.
  Then check in _post_validation that there are none left.
MutuallyExclusiveValidator?
Because target fields where second condition must not be any of the target fields where first condition
"""
config = {
    'first_field_where': {
        'field': 'SYMBIONT',
        'operator': '!=',
        'value': 'SYMBIONT',
    },
    'second_field_where': {
        'field': 'SYMBIONT',
        'operator': '==',
        'value': 'SYMBIONT',
    },
    'target_fields': [
        'RACK_OR_PLATE_ID',
        'TUBE_OR_WELL_ID',
    ],
    'error_message': 'All symbionts must have a TARGET with same rack/plate and tube/well'
}






ConditionConfig = Dict[str, str]
TargetsCnfig = List[str]
Config = Dict[str, ConditionConfig | TargetsCnfig | str]


class OneToManyValidator(Validator, ConditionEvaluator):
    """
    TODO: Doc comment
    """
    __slots__ = ['__config', '__target_fields_for_conditional', '__target_fields_for_orphaned']
    __config: Config
    __target_fields_for_conditional: List[List[str]]
    __taget_fields_for_orphaned: List[List[str]]

    def __init__(self, config: Config) -> None:
        super().__init__()

        self.__config = config
        self.__target_fields_for_conditional = []
        self.__target_fields_for_orphaned = []
    
    def _validate_data_object(self, obj: DataObject) -> None:
        conditional_condition = cast(
            ConditionConfig,
            self.__extract_config_value(self.__config, 'conditional_field_condition')
        )
        orphaned_condition = cast(
            ConditionConfig,
            self.__extract_config_value(self.__config, 'orphaned_field_condition')
        )
        checked_fields = cast(
            CheckedFieldsConfig,
            self.__extract_config_value(self.__config, 'checked_fields')
        )

        if self._evaluate_condition(*self.__extract_condition(obj, conditional_condition)):
            self.__target_fields_for_conditional.append(checked_fields)
        elif self._evaluate_condition(*self.__extract_condition(obj, orphaned_condition)):
            if checked_fields not in self.__target_fields_for_conditional:
                self.add_error(
                    object_id=obj.id,
                    detail=cast(str, self.__extract_config_value(self.__config, 'error_message'))
                )
    
    def __extract_condition(self, obj: DataObject, condition: Dict) -> Tuple[Any, str, Any]:
        condition_field = cast(
            str, self.__extract_config_value(condition, 'field')
        )
        condition_field_value = obj.attributes.get(condition_field)
        if condition_field_value is None:
            self.add_error(
                object_id=obj.id,
                detail=f'The requested condition field {condition_field}'
                        'was not found in the DataObject',  # noqa E131
                field=condition_field,
            )
        operator = cast(
            str, self.__extract_config_value(condition, 'operator')
        )
        expected_value = cast(
            Any, self.__extract_config_value(condition, 'value')
        )

        return (condition_field_value, operator, expected_value)

    def __extract_config_value(self, dictionary: Dict, key: str):
        """
        A reusable function that handles extracting a key from the config, handling the case
        that it is not present. It takes in a `dictionary` to look in, because the key may not
        be at the top-level of the config
        """
        try:
            return dictionary[key]
        except KeyError:
            raise Exception(f'VALIDATOR SETUP ERROR: '
                            f'{key} not present in the config for AssertOnConditionValidator')
