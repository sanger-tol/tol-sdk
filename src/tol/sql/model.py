# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABCMeta
from datetime import datetime
from functools import cache
from types import MappingProxyType  # A read-only dict
from typing import Any, Iterable, Optional, Type

from sqlalchemy import JSON, inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import (
    Mapped,
    MappedColumn,
    RelationshipDirection,
    declarative_base,
    declared_attr,
    mapped_column
)

from .exception import BadColumnError
from .relationship import InstanceRelationDict
from ..core import DataSourceError


class Model:
    """
    A model that can be converted to DataObject instances.

    The properties can be implemented in many different ways, but
    are necessary on every child class that is exposed to
    SqlDataSource.

    Relationships that start with an underscore (e.g. `User._tokens`)
    will be ignored by these methods.
    """

    @classmethod
    def get_table_name(cls) -> str:  # noqa
        """The name of the Model"""

    @classmethod
    def get_id_column_name(cls) -> str:  # noqa
        """
        The name of the column that serves as the "id".
        Override this classmethod to change.
        """

    @classmethod
    def get_column(cls, name: str) -> MappedColumn:
        """The (attribute) column for the given name."""

    @classmethod
    def get_to_one_relationship_config(cls) -> dict[str, str]:
        """
        The mapping of relationship names to tablenames for to-one relationships
        """

    @classmethod
    def get_to_many_relationship_config(cls) -> dict[str, str]:
        """
        The mapping of relationship names to tablenames for to-many relationships
        """

    @classmethod
    def get_attribute_types(cls) -> dict[str, type]:
        """
        The mapping of attribute names to their datatype in python
        """

    @classmethod
    def get_foreign_key_name(cls, relationship_name: str) -> str:
        """
        The name of the foreign key column for the given relationship name
        """

    @classmethod
    def get_all_foreign_key_names(cls) -> set[str]:
        """
        Returns only the names of columns which are foreign keys used in
        relationsips.
        """

    def before_commit(self, user_id: Optional[str] = None) -> None:
        """
        The method that is called by a `Database` instance before a commit
        """

    @classmethod
    def get_excluded_column_names(cls) -> list[str]:
        """
        The list of column names that both exist on the model, but
        shouldn't be automatically added to `Model().instance_attributes`.
        """

        return [
            cls.get_id_column_name()
        ]

    @property
    def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
        """
        The mapping of relationship names to to-one relation rows
        """

    @property
    def instance_to_many_relations(self) -> dict[str, Iterable[Model]]:
        """
        The mapping of relationship names to to-many relation rows
        """

    @property
    def instance_id(self) -> Optional[str]:
        """The (potentially None) id of this model instance"""

    @property
    def instance_attributes(self) -> dict[str, Any]:
        """The Dict of attribute key to values"""


class InstanceToOneDict(
    InstanceRelationDict[Optional[Model]]
):
    """
    A useful concretion for the to-one instance relationship dict
    """

    @property
    def config(self) -> dict[str, str]:
        return self.source.get_to_one_relationship_config()


class InstanceToManyDict(
    InstanceRelationDict[Iterable[Model]]
):
    """
    A useful concretion for the to-many instance relationship dict
    """

    @property
    def config(self) -> dict[str, str]:
        return self.source.get_to_many_relationship_config()


class DefaultModel(Model):
    Log: Model
    """
    An inherited class that logs changes to its fields:
    - when
    - by whom
    """


