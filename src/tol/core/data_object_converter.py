# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Iterable

from more_itertools import flatten

from .data_object import DataObject
from .factory import DataObjectFactory
from .operator.updater import DataObjectUpdate


class DataObjectToDataObjectOrUpdateConverter(ABC):
    """
    This is (currently) not inheriting from Converter as we are changing
    the method signatures (convert() can return None, a DataObject or an
    Iterable of DataObjects)
    """

    def __init__(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:
        """
        Takes a data_object_factory to use for creating new DataObjects
        """
        self._data_object_factory = data_object_factory
        self._return_objects = []

    def convert_iterable(
        self,
        inputs: Iterable[DataObject | DataObjectUpdate]
    ) -> Iterable[DataObject]:
        return flatten((self.convert(i) for i in inputs))

    def get_return_objects(self):
        return self._return_objects

    @abstractmethod
    def convert(self, input_: DataObject) -> Iterable[DataObject | DataObjectUpdate]:
        """
        Converts an input representation to an output representation.
        output can be:
            None: ignored
            DataObject
            Iterable of DataObjects
        """


class DefaultDataObjectToDataObjectConverter(DataObjectToDataObjectOrUpdateConverter):

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        destination_object_type: str | None = None
    ):

        super().__init__(data_object_factory)
        self.__dest_object_type = destination_object_type

    def convert(
        self,
        data_object: DataObject,
        id_field: str | None = None
    ) -> Iterable[DataObject]:
        """
        A "passthrough" converter only dealing with attributes:
            None: ignored
            DataObject
            Iterable of DataObjects
        """
        if data_object is not None and data_object.id is not None:
            dest_type = (
                self.__dest_object_type
                if self.__dest_object_type is not None
                else self.data_loader._destination_object_type
            )
            ret = self._data_object_factory(
                id_=(
                    data_object.id if id_field is None
                    else data_object.get_field_by_name(id_field)
                ),
                type_=dest_type,
                attributes={k: v for k, v in data_object.attributes.items() if k != id_field}
            )
            return iter([ret])
        return iter([])
