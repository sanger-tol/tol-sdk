# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional

from .model import Model
from ..core import DataObject
from ..core.factory import DataObjectFactory


TypeFunction = Callable[[Model], str]
"""Takes a Model instance, and returns the corresponding DataObject type."""


class Converter(ABC):
    """
    Converts Sqlalchemy model instances to DataObject instances.
    """

    @abstractmethod
    def convert(
        self,
        models: Iterable[Optional[Model]]
    ) -> Iterable[Optional[DataObject]]:
        pass


class DefaultConverter(Converter):

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

    def convert(
        self,
        models: Iterable[Optional[Model]]
    ) -> Iterable[Optional[DataObject]]:

        return (
            self.__convert_model(model) for model in models
        )

    def __convert_model(self, model: Optional[Model]) -> Optional[DataObject]:

        if model is None:
            return None

        type_ = self.__type_function(model)
        return self.__data_object_factory(
            type_,
            id_=model.instance_id,
            data=model.instance_attributes
        )
