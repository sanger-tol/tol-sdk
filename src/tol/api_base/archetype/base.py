# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from ..utils.config import IndividualConfig
from ...core.datasource import DataSource


class Archetype(ABC):
    """
    A declarative Archetype class for an object_type.
    
    Must implement the to_config method.
    """

    def __init__(self, data_source: DataSource) -> None:
        self.__data_source = data_source

    @property
    def data_source(self) -> DataSource:
        return self.__data_source

    @abstractmethod
    def to_config(self) -> IndividualConfig:
        pass
