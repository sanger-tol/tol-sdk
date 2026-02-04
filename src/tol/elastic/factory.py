# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from . import ElasticDataSource
from .client import ElasticClient
from .converter import ElasticApiConverter
from .parser import DefaultParser
from ..core import (
    AttributeMetadata,
    DefaultAttributeMetadata
)
from ..core.relationship import RelationshipConfig


class ElasticApiConverterFactoryManager:
    """
    Wow, what a class name.
    The purpose of this class is to provide `elastic_converter_factory`, a function passed to
    `ElasticDataSource` that manages the instantiation of an `ElasticApiConverter`.
    The reason we need this manager class around that function is because `ElasticApiConverter`
    can't be instantiated until we already have an instance of `ElasticDataSource`. So this class
    is instantiated, then its `elastic_converter_factory` method is provided to `ElasticDataSource`
    when that is instantiated, then the `data_source` property is set, then we're done.
    """
    __slots__ = ['__data_source']
    __data_source: ElasticDataSource | None

    def __init__(self) -> None:
        # The converter factory is instantisated before the data source, so this must be assigned
        # after initialisation. Therefore, if `None`, the data source hasn't been instantiate yet
        self.__data_source = None

    @property
    def data_source(self) -> ElasticDataSource | None:
        """
        Fetch the data source, or `None` if it hasn't been instantiated yet
        """
        return self.__data_source

    @data_source.setter
    def data_source(self, data_source: ElasticDataSource) -> None:
        self.__data_source = data_source

    def elastic_converter_factory(self) -> ElasticApiConverter:
        if self.data_source is None:
            raise Exception(
                "TOL INTERNAL ERROR: elastic_converter_factory called before the data_source "
                "was assigned in _ConverterFactoryManager"
            )

        parser = DefaultParser(self.data_source)
        return ElasticApiConverter(parser)


def _client_factory() -> ElasticClient:
    """
    A resonable default for creating
    an `ElasticApiClient` instance
    """
    # TODO
    raise NotImplementedError(
        '`ElasticClient` hasn\'t been made yet, so this function cannot be implemented, '
        'but it is useful in the construction of `ElasticDataSource` to have this function present'
    )


def create_elastic_datasource(
    config: dict,
    attribute_metadata: AttributeMetadata = DefaultAttributeMetadata,
    relationship_cfg: dict[str, RelationshipConfig] | None = None,
    runtime_fields: dict[str, Any] = {}
) -> ElasticDataSource:
    """
    Properly instaniates an ElasticDataSource
    using the configuration required for the client
    """
    client_factory = _client_factory
    manager = ElasticApiConverterFactoryManager()
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
