# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from dataclasses import dataclass
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
        destination_object_type: str | None = None,
        id_field: str | None = None
    ):

        super().__init__(data_object_factory)
        self.__dest_object_type = destination_object_type
        self.__id_field = id_field

    def convert(
        self,
        data_object: DataObject
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
                    data_object.id if self.__id_field is None
                    else data_object.get_field_by_name(self.__id_field)
                ),
                type_=dest_type,
                attributes={
                    k: v
                    for k, v in data_object.attributes.items()
                    if k != self.__id_field
                }
            )
            yield ret


class SanitisingConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        pass

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        config: Config,
        **kwargs
    ):
        super().__init__(data_object_factory)

    def convert(
        self,
        data_object: DataObject
    ) -> Iterable[DataObject]:
        """
        A converter that removes leading and trailing whitespace from
        string attributes.
        """
        if data_object is not None and data_object.id is not None:
            ret = self._data_object_factory(
                id_=data_object.id,
                type_=data_object.type,
                attributes={
                    k: self.__sanitise(v)
                    for k, v in data_object.attributes.items()
                }
            )
            yield ret

    def __sanitise(
        self,
        value: object
    ) -> object:
        if isinstance(value, str):
            return value.strip()
        return value
