# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Tuple, cast

from tol.core import DataObject, Validator
from tol.validators import Condition


ConditionDict = Dict[str, str]
PassConfig = Dict[str, List[ConditionDict]]
Config = Dict[str, str | List[PassConfig] | bool]


class CumulativeUniquenessValidator(Validator):
    # TODO: Rewrite doc comment for clarity
    """
    Validates an incoming stream of `DataObject` instances.
    It performs multiple passes, where each pass the 'unique_field'
    from the config is checked to see whether it is in the accumulated list,
    although this is only checked for fields that satisfy
    the conditions (also defined in the config). If in the list, it
    is not unique so this is an error. The config's 'append_to_list'
    boolean value controls which passes append to the cumulative list.
    """
    __slots__ = ('__unique_field', '__passes', '__occurrences')
    __unique_field: str
    __passes: List[PassConfig]
    __occurrences: List[Any]

    def __init__(self, config: Config) -> None:
        super().__init__()
        # TODO Use extract fn
        self.__unique_field = cast(str, config['unique_field'])
        self.__passes = cast(List[PassConfig], config['passes'])
        self.__occurrences = []
    
    def _validate_data_object(self, obj: DataObject) -> None:
        # for pass_ in self.__passes:
        append_to_list = cast(bool, pass_['append_to_list'])

        if self._check_conditions(cast(List[ConditionDict], pass_['conditions'])):
            value = obj.attributes.get(self.__unique_field)
            if value in occurrences:
                self.add_error(
                    object_id=obj.id,
                    detail=cast(str, pass_['error_message']),
                    field=self.__unique_field,
                )

            if append_to_list:
                occurrences.append(obj.attributes.get(self.__unique_field))