# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataObjectToDataObjectOrUpdateConverter, ErrorObject


class ErrorObjectConverter(DataObjectToDataObjectOrUpdateConverter):

    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        include: bool = True

    __slots__ = ['__config']
    __config: Config

    def __init__(self, data_object_factory, config: Config) -> None:
        super().__init__(data_object_factory)
        self.__config = config
        self._data_object_factory = data_object_factory

    def convert(self, data_object: DataObject | ErrorObject) -> Iterable[DataObject | ErrorObject]:
        """
        Include or exclude ErrorObjects based on the `include` config.
        If `include` is True, yield ErrorObjects and discard DataObjects.
        If `include` is False, filters out ErrorObjects.
        """

        if self.__config.include:
            if isinstance(data_object, ErrorObject):
                yield data_object
        else:
            if isinstance(data_object, DataObject):
                yield data_object
