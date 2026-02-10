# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from . import ElasticDataSource
from .client import ElasticClient
from .converter import (
    ElasticApiConverter,
    ElasticUpdateInputConverter,
    ElasticUpsertInputConverter,
)
from .parser import (
    DefaultElasticApiParser,
    DefaultElasticUpdateInputParser,
    DefaultElasticUpsertInputParser,
)
from ..core import (
    AttributeMetadata,
    DefaultAttributeMetadata
)
from ..core.relationship import RelationshipConfig


class _ConverterFactoriesManager:
    """
    The purpose of this class is to provide `elastic_api_converter_factory` and
    `data_object_converter_factory`, functions passed to `ElasticDataSource` that manage the
    instantiation of their respective converters (`ElasticApiConverter`, `DataObjectConverter`
    and `DataObjectUpdateConverter`).
    The reason we need this manager class around these factory functions is because the parser
    classes (needed to instantiate the converters) cannot themselves be instantiated until we
    already have an instance of `ElasticDataSource`.
    So, this class is instantiated, then its converter factory methods are provided to the data
    source for its instantiation, then the `data_source` property is set to enable the factory
    functions to work.
    """
    __slots__ = ['__data_source']
    __data_source: ElasticDataSource | None

    def __init__(self) -> None:
        # The factory is instantisated before the data source, so this must be assigned
        # after initialisation. Therefore, if `None`, the data source hasn't been instantiated yet
        self.__data_source = None

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

    def elastic_api_converter_factory(self) -> ElasticApiConverter:
        if self.data_source is None:
            raise Exception(
                'TOL INTERNAL ERROR: factory function for ElasticApiConverter called '
                'before the data source was assigned in _ConverterFactoriesManager'
            )

        parser = DefaultElasticApiParser(self.data_source)
        return ElasticApiConverter(parser)

    def data_object_converter_factory(self) -> ElasticUpsertInputConverter:
        if self.data_source is None:
            raise Exception(
                'TOL INTERNAL ERROR: factory function for DataObjectConverter called '
                'before the data source was assigned in _ConverterFactoriesManager'
            )

        parser = DefaultElasticUpsertInputParser(self.data_source)
        return ElasticUpsertInputConverter(parser)

    def data_object_update_converter_factory(self) -> ElasticUpdateInputConverter:
        if self.data_source is None:
            raise Exception(
                'TOL INTERNAL ERROR: factory function for DataObjectUpdateConverter called '
                'before the data source was assigned in _ConverterFactoriesManager'
            )

        parser = DefaultElasticUpdateInputParser(self.data_source)
        return ElasticUpdateInputConverter(parser)


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
    runtime_fields: dict[str, Any] = {},
    **kwargs,
) -> ElasticDataSource:
    """
    Properly instaniates an ElasticDataSource
    using the configuration required for the client
    """
    # Instantiate the factories needed by the data source
    client_factory = _client_factory

    # The converters are different however, as they require a references to the data source itself.
    # Thus, a manager object is used to pass the factory functions to the data source's
    # constructor before its reference is passed in
    converter_factories_manager = _ConverterFactoriesManager()

    # Instantiate the data source
    elastic_ds = ElasticDataSource(
        config,
        client_factory,
        converter_factories_manager.elastic_api_converter_factory,
        converter_factories_manager.data_object_converter_factory,
        converter_factories_manager.data_object_update_converter_factory,
        attribute_metadata,
        relationship_cfg,
        runtime_fields,
        **kwargs,
    )

    # Update the converter factories manager so that the converter factories have a references to
    # the now instantiated data source
    converter_factories_manager.data_source = elastic_ds

    return elastic_ds
