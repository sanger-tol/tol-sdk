# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from ..core import DataSourceParser


ElasticApiResource = dict[str, Any]


class DefaultParser(DataSourceParser[ElasticApiResource]):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    pass
