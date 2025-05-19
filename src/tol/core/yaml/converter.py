# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Iterable

from yaml import safe_load

from .model import AttributeConfig, YamlConfig
from ..data_object import DataObject
from ..data_object_converter import (
    DataObjectToDataObjectOrUpdateConverter,
)
from ..datasource import DataObjectFactory


class YamlConverter(DataObjectToDataObjectOrUpdateConverter):
    """
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

        d = attribute_config.destination

        if len(d.import_values) == 1:
            value = getattr(input_, d.import_values[0])
        else:
            value = self.__convert_compound_value(
                input_,
                attribute_config,
            )

        return d.key, value

    def __convert_compound_value(
        self,
        input_: DataObject,
        attribute_config: AttributeConfig,
    ) -> str:

        # TODO need to account for "magic" all/integers

        seperator = attribute_config.destination.separator

        values = (
            getattr(input_, k)
            for k
            in attribute_config.destination.import_values
        )

        return seperator.join(values)

    def __load_yaml(
        self,
        yaml_path: str,
        pydantic_class: type[YamlConfig],
    ) -> YamlConfig:

        with open(yaml_path, 'r') as yaml_file:
            loaded = safe_load(yaml_file)

            return pydantic_class(**loaded)
