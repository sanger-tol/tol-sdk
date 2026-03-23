# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Dict, List

from tol.core import DataObject
from tol.core.validate import Validator

from .regex import Regex, RegexDict


class RegexByValueValidator(Validator):
    """
    Validates an incoming stream of `DataObject` instances
    according to the specified allowed values for a given
    key.
    """
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        key_column: str
        regexes: Dict[str, List[Regex | RegexDict]]

    __slots__ = ['__config']
    config: Config

    def __init__(
        self,
        config: Config,
        **kwargs
    ) -> None:

        super().__init__()

        self.__config = self.__get_config(config)

    def _validate_data_object(
        self,
        obj: DataObject
    ) -> None:
        # Pull out value of the 'key_column' attribute
        key_column_value = obj.attributes.get(self.__config.key_column)
        if not key_column_value:
            return

        # Pull out relevant regex list based on this value: {[{'name': 'regex'}]}
        regex_list = self.__config.regexes.get(key_column_value)
        if not regex_list:
            return
        self.__validate_attribute(obj, regex_list)

    def __validate_attribute(
        self,
        obj: DataObject,
        regexes: List[Regex],
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

    def __get_config(
        self,
        config: Config,
    ) -> Config:

        # Ensure config is in Regex format
        # (as you can either pass in a list of Regex or a RegexDict,
        # which can be used to initialize a Regex)
        return self.Config(
            key_column=config.key_column,
            regexes={
                k: [
                    c if isinstance(c, Regex) else Regex(**c)
                    for c in v
                ]
                for k, v in config.regexes.items()
            }
        )
