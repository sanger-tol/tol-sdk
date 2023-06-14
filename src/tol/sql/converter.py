# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Callable, Iterable, Optional

from .model import Model
from .sql_data_object import SqlDataObject
from ..core import DataObject


TypeFunction = Callable[[Model], str]


class Converter(ABC):
    """
    Converts Sqlalchemy model instances to DataObject instances.
    """

    @abstractmethod
    def convert(self, models: Iterable[Model]) -> Iterable[DataObject]:
        pass


class DefaultConverter(Converter):

    def __init__(self, type_function: TypeFunction) -> None:
        """
        Takes a type_function Callable, which determines the type of the
        DataObject for a given Model instance.
        """
        self.__type_function = type_function

    def convert(
        self,
        models: Iterable[Optional[Model]]
    ) -> Iterable[Optional[DataObject]]:

        return (self.__convert_model(model) for model in models)

    def __convert_model(
        self,
        model: Optional[Model]
    ) -> Optional[DataObject]:

        if model is None:
            return None

        type_ = self.__type_function(model)
        return SqlDataObject(
            type_,
            id_=model.instance_id,
            data=model.instance_attributes
        )
