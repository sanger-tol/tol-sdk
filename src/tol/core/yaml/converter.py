# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Iterable

from yaml import safe_load

from .model import YamlConfig
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
        pydantic_class: type[YamlConfig] = YamlConfig,
    ) -> None:

        super().__init__(data_object_factory)

        self.__config = self.__load_yaml(
            yaml_path,
            pydantic_class,
        )

    def convert(
        self,
        input_: DataObject
    ) -> Iterable[DataObject]:

        pass

    def __load_yaml(
        self,
        yaml_path: str,
        pydantic_class: type[YamlConfig],
    ) -> YamlConfig:

        with open(yaml_path, 'r') as yaml_file:
            loaded = safe_load(yaml_file)

            return pydantic_class(**loaded)
