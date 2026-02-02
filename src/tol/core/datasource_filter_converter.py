# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from . import DataSourceFilter


class DataSourceFilterConverter(ABC):
    """
    Converts instances of `DataSourceFilter` to a
    valid filter for the remote source.
    """

    @abstractmethod
    def convert(
        self, object_type: str, object_filters: DataSourceFilter | None = None
    ) -> dict | str:
        """
        Emit a filter valid for the remote source from a `DataSourceFilter` instance
        """
        pass
