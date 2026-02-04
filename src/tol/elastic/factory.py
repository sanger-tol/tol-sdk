# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from . import ElasticDataSource
from .client import ElasticClient
from .converter import ElasticApiConverter
from .parser import DefaultDataObjectParser, DefaultElasticApiParser
from ..core import (
    AttributeMetadata,
    DataObject,
    DefaultAttributeMetadata
)
from ..core.relationship import RelationshipConfig


class _ConverterFactoryManager:
    """
    The purpose of this class is to provide `converter_factory`, a function passed to
    `ElasticDataSource` that manages the instantiation of a converter (i.e. `ElasticApiConverter
    and `DataObjectConverter`). It takes in the types of the converter and parser class so it can
    be reused for both converters.
    The reason we need this manager class around that function is because the parser class (needed
    to instantiate a converter) cannot itself be instantiated until we already have an instance of
    `ElasticDataSource`.
    So, this class is instantiated, then its `converter_factory` method is provided to
    `ElasticDataSource` when that is instantiated, then the `data_source` property is set, then
    we're done.
    """
    __slots__ = ['__data_source', '__ConverterClass', '__ParserClass']
    __data_source: ElasticDataSource | None
    __ConverterClass: type
    __ParserClass: type

    def __init__(self, ConverterClass: type, ParserClass: type) -> None:
        # The factory is instantisated before the data source, so this must be assigned
        # after initialisation. Therefore, if `None`, the data source hasn't been instantiated yet
        self.__data_source = None
        self.__ConverterClass = ConverterClass
        self.__ParserClass = ParserClass

    @property
    def data_source(self) -> ElasticDataSource | None:
        """
        Fetch the data source, or `None` if it hasn't been instantiated yet
        """
        return self.__data_source

    @data_source.setter
    def data_source(self, data_source: ElasticDataSource) -> None:
        """
        The means to link the data source once it has been instantiated
        """
        self.__data_source = data_source

    def converter_factory(self) -> Any:
        """
        Returns the instantiated converter of type self.__ConverterClass
        """
        if self.data_source is None:
            raise Exception(
                f'TOL INTERNAL ERROR: factory function for '
                f'{self.__ConverterClass.__class__.__name__} called before '
                f'the data source was assigned in _ConverterFactoryManager'
            )

        parser = self.__ParserClass(self.data_source)
        return self.__ConverterClass(parser)


def _client_factory() -> ElasticClient:
    """
    A resonable default for creating
    an `ElasticApiClient` instance
    """
    # TODO
    raise NotImplementedError(
        "`ElasticClient` hasn't been made yet, so this function cannot be implemented, "
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
    # Instantiate the factories needed by the data source
    client_factory = _client_factory

    # The converters are different however, as they require a references to the data source itself.
    # Thus, manager objects are used to pass the factory methods to the data source's constructor
    # before its reference is passed in
    elastic_api_converter_factory_manager = _ConverterFactoryManager(
        ElasticApiConverter, DefaultElasticApiParser
    )
    data_object_converter_factory_manager = _ConverterFactoryManager(
        DataObject, DefaultDataObjectParser
    )

    # Instantiate the data source
    elastic_ds = ElasticDataSource(
        config,
        client_factory,
        elastic_api_converter_factory_manager.converter_factory,
        data_object_converter_factory_manager.converter_factory,
        attribute_metadata,
        relationship_cfg,
        runtime_fields
    )

    # Update the converter factory managers so that the converter factories have a references to
    # the now instantiated data source
    elastic_api_converter_factory_manager.data_source = elastic_ds
    data_object_converter_factory_manager.data_source = elastic_ds

    return elastic_ds
