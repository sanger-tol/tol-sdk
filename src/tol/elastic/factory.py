# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Iterator, Mapping

if typing.TYPE_CHECKING:
    from . import ElasticDataSource


# class _ElasticDSDict(Mapping):
#     """
#     A wrapper around an `ElasticDataSource` that only
#     lets you access it if you provide on object type
#     supported by the data source. This class masquerades as a dictionary
#     (and is considered as a `dict` type in the Parser),
#     so you go about this via a key access using square brackets.
#     I'm not quite sure why it's done like this, but as the code is
#     set up right now all data sources need to use this pattern.
#     """
#     __slots__ = ['__data_source']
#     __data_source: ElasticDataSource

#     def __init__(self, data_source: ElasticDataSource) -> None:
#         self.__data_source = data_source
    
#     def __getitem__(self, key: str) -> ElasticDataSource:
#         if key not in self.__data_source.supported_types:
#             raise KeyError()
#         return self.__data_source

#     def __iter__(self) -> Iterator:
#         return iter(self.__data_source.supported_types)

#     def __len__(self) -> int:
#         return len(self.__data_source.supported_types)


class _ConverterFactory:
    """
    Manages the instantiation of `ElasticApiConverter`
    """
    pass


class _FilterFactory:
    """
    Manages the instantiation of `ElasticFilterConverter`
    """
    pass


def _get_client_factory():
    """
    A resonable default for creating
    an `ElasticApiClient` instance
    """
    pass


def create_elastic_datasource():
    """
    Properly instaniates an ElasticDataSource
    using the configuration required for the client
    """
    pass
