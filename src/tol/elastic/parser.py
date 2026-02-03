# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from ..core import DataObject, DataSourceParser


ElasticApiResource = dict[str, Any]


class DefaultParser(DataSourceParser[ElasticApiResource]):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    def parse(self, transfer: ElasticApiResource) -> DataObject:
        pass
