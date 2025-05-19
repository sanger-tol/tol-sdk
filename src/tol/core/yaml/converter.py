# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Iterable

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
        config: type[YamlConfig] = YamlConfig,
    ) -> None:

        super().__init__(data_object_factory)

    def convert(
        self,
        input_: DataObject
    ) -> Iterable[DataObject]:

        pass
