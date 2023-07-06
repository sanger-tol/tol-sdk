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

    def convert_iterable(
        self,
        models: Iterable[Optional[Model]]
    ) -> Iterable[Optional[DataObject]]:
        """
        Uses the end-user defined `convert()` method to convert
        an `Iterable` of `Optional[Model]` instances to an `Iterable`
        of `Optional[DataObject]` instances.

        If the input `Model` instance is `None`, then so is the
        output `DataObject`.
        """

        return (
            self.convert_optional(m) for m in models
        )

    def convert_optional(
        self,
        model: Optional[Model]
    ) -> Optional[DataObject]:
        """Uses `convert()`, but supports the input being `None`"""

        if model is None:
            return None
        else:
            return self.convert(model)

    @abstractmethod
    def convert(self, model: Model) -> DataObject:
        """
        Converts a Model instance to a DataObject instance. If the
        input could be None, use `convert_optional()` instead.
        """


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

    def convert(self, model: Model) -> DataObject:
        type_ = self.__type_function(model)
        return self.__data_object_factory(
            type_,
            id_=model.instance_id,
            data=model.instance_attributes
        )
