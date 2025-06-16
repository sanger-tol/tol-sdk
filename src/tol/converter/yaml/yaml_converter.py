# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections import ChainMap
from pathlib import Path
from typing import Any, Iterable

from yaml import safe_load

from .model import (
    AttributeConfig,
    DestinationConfig,
    YamlConfig,
)
from ...core import (
    DataObject,
    DataObjectFactory,
    DataObjectToDataObjectOrUpdateConverter,
)


class YamlConverter(DataObjectToDataObjectOrUpdateConverter):
    """
    Used for Tree of Sex.

    Converts `DataObject` instances dynamically, according to
    a YAML specification.
    """

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        yaml_path: str | Path,
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

        attr_dicts = [
            self.__convert_attribute(
                input_,
                attribute_config,
            )
            for attribute_config
            in self.__config.attributes
        ]

        return dict(
            ChainMap(*attr_dicts)
        )

    def __convert_attribute(
        self,
        input_: DataObject,
        attribute_config: AttributeConfig,
    ) -> dict[str, Any]:

        pairs = [
            self.__convert_destination(
                input_,
                d,
                attribute_config.imported_column_name,
            )
            for d in self.__get_destinations(
                attribute_config,
            )
        ]

        return dict(pairs)

    def __get_destinations(
        self,
        attribute_config: AttributeConfig
    ) -> list[DestinationConfig]:

        if isinstance(attribute_config.destination, DestinationConfig):
            return [attribute_config.destination]
        else:
            return attribute_config.destination

    def __convert_destination(
        self,
        input_: DataObject,
        destination_config: DestinationConfig,
        imported_column_name: str,
    ) -> tuple[str, Any]:

        if not self.__should_convert_destination(
            input_,
            imported_column_name,
        ):
            __v = getattr(input_, imported_column_name)

            return destination_config.key, __v

        split_values = self.__get_split_values(
            input_,
            destination_config,
            imported_column_name,
        )

        seperator = destination_config.separator

        converted = seperator.join(
            self.__convert_split_values(
                split_values,
                destination_config,
            )
        )

        return destination_config.key, converted

    def __should_convert_destination(
        self,
        input_: DataObject,
        imported_column_name: str,
    ) -> bool:

        __v = getattr(input_, imported_column_name)

        return (
            __v is not None and isinstance(__v, str)
        )

    def __get_split_values(
        self,
        input_: DataObject,
        destination_config: DestinationConfig,
        imported_column_name: str,
    ) -> list[str]:

        value: str = getattr(
            input_,
            imported_column_name,
        )

        return value.split(
            destination_config.separator,
        )

    def __convert_split_values(
        self,
        values: list[str],
        destination_config: DestinationConfig,
    ) -> list[str]:

        value_map = destination_config.imported_values_map

        return [
            value_map[v] if v in value_map else v
            for v in values
            if self.__include_split_value(
                v,
                destination_config,
            )
        ]

    def __include_split_value(
        self,
        value: str,
        destination_config: DestinationConfig,
    ) -> bool:

        if value in destination_config.ignore:
            return False

        if destination_config.magic_match_all:
            return True

        value_map = destination_config.imported_values_map
        if value in value_map:
            return True

        return self.__allowed_magic_type(
            value,
            destination_config,
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
        yaml_path: str | Path,
        pydantic_class: type[YamlConfig],
    ) -> YamlConfig:

        with open(yaml_path, 'r') as yaml_file:
            loaded = safe_load(yaml_file)

        return pydantic_class(**loaded)
