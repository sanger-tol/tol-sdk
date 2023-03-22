# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod, abstractproperty

from tol.api_base.utils import tol_fields

from ...utils.config import DataTypeConfig
from ....core.datasource import DataSource


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

    @abstractproperty
    def id_field(self) -> tol_fields.Id:
        """
        Returns the archetypic tol_field.Id for the inherited
        class
        """
        pass

    @abstractmethod
    def to_config(self) -> DataTypeConfig:
        """
        Produces an IndividualConfig DataClass instance, defining
        everything other classes require to operate upon this
        archetype.
        """
        pass
