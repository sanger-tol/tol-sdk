# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC


class Parser(ABC):
    """
    Parses Elastic API transfer resource `dict`s to `DataObject` instances
    """
    pass
