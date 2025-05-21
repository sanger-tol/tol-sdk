# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections import ChainMap
from collections.abc import Mapping
from typing import Any, Iterable

from yaml import safe_load

from .model import (
    AttributeConfig,
    DestinationConfig,
    YamlConfig,
)
from ..core import (
    DataObject,
    DataObjectFactory,
    DataObjectToDataObjectOrUpdateConverter,
)


class TOSConverter(DataObjectToDataObjectOrUpdateConverter):
    """
    Used for Tree of Sex.

    Converts `DataObject` instances dynamically, according to
    a YAML specification.
    """

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        yaml_path: str,
        *,
        destination_object_type: str | None = None,
        pydantic_class: type[YamlConfig] = YamlConfig,
    ) -> None:

        super().__init__(data_object_factory)

        self.__config = self.__load_yaml(
            yaml_path,
            pydantic_class,
        )
        self.__dest_type = destination_object_type

    def convert(
        self,
        input_: DataObject
    ) -> Iterable[DataObject]:

        attributes = self.__convert_attributes(
            input_,
        )
        destination_type = self.__get_destination_type(
            input_,
        )

        yield self._data_object_factory(
            destination_type,
            id_=input_.id,
            attributes=attributes,
        )

    def __get_destination_type(
        self,
        input_: DataObject,
    ) -> str:

        if self.__dest_type:
            return self.__dest_type
        else:
            return input_.type

    def __convert_attributes(
        self,
        input_: DataObject
    ) -> dict[str, Any]:

        attr_pairs = (
            self.__convert_attribute(
                input_,
                attribute_config,
            )
            for attribute_config
            in self.__config.attributes
        )

        return dict(attr_pairs)

    def __convert_attribute(
        self,
        input_: DataObject,
        attribute_config: AttributeConfig,
    ) -> tuple[str, Any]:

        # TODO support one in, multiple out

        split_values = self.__get_split_values(
            input_,
            attribute_config,
        )

        seperator = attribute_config.destination.separator

        converted = seperator.join(
            self.__convert_split_values(
                split_values,
                attribute_config,
            )
        )

        return attribute_config.destination.key, converted

    def __get_split_values(
        self,
        input_: DataObject,
        attribute_config: AttributeConfig,
    ) -> list[str]:

        value: str = getattr(
            input_,
            attribute_config.imported_column_name,
        )

        return value.split(
            attribute_config.destination.separator,
        )

    def __get_value_map(
        self,
        attribute_config: AttributeConfig,
    ) -> dict[str, str]:

        maps = [
            a
            for a
            in attribute_config.destination.imported_values
            if isinstance(a, Mapping)
        ]

        return dict(
            ChainMap(*maps)
        )

    def __convert_split_values(
        self,
        values: list[str],
        attribute_config: AttributeConfig,
    ) -> list[str]:

        value_map = self.__get_value_map(
            attribute_config,
        )

        return [
            value_map[v] if v in value_map else v
            for v in values
            if self.__include_split_value(
                v,
                attribute_config,
                value_map,
            )
        ]

    def __include_split_value(
        self,
        value: str,
        attribute_config: AttributeConfig,
        value_map: dict[str, str],
    ) -> bool:

        d = attribute_config.destination

        if value in d.ignore:
            return False

        if value in d.imported_values or value in value_map:
            return True

        return self.__allowed_magic_type(
            value,
            d,
        )

    def __allowed_magic_type(
        self,
        value: str,
        destination_config: DestinationConfig,
    ) -> bool:

        for t in destination_config.magic_types:
            try:
                t(value)
                return True
            except ValueError:
                continue

        return False

    def __load_yaml(
        self,
        yaml_path: str,
        pydantic_class: type[YamlConfig],
    ) -> YamlConfig:

        with open(yaml_path, 'r') as yaml_file:
            loaded = safe_load(yaml_file)

        return pydantic_class(**loaded)
