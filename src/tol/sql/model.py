# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, ABCMeta, abstractclassmethod, abstractproperty
from typing import Any, Dict, Optional, Type

from sqlalchemy.orm import DeclarativeMeta, declarative_base


class Model(ABC):
    """
    A model that can be converted to DataObject instances.

    The properties can be implemented in many different ways, but
    are necessary on every child class that is exposed to
    SqlDataSource.
    """

    @abstractclassmethod
    def get_table_name(cls) -> str:  # noqa
        """The name of the Model"""

    @abstractclassmethod
    def get_id_column_name(cls) -> str:  # noqa
        """
        The name of the column that serves as the "id".
        Override this classmethod to change.
        """

    @abstractproperty
    def instance_id(self) -> Optional[str]:
        """The (potentially None) id of this model instance"""

    @abstractproperty
    def instance_attributes(self) -> Dict[str, Any]:
        """The Dict of attribute key to values"""


def model_base() -> Type[Model]:
    """
    Creates a new base for Model classes that implement the Model ABC.
    """

    class ModelMeta(DeclarativeMeta, ABCMeta):
        pass

    DeclarativeBase = declarative_base(metaclass=ModelMeta)  # noqa N806

    class ModelBase(DeclarativeBase, Model, ABC):
        """
        An ABC that implements the Model ABC, using reasonable defaults.

        Either:
        - use this class for reasonable default behaviour
        - inherit from both DeclarativeBase and Model, implementing the
        required abstract members, if custom behaviour is required.
        """

        __abstract__ = True

        __tablename__: str
        """The name of this table in the actual DB"""

        @classmethod
        def get_table_name(cls) -> str:
            return cls.__tablename__

        @classmethod
        def get_id_column_name(cls) -> str:
            return 'id'

        @property
        def instance_id(self) -> Optional[str]:
            id_key = self.get_id_column_name()
            id_val = getattr(self, id_key)
            return None if id_val is None else str(id_val)

        @property
        def instance_attributes(self) -> Dict[str, Any]:
            id_key = self.get_id_column_name()
            return {
                k: getattr(self, v.key)
                for k, v in self.__mapper__.attrs.items()
                if k != id_key
            }

    return ModelBase
