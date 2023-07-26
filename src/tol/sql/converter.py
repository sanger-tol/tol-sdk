# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC
from typing import Callable

from .model import Model
from ..core import Converter, DataObject
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
        data_object_factory: DataObjectFactory
    ) -> None:
        """
        Takes a type_function Callable, which determines the type of the
        DataObject for a given Model instance.
        """
        self.__type_function = type_function
        self.__data_object_factory = data_object_factory

    def convert(self, model: Model) -> DataObject:
        type_ = self.__type_function(model)
        return self.__data_object_factory(
            type_,
            id_=model.instance_id,
            data=model.instance_attributes
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
            **self.__get_foreign_key_dict(
                input_._to_one_objects,
                model_class
            )
        )

    def __get_id_dict(
        self,
        id_: str,
        model_class: type[Model]
    ) -> dict[str, str]:

        id_column_name = model_class.get_id_column_name()
        return {id_column_name: id_}

    def __get_foreign_key_dict(
        self,
        ones: dict[str, DataObject],
        model_class: type[Model]
    ) -> dict[str, str]:
        # TODO validation - relationship names and their types

        return {
            model_class.get_foreign_key_name(
                relationship_name
            ): relation_object.id
            for relationship_name, relation_object in ones.items()
        }
