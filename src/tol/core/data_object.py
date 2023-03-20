# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC
from typing import Any, Dict

# only import DataSource for type hints
if typing.TYPE_CHECKING:
    from .datasource import DataSource


DataDict = Dict[str, Any]


class DataObject(ABC):
    """
    The abstract base class for the unit of data
    on which a DataSource operates.
    """

    def __init__(
        self,
        object_type: str,
        data_source: DataSource,
        data: DataDict
    ):
        self.__object_type = object_type
        self.__data_source = data_source
        self.set_data(data)

    @property
    def object_type(self):
        return self.__object_type

    def set_data(self, data: DataDict) -> None:
        """
        Sets the data as given to the constructor.
        Override for custom behaviour.
        """
        for key, value in data.items():
            setattr(self, key, value)
