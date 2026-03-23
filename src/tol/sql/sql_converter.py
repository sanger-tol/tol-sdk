# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Any, Callable

from .model import Model
from ..core import DataObject, ReqFieldsTree
from ..core.core_converter import Converter
from ..core.factory import DataObjectFactory


TypeFunction = Callable[[Model], str]
"""Takes a Model instance, and returns the corresponding DataObject type."""


class ModelConverter(Converter[Model, DataObject], ABC):
    """
    Converts Sqlalchemy model instances to DataObject instances.
    """


class DefaultModelConverter(ModelConverter):
    def __init__(
        self,
        type_function: TypeFunction,
        data_object_factory: DataObjectFactory,
        requested_tree: ReqFieldsTree,
    ) -> None:
        """
        Takes a type_function Callable, which determines the type of the
        DataObject for a given Model instance.
        """

        self.__type_function = type_function
        self.__data_object_factory = data_object_factory
        self.__requested_tree = requested_tree

    def convert(self, model: Model) -> DataObject:
        if model is None:
            return None
        if tree := self.__requested_tree:
            return self.__convert_requested(model, tree)
        else:
            return self.__data_object_factory(
                self.__type_function(model),
                id_=model.instance_id,
                attributes=model.instance_attributes,
            )

    def __convert_requested(self, model, tree):
        if attr_names := tree.attribute_names:
            attributes = {x: getattr(model, x) for x in attr_names if x != 'id'}
        else:
            attributes = model.instance_attributes

        req_to_ones = self.__convert_to_ones_requested(model, tree)
        req_to_many = self.__convert_to_many_requested(model, tree)

        obj = self.__data_object_factory(
            self.__type_function(model),
            id_=model.instance_id,
            attributes=attributes,
            to_one=req_to_ones,
            to_many=req_to_many,
        )
        return obj

    def __convert_to_ones_requested(self, model, tree):
        to_ones = {}
        for rel_name, remote in model.get_to_one_relationship_config().items():
            one = None
            if sub_tree := tree.get_sub_tree(rel_name):
                if sub_model := getattr(model, rel_name):
                    one = self.__convert_requested(sub_model, sub_tree)
            else:
                # Create a stub DataObject
                rel_col = model.get_foreign_key_name(rel_name)
                if rel_id := getattr(model, rel_col):
                    one = self.__data_object_factory(remote, id_=rel_id)
            to_ones[rel_name] = one
        return to_ones if to_ones else None

    def __convert_to_many_requested(self, model, tree):
        to_manys = {}
        for rel_name in model.get_to_many_relationship_config():
            if sub_tree := tree.get_sub_tree(rel_name):
                to_manys[rel_name] = [
                    self.__convert_requested(x, sub_tree) for x in getattr(model, rel_name)
                ]
        return to_manys if to_manys else None


class DataObjectConverter(Converter[DataObject, Model], ABC):
    """
    Converts `DataObject` instances to `Model` instances.
    """


class DefaultDataObjectConverter(DataObjectConverter):
    def __init__(self, type_models_dict: dict[str, type[Model]]) -> None:
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
            **self.__get_relation_dict(model_class, input_._to_one_objects),
        )

    def __get_id_dict(self, id_: str, model_class: type[Model]) -> dict[str, str]:
        id_column_name = model_class.get_id_column_name()
        return {id_column_name: id_}

    def __get_relation_dict(
        self, model_class: type[Model], ones: dict[str, DataObject]
    ) -> dict[str, str]:
        # TODO validation - relationship names and their types

        return {
            model_class.get_foreign_key_name(rel_name): self.__map_to_foreign_key(rel_obj)
            for rel_name, rel_obj in ones.items()
        }

    def __map_to_foreign_key(self, rel_obj: DataObject | None) -> Any | None:
        return None if rel_obj is None else rel_obj.id
