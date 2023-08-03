# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from ..api_base2.parser import JsonApiResource
from ..core.converter import Converter
from ..core import DataObject


class Dumper(Converter[DataObject, JsonApiResource], ABC):
    """
    Serializes `DataObject` instances to `JsonApiResource`
    dumps.
    """


class DefaultDumper(Dumper):
    def convert(self, input_: DataObject) -> JsonApiResource:
        pass
