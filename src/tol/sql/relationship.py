# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type

from .converter import TypeFunction
from .model import Model
from ..core.relationship import RelationshipConfig


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

    def __init__(self, models: List[Model], type_function: TypeFunction) -> None:
        self.__models = models
        self.__models_dict = {
            m.get_table_name(): m for m in self.__models
        }
        self.__type_function = type_function

    def to_dict(self) -> Optional[Dict[str, RelationshipConfig]]:

        configs = (
            self.__config_from_model(model) for model in self.__models
        )
        dict_config = {
            k: v for k, v in configs if v is not None
        }
        return dict_config if dict_config else None

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
