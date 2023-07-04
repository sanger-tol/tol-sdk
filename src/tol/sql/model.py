# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, List, Optional, Type

from sqlalchemy import inspect
from sqlalchemy.orm import (
    ColumnProperty,
    DeclarativeMeta,
    MappedColumn,
    RelationshipDirection,
    declarative_base
)

from .exception import BadColumnError


class Model(ABC):
    """
    A model that can be converted to DataObject instances.

    The properties can be implemented in many different ways, but
    are necessary on every child class that is exposed to
    SqlDataSource.
    """

    @classmethod
    @abstractmethod
    def get_table_name(cls) -> str:  # noqa
        """The name of the Model"""

    @classmethod
    @abstractmethod
    def get_id_column_name(cls) -> str:  # noqa
        """
        The name of the column that serves as the "id".
        Override this classmethod to change.
        """

    @classmethod
    @abstractmethod
    def get_column(cls, name: str) -> MappedColumn:  # noqa N805
        """The (attribute) column for the given name."""

    @classmethod
    @abstractmethod
    def get_to_one_relationship_config(cls) -> dict[str, str]:  # noqa N805
        """
        The mapping of relationship names to tablenames for to-one relationships
        """

    @classmethod
    @abstractmethod
    def get_to_many_relationship_config(cls) -> dict[str, str]:  # noqa N805
        """
        The mapping of relationship names to tablenames for to-many relationships
        """

    @property
    @abstractmethod
    def instance_id(self) -> Optional[str]:
        """The (potentially None) id of this model instance"""

    @property
    @abstractmethod
    def instance_attributes(self) -> dict[str, Any]:
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

        @classmethod
        def get_column(cls, name: str) -> MappedColumn:
            if name not in inspect(cls).attrs:
                raise BadColumnError(cls, name)
            return getattr(cls, name)

        @classmethod
        def get_to_many_relationship_config(cls) -> dict[str, str]:
            relationships = inspect(cls).relationships
            return {
                cls.__get_relationshship_name(r): cls.__get_relationship_target(r)
                for r in relationships
                if cls.__is_to_many_relationship(r)
            }

        @classmethod
        def get_to_one_relationship_config(cls) -> dict[str, str]:
            relationships = inspect(cls).relationships
            return {
                cls.__get_relationshship_name(r): cls.__get_relationship_target(r)
                for r in relationships
                if cls.__is_to_one_relationship(r)
            }

        @property
        def instance_id(self) -> Optional[str]:
            id_key = self.get_id_column_name()
            id_val = getattr(self, id_key)
            return None if id_val is None else str(id_val)

        @property
        def instance_attributes(self) -> dict[str, Any]:
            return {
                k: getattr(self, k)
                for k in self.__get_attribute_names()
            }

        @classmethod
        def __get_relationshship_name(cls, relationship) -> str:
            return str(relationship).split('.')[-1]

        @classmethod
        def __get_relationship_target(cls, relationship) -> str:
            return list(relationship.remote_side)[0].table.name

        @classmethod
        def __get_all_relationship_names(cls) -> List[str]:
            mapper = inspect(cls)
            return list(mapper.relationships.keys())

        @classmethod
        def __is_to_one_relationship(cls, relationship) -> bool:
            return relationship.direction == RelationshipDirection.MANYTOONE

        @classmethod
        def __is_to_many_relationship(cls, relationship) -> bool:
            return relationship.direction in (
                RelationshipDirection.ONETOMANY,
                RelationshipDirection.MANYTOMANY
            )

        @classmethod
        def __get_foreign_keys(cls) -> List[str]:
            attrs = inspect(cls).attrs
            return [
                k for k, v in attrs.items()
                if isinstance(v, ColumnProperty)
                and getattr(cls, k).foreign_keys
            ]

        @classmethod
        def __get_attribute_names(cls) -> List[str]:
            id_key = cls.get_id_column_name()
            mapper = inspect(cls)
            relationships = cls.__get_all_relationship_names()
            foreign_keys = cls.__get_foreign_keys()
            return [
                k for k in mapper.attrs.keys()
                if k != id_key
                and k not in relationships
                and k not in foreign_keys
            ]

    return ModelBase
