# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import typing
from abc import ABC

from ..core import Converter, DataObject, DataObjectFactory

if typing.TYPE_CHECKING:
    from .client import ObjectDump


class ObjectParser(Converter[ObjectDump, DataObject], ABC):
    """Converts object-dumps back to `DataObject` instances"""
