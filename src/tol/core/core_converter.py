# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, TypeVar

from .data_object import DataObject
from .datasource import DataSource


In = TypeVar('In')
"""The input representation type"""


Out = TypeVar('Out')
"""The output representation type"""


class Converter(ABC, Generic[In, Out]):
    """
    A useful `ABC` for converting from one representation to another.
    """

    def convert_iterable(
        self,
        inputs: Iterable[Optional[In]]
    ) -> Iterable[Optional[Out]]:
        """
        Converts an `Iterable` of (possibly `None`) input representations
        to an `Iterable` of (possibly `None`) output representations,
        according to the rules of `convert_optional()`
        """

        return (self.convert_optional(i) for i in inputs)

    def convert_optional(self, input_: Optional[In]) -> Optional[Out]:
        """
        Converts a possibly `None` input representation to either:

        - `None` if the input is `None`
        - `convert(input)` if the input is not `None`
        """

        return self.convert(input_) if input_ is not None else None

    @abstractmethod
    def convert(self, input_: In) -> Out:
        """
        Converts an input representation to an output representation.

        If the input could be `None`, use `convert_optional()` instead.
        """


class DataObjectToDataObjectConverter(Converter[DataObject, DataObject], ABC):
    """
    Converts one DataObject to another.
    """


class DefaultDataObjectToDataObjectConverter(DataObjectToDataObjectConverter):

    def convert(self, data_objects: List[DataObject], target_datasource: DataSource) -> DataObject:
        CoreDataObject = target_datasource.data_object_factory # noqa N806
        for data_object in data_objects:
            ret = CoreDataObject(
                id_=data_object.id,
                type_=data_object.type,
                data={**data_object.attributes}
            )
            yield ret
