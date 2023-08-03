# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC

from .dumper import RelationDict
from ..api_base2.parser import JsonApiResource
from ..core.converter import Converter
from ..core import DataObject


class Parser(Converter[JsonApiResource, DataObject], ABC):
    """
    Deserializes `DataObject` instances from `JsonApiResource`
    dumps.
    """
