# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from functools import cache
from typing import Optional, Type

from .attribute_metadata import (AttributeMetadata, DefaultAttributeMetadata)
from .data_source_dict import DataSourceDict
from .datasource import DataSource
from .factory import DataSourceDictFactory


def data_source_attribute_metadata(
    *data_sources: DataSource,
    data_source_dict_factory: DataSourceDictFactory = lambda *d: DataSourceDict(*d)
) -> Type[AttributeMetadata]:
    """
    Takes a tuple of DataSource instances, and creates an AbstractMetadata
    implementation that refers to all of them.
    """

    data_source_dict = data_source_dict_factory(*data_sources)

    class DataSourceAttributeMetadata(DefaultAttributeMetadata):
        """
        AbstractMetadata that gets its info from one or more DataSources
        """
        @cache
        def __read_attributes_from_datasource(self):
            ds = data_source_dict['attribute']
            attributes = ds.get_list('attribute')
            ret = {}
            for attribute in attributes:
                if attribute.object_type not in ret:
                    ret[attribute.object_type] = {}
                ret[attribute.object_type][attribute.name] = attribute
            return ret

        def __get_attribute(
                self,
                object_type: str,
                attribute_name: str) -> str:
            attributes = self.__read_attributes_from_datasource()
            if object_type in attributes:
                if attribute_name in attributes[object_type]:
                    return attributes[object_type][attribute_name]
            return None

        def get_display_name(
                self,
                object_type: str,
                attribute_name: str) -> str:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return super().get_display_name(object_type, attribute_name)
            return attribute.display_name

        def is_available_on_relationships(
                self,
                object_type: str,
                attribute_name: str) -> bool:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return False  # available attributes must be in DataSource
            return attribute.available_on_relationships

        def is_authoritative(
                self,
                object_type: str,
                attribute_name: str) -> bool:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return False  # authoritative attributes must be in DataSource
            return attribute.authoritative

        def get_cardinality(
                self,
                object_type: str,
                attribute_name: str) -> Optional[int]:
            return super().get_cardinality(object_type, attribute_name)

        def get_description(
                self,
                object_type: str,
                attribute_name: str) -> Optional[str]:
            attribute = self.__get_attribute(object_type, attribute_name)
            if attribute is None:
                return super().get_description(
                    object_type, attribute_name)
            return attribute.description

    return DataSourceAttributeMetadata
