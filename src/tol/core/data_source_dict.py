# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Mapping
from itertools import chain
from typing import Dict, Iterable, Tuple

from .datasource_error import UnknownObjectTypeException

if typing.TYPE_CHECKING:
    from .datasource import DataSource


class DataSourceDict(Mapping):
    """
    A useful implementation of a Dict[str, DataSource], mapping
    a type of DataObject to its "providing" DataSource, to be injected
    into the constructor of each Controller instance.

    A singleton can be used.
    """

    def __init__(self, *data_sources: DataSource) -> None:
        self.__data_sources = data_sources

    def __getitem__(self, object_type: str) -> DataSource:
        data_source = self.__get_dict().get(object_type)
        if data_source is None:
            raise UnknownObjectTypeException(object_type)
        return data_source

    def __setitem__(self, *args, **kwargs) -> None:
        raise NotImplementedError('This Dict is readonly.')

    def __len__(self) -> int:
        return len(self.__get_dict())

    def __iter__(self) -> Iterable:
        return iter(self.__get_dict())

    def __get_dict(self) -> Dict[str, DataSource]:
        object_tuples = [
            self.__get_pairs_iterable(data_source)
            for data_source in self.__data_sources
        ]
        return dict(chain(*object_tuples))

    def __get_pairs_iterable(
        self,
        data_source: DataSource
    ) -> Iterable[Tuple[str, DataSource]]:
        return [
            (object_type, data_source)
            for object_type in data_source.supported_types
        ]
