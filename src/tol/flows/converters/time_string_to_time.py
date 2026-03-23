# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from dataclasses import dataclass
from datetime import time
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter


class TimeStringToTimeConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        field_names: list[str]

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        Converts string fields representing time in HH:MM (24-hour) format to Python time objects.
        If the string is not in HH:MM, tries to append ':00' and parse as HH:MM:SS.
        """

        for field_name in self.__config.field_names:
            value = data_object.attributes.get(field_name)
            if isinstance(value, str):
                match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', value)
                if match:
                    h, m = int(match.group(1)), int(match.group(2))
                    s = int(match.group(3)) if match.group(3) else 0
                    try:
                        data_object.attributes[field_name] = time(h, m, s)
                    except ValueError:
                        pass
        yield data_object
