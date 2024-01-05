# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import (
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar
)

from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from .sql_converter import TypeFunction
    from .model import Model


class SqlRelationshipConfig(ABC):
    """
    Describes the relationships, to-one and to-many, between
    DataObject instances fulfilled by Model classes within
    SqlDataSource.
    """

    @abstractmethod
    def to_dict(self) -> Optional[Dict[str, RelationshipConfig]]:
        """
        Converts this config to a dictionary representation,
        mapping DataObject types to their individual
        RelationshipConfig instance.
        """


class DefaultSqlRelationshipConfig(ABC):

    def __init__(self, models: List[Type[Model]], type_function: TypeFunction) -> None:
        self.__models = models
        self.__models_dict = {
            m.get_table_name(): m for m in self.__models
        }
        self.__type_function = type_function

    def to_dict(self) -> Dict[str, RelationshipConfig]:

        configs = (
            self.__config_from_model(model) for model in self.__models
        )
        return {
            k: v for k, v in configs if v is not None
        }

    def __config_from_model(self, model: Type[Model]) -> Optional[RelationshipConfig]:

        object_type = self.__type_function(model)
        to_one = model.get_to_one_relationship_config()
        to_many = model.get_to_many_relationship_config()

        if not to_one and not to_many:
            return object_type, None
        else:
            return object_type, RelationshipConfig(
                to_one=self.__map_config(to_one),
                to_many=self.__map_config(to_many)
            )

    def __map_config(self, config: Dict[str, str]) -> Dict[str, str]:

        return {
            k: self.__type_function(self.__models_dict[v])
            for k, v in config.items()
        }


V = TypeVar('V')


class InstanceRelationDict(Mapping, Generic[V], ABC):
    def __init__(self, source: Model) -> None:
        self.__source = source

    def __iter__(self) -> Iterator[str]:
        return iter(self.config)

    def __len__(self) -> int:
        return len(self.config)

    def __getitem__(self, __k: str) -> V:
        if __k not in self.config:
            raise KeyError()
        return getattr(self.source, __k)

    @property
    def source(self) -> Model:
        """The source model for this `dict`"""

        return self.__source

    @property
    @abstractmethod
    def config(self) -> dict[str, str]:
        """
        The relevant relationship config for this `dict`
        """
