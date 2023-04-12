# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations
from typing import Any, Dict, List

from ..core import DataObject


class ApiDataObjectSerializer:
    """
    Serializes a complex, nested list of DataObjects into
    a flat list of raw data.
    """

    def dump(self, objects: List[DataObject]) -> List[Dict[str, Any]]:
        pass
