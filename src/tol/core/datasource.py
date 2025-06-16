# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

from cachetools.func import ttl_cache

from .attribute_metadata import (
    AttributeMetadata,
    DefaultAttributeMetadata
)
from .data_object import DataDict
from .datasource_error import DataSourceError, NoDataObjectFactoryError
from .factory import DataObjectFactory
from .operator import AllOperatorType
from .session import DataSourceSession

if typing.TYPE_CHECKING:
    from .session import OperableSession


DataId = str
DataSourceUpdate = Tuple[DataId, DataDict]
DataSourceConfig = Dict[str, Any]
UserIdGetter = Callable[[], str]


class DataSource(ABC):
    """
    The central class for managing operations on heterogeneous data sources.
    """

    DEFAULT_PAGE_SIZE = 20

    def __init__(
            self,
            config: DataSourceConfig,
            expected: List[str] | None = None,
            attribute_metadata: type[AttributeMetadata] = DefaultAttributeMetadata):
        self.__data_object_factory: Optional[DataObjectFactory] = None
        self.__attribute_metadata = attribute_metadata
        self.__validate_config(config, expected)
        for k, v in config.items():
            setattr(self, k, v)

    @property
    @abstractmethod
    def supported_types(self) -> List[str]:
        """
        The list of types of DataObject supported by this DataSource instance.

        This can either be a static list, or dynamically generated.
        """

    def get_session(self) -> OperableSession:
        """
        Gets a `DataSourceSession` instance. This behaviour is
        `DataSource`-specific, and may be overriden.
        """

        return DataSourceSession(self)

    def __validate_config(
        self,
        config: DataSourceConfig,
        expected: List[str] | None,
    ):
        if expected is None:
            return
        for k in expected:
            if k not in config:
                raise DataSourceError(
                    title='Incorrect configuration',
                    detail=f'{k} missing in config dict'
                )

    def get_page_size(self) -> int:
        return getattr(self, 'page_size', self.DEFAULT_PAGE_SIZE)

    def get_attribute_types(self, object_type: str) -> dict[str, str]:
        """
        DEPRECATED - use the `DataSource().attribute_types` property
        instead.

        The types (str, int, etc) of the attributes of an object_type.

        This can either be a static list, or dynamically generated.
        """

        return self.attribute_types[object_type]

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        """
        The `dict` mapping supported types to the (python) types of
        their attributes.

        This can either be a static `dict`, or dynamically generated.
        """

        return {}

    @property
    @ttl_cache(ttl=86400)
    def attribute_metadata(self) -> dict[str, dict[str, dict[str, Optional[str | bool]]]]:
        """
        Information about the attributes:
            python_type
            display_name
            available_on_relationships
        """
        ret: dict[str, dict[str, dict[str, Any]]] = {}
        am = self.__attribute_metadata()
        for object_type, attribute in self.attribute_types.items():
            ret[object_type] = {}
            for attribute_name, attribute_type in attribute.items():
                ret[object_type][attribute_name] = {
                    'python_type': attribute_type,
                    'display_name': am.get_display_name(object_type, attribute_name),
                    'description': am.get_description(object_type, attribute_name),
                    'cardinality': am.get_cardinality(object_type, attribute_name),
                    'authoritative': am.is_authoritative(object_type, attribute_name),
                    'source': am.get_source(object_type, attribute_name),
                    'available_on_relationships':
                        am.is_available_on_relationships(
                            object_type,
                            attribute_name)
                }
        return ret

    def get_attribute_metadata_by_name(self, obj_type: str, field_name: str) -> Any:
        """
        Get attribute_metadata by name, or return `None` if the field does not exist.
        """
        # Split by dots to allow for nested fields
        field_names = field_name.split('.')
        current_obj_type = obj_type
        for name in field_names:
            # It may be an attribute of the current object type
            if name in self.attribute_metadata[current_obj_type]:
                return self.attribute_metadata[current_obj_type][name]
            # ...or a to_one relation
            if current_obj_type in self.relationship_config and \
                    self.relationship_config[current_obj_type].to_one is not None:
                if name in self.relationship_config[current_obj_type].to_one:
                    current_obj_type = self.relationship_config[current_obj_type].to_one[name]
                    continue
            return None
        return None

    @property
    def data_object_factory(self) -> DataObjectFactory:
        """A callable that returns a new DataObject for the given type."""

        if self.__data_object_factory is None:
            raise NoDataObjectFactoryError(
                'The `data_object_factory` setter must be called before a '
                'DataSource instance can be used. The standard way to do '
                'this is to collect all of the DataSource instances, and '
                'provide them to the `core_data_object` function.'
            )

        return self.__data_object_factory

    @data_object_factory.setter
    def data_object_factory(
        self,
        data_object_factory: DataObjectFactory
    ) -> None:
        """Sets the factory for creating new DataObject instances"""

        self.__data_object_factory = data_object_factory


class OperableDataSource(DataSource, AllOperatorType):
    """A type hint. For inheriting, use DataSource"""