def model_base() -> Type[DefaultModel]:
    """
    Creates a new base for Model classes that implement the Model ABC.
    """

    class ModelMeta(DeclarativeMeta, ABCMeta):
        pass

    DeclarativeBase = declarative_base(  # noqa N806
        metaclass=ModelMeta,
        type_annotation_map={
            dict: JSON,
            dict[str, Any]: JSON
        }
    )

    class ModelBase(DeclarativeBase, DefaultModel):
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
            if name not in inspect(cls).mapper.attrs:
                raise BadColumnError(cls, name)
            return getattr(cls, name)

        @classmethod
        @cache
        def get_to_many_relationship_config(cls) -> MappingProxyType[str, str]:
            relationships = inspect(cls).relationships
            all_ = {
                r.key: cls.__get_relationship_target(r)
                for r in relationships
                if cls.__is_to_many_relationship(r)
            }
            return MappingProxyType({
                k: v for k, v in all_.items()
                if not k.startswith('_')
            })

        @classmethod
        @cache
        def get_to_one_relationship_config(cls) -> MappingProxyType[str, str]:
            relationships = inspect(cls).relationships
            all_ = {
                r.key: cls.__get_relationship_target(r)
                for r in relationships
                if cls.__is_to_one_relationship(r)
            }
            return MappingProxyType({
                k: v for k, v in all_.items()
                if not k.startswith('_')
            })

        @classmethod
        def get_foreign_key_name(cls, relationship_name: str) -> str:
            # TODO refactor `Database().get_to_one_relation()` to use this
            foreign_key = cls.__get_foreign_key(relationship_name)
            return foreign_key.name

        @classmethod
        @cache
        def get_attribute_types(cls) -> MappingProxyType[str, type]:
            names = cls.__get_attribute_names()
            columns = inspect(cls).columns
            return MappingProxyType({
                k: columns[k].type.python_type for k in names
            })

        @classmethod
        def get_id_attribute_type(cls) -> dict[str, type]:
            columns = inspect(cls).columns
            return columns[cls.get_id_column_name()].type.python_type

        @property
        def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
            config = self.get_to_one_relationship_config()
            return self.__get_attributes_map(config)

        @property
        def instance_to_many_relations(self) -> dict[str, Iterable[Model]]:
            config = self.get_to_many_relationship_config()
            return self.__get_attributes_map(config)

        @property
        def instance_id(self) -> Optional[str]:
            id_key = self.get_id_column_name()
            id_val = getattr(self, id_key)
            return None if id_val is None else str(id_val)

        @property
        def instance_attributes(self) -> dict[str, Any]:
            names = self.__get_attribute_names()
            return self.__get_attributes_map(names)

        @classmethod
        def __get_foreign_key(
            cls,
            relationship_name: str
        ) -> MappedColumn:
            """
            Returns the local foreign key column given a relationship name
            """

            rel = inspect(cls).relationships[relationship_name]
            all_cols = tuple(rel.local_columns)
            if len(all_cols) != 1:
                raise NotImplementedError('Composite keys are not supported.')
            return all_cols[0]

        def __get_attributes_map(
            self,
            names: Iterable[str]
        ) -> dict[str, Any]:

            return {
                name: getattr(self, name) for name in names
            }

        @classmethod
        def __get_relationship_target(cls, relationship) -> str:
            return relationship.entity.tables[0].name

        @classmethod
        def __get_all_relationship_names(cls) -> list[str]:
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
        @cache
        def get_all_foreign_key_names(cls) -> frozenset[str]:
            """
            Returns only the names of columns which are foreign keys used in
            relationsips. i.e. To-one relationships.
            """

            col_to_attr = cls.__get_column_name_to_attribute_map()

            foreign_keys = set()
            for rel in inspect(cls).relationships:
                for col in rel.local_columns:
                    # If it is really a foreign key, get the name of the
                    # attribute in the model
                    if len(col.foreign_keys) > 0 and (attr_name := col_to_attr.get(col.name)):
                        foreign_keys.add(attr_name)
            return frozenset(foreign_keys)

        @classmethod
        def __get_column_name_to_attribute_map(cls) -> dict[str, str]:
            """
            Returns a dict mapping database column names to this model's
            attribute names.
            """

            return {
                col_prop.columns[0].name: col_prop.key
                for col_prop in inspect(cls).column_attrs
            }

        @classmethod
        @cache
        def __get_attribute_names(cls) -> tuple[str]:
            excluded = cls.get_excluded_column_names()
            mapper = inspect(cls)
            relationships = cls.__get_all_relationship_names()
            foreign_keys = cls.get_all_foreign_key_names()
            return tuple(
                k for k in mapper.attrs.keys()  # noqa: SIM118
                if k not in excluded
                and k not in relationships
                and k not in foreign_keys
            )

    class LogBase(ModelBase):
        """
        Logs changes to its columns. (by whom/when)
        """

        __abstract__ = True

        @declared_attr
        def modified_at(self) -> Mapped[datetime]:
            return mapped_column(nullable=True)

        @declared_attr
        def modified_by(self) -> Mapped[str]:
            return mapped_column(nullable=True)

        def before_commit(
            self,
            *,
            user_id: Optional[str]
        ) -> None:

            if user_id is None:
                self.__raise_unknown_user()
            self.__update_log_fields(user_id)

        def __update_log_fields(
            self,
            user_id: str
        ) -> None:

            self.modified_by = user_id
            self.modified_at = datetime.now()

        def __raise_unknown_user(self) -> None:
            raise DataSourceError(
                title='Unauthenticated',
                detail='No user identified for this change.',
                status_code=401
            )

    ModelBase.Log = LogBase

    return ModelBase
