# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from tol.core import DataObject
from tol.core.validate import Validator

from .regex import Regex

RegexDict = dict[
    str,
    str | bool | list[Any],
]
Config = dict[str, str | dict[str, list[Regex | RegexDict]]]

"""Can also specify `Regex` as a `dict`"""


class RegexByValueValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """

    def __init__(
        self,
        config: dict[str, str | list[str]]
    ) -> None:

        super().__init__()

        self.__config = self.__get_config(config)

    def __get_config(
        self,
        config: Config,
    ) -> Config:

        return {
            'key_column': config['key_column'],
            'regexes': {
                k: [
                    c if isinstance(c, Regex) else Regex(**c)
                    for c in v
                ]
                for k, v in config['regexes'].items()
            }
        }

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        # Pull out value of the 'key_column' attribute
        key_column_value = obj.attributes.get(self.__config['key_column'])
        if not key_column_value:
            return
        # Pull out relevant regex list based on this value: {[{'name': 'regex'}]}
        regex_list = self.__config['regexes'].get(key_column_value)
        if not regex_list:
            return
        self.__validate_attribute(obj, regex_list)

    def __validate_attribute(
        self,
        obj: DataObject,
        regexes: list[Regex],
    ) -> None:
        for r in regexes:
            attribute_name = r.key
            value = obj.attributes.get(attribute_name)
            if not r.is_allowed(value):
                self.__add_result(obj, r)

    def __add_result(
        self,
        obj: DataObject,
        c: Regex,
    ) -> None:

        if c.is_error:
            self.add_error(
                object_id=obj.id,
                detail=c.detail,
                field=c.key
            )
        else:
            self.add_warning(
                object_id=obj.id,
                detail=c.detail,
                field=c.key,
            )
