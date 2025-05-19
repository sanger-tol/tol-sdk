# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .model import YamlValidatorConfig
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
        config: type[YamlValidatorConfig] = YamlValidatorConfig,
    ) -> None:

        super().__init__(data_object_factory)
