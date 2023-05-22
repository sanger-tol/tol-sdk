# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import List

from ..core import DataSource


class BenchlingDataSource(DataSource):
    """
    A (read-only) DataSource for getting objects in Benchling
    """

    @property
    def supported_types(self) -> List[str]:
        return [
            'sequencing_requests',
        ]
