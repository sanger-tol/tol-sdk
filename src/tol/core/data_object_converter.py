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

    def convert_iterable(
        self,
        inputs: Iterable[DataObject | DataObjectUpdate]
    ) -> Iterable[DataObject]:
        return flatten((self.convert(i) for i in inputs))

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

    def convert(self, data_object: DataObject) -> Iterable[DataObject]:
        """
        A "passthrough" converter only dealing with attributes:
            None: ignored
            DataObject
            Iterable of DataObjects
        """
        if data_object.id is not None:
            ret = self._data_object_factory(
                id_=data_object.id,
                type_=self.data_loader._destination_object_type,
                attributes={**data_object.attributes}
            )
            return iter([ret])
        return iter([])
