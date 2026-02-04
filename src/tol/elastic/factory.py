# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any, TYPE_CHECKING

from .converter import ElasticApiConverter
from .parser import DefaultParser
from ..core import (
    AttributeMetadata,
    DataSource,
    DefaultAttributeMetadata
)
from ..core.relationship import RelationshipConfig

# if TYPE_CHECKING:
#     from . import ElasticDataSource
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
    __slots__ = ['__data_source']
    __data_source: DataSource | None  

    def __init__(self) -> None:
        # The converter factory is instantisated before the data source, so this must be assigned
        # after initialisation. Therefore, if `None`, the data source hasn't been instantiate yet
        self.__data_source = None

    @property
    def data_source(self) -> DataSource | None:
        """
        Fetch the data source, or `None` if it hasn't been instantiated yet
        """
        return self.__data_source

    @data_source.setter
    def data_source(self, data_source: DataSource) -> None:
        self.__data_source = data_source

    def elastic_converter_factory(self) -> ElasticApiConverter:
        # TODO CHECK NOT NONE OR USE DICT FROM BEFORE
        parser = DefaultParser(self.data_source)
        return ElasticApiConverter(parser)

    # TODO ds dict


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


def create_elastic_datasource(config: dict, attribute_metadata: AttributeMetadata = DefaultAttributeMetadata,
                 relationship_cfg: dict[str, RelationshipConfig] | None = None,
                 runtime_fields: dict[str, Any] = {}) -> ElasticDataSource:
    """
    Properly instaniates an ElasticDataSource
    using the configuration required for the client
    """
    client_factory = None  # TODO
    manager = _ConverterFactory()
    elastic_ds = ElasticDataSource(
        config,
        client_factory,
        manager.elastic_converter_factory,
        attribute_metadata,
        relationship_cfg,
        runtime_fields
    )

    manager.data_source = elastic_ds

    return elastic_ds
