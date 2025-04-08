# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any, Callable, Optional, TypeVar

from .model import Model
from ..core import DataObject
from ..core.core_converter import Converter
from ..core.factory import DataObjectFactory


TypeFunction = Callable[[Model], str]
"""Takes a Model instance, and returns the corresponding DataObject type."""


In = TypeVar('In')
"""The input representation type"""


Out = TypeVar('Out')
"""The output representation type"""


class ModelConverter(Converter[Model, DataObject], ABC):
    """
    Converts Sqlalchemy model instances to DataObject instances.
    """


class DefaultModelConverter(ModelConverter):

    def __init__(
        self,
        type_function: TypeFunction,
        data_object_factory: DataObjectFactory,
        max_depth: int = 1,
        requested_fields: list[str] | None = None,
    ) -> None:
        """
        Takes a type_function Callable, which determines the type of the
        DataObject for a given Model instance.
        """

        self.__type_function = type_function
        self.__data_object_factory = data_object_factory

        self.__requested_fields = requested_fields
        self.__max_depth = (
            None
            if self.__requested_fields
            else max_depth
        )

    def convert(self, model: Model) -> DataObject:
        return self.__convert_to_max_depth(
            model,
            self.__initial_marker
        )

    def __convert_to_max_depth(
        self,
        model: Model | None,
        marker: int
    ) -> DataObject:

        if model is None:
            return None

        type_ = self.__type_function(model)

        return self.__data_object_factory(
            type_,
            id_=model.instance_id,
            attributes=model.instance_attributes,
            to_one=self.__convert_to_ones(
                model,
                marker
            )
        )

    @property
    def __initial_marker(self) -> int | str:
        return (
            ''
            if self.__requested_fields
            else 0
        )

    def __convert_to_ones(
        self,
        model: Model,
        marker: int | str
    ) -> dict[str, Optional[DataObject]]:

        if self.__max_depth and marker >= self.__max_depth:
            return {}

        return {
            k: self.__convert_to_max_depth(
                model.instance_to_one_relations[k],
                self.__get_next_marker(
                    k,
                    marker,
                )
            )
            for k in self.__get_requested_to_ones(
                model,
                marker,
            )
        }

    def __get_next_marker(
        self,
        k: str,
        marker: int | str
    ) -> int | str:

        if self.__requested_fields:
            return f'{marker}.{k}' if marker else k
        else:
            return marker + 1

    def __get_requested_to_ones(
        self,
        model_instance: Model,
        marker: int | str
    ) -> list[str]:

        all_keys = list(
            model_instance.get_to_one_relationship_config().keys()
        )

        if not self.__requested_fields:
            return all_keys

        return [
            k for k in all_keys
            if self.__requested_to_one(k, marker)
        ]

    def __requested_to_one(
        self,
        k: str,
        marker: int | str
    ) -> bool:

        next_marker = self.__get_next_marker(
            k,
            marker,
        )

        return any(
            r.startswith(next_marker)
            for r in self.__requested_fields
        )


class DataObjectConverter(Converter[DataObject, Model], ABC):
    """
    Converts `DataObject` instances to `Model` instances.
    """


class DefaultDataObjectConverter(DataObjectConverter):

    def __init__(
        self,
        type_models_dict: dict[str, type[Model]]
    ) -> None:
        """
        `type_models_dict` maps object type to the
        corresponding `type[Model]` class.
        """

        self.__models_dict = type_models_dict

    def convert(self, input_: DataObject) -> Model:
        model_class = self.__models_dict[input_.type]

        return model_class(
            **self.__get_id_dict(input_.id, model_class),
            **input_.attributes,
            **self.__get_relation_dict(
                model_class,
                input_._to_one_objects
            )
        )

    def __get_id_dict(
        self,
        id_: str,
        model_class: type[Model]
    ) -> dict[str, str]:

        id_column_name = model_class.get_id_column_name()
        return {id_column_name: id_}

    def __get_relation_dict(
        self,
        model_class: type[Model],
        ones: dict[str, DataObject]
    ) -> dict[str, str]:
        # TODO validation - relationship names and their types

        return {
            model_class.get_foreign_key_name(
                rel_name
            ): self.__map_to_foreign_key(rel_obj)
            for rel_name, rel_obj in ones.items()
        }

    def __map_to_foreign_key(
        self,
        rel_obj: DataObject | None
    ) -> Any | None:

        return (
            None if rel_obj is None else rel_obj.id
        )
