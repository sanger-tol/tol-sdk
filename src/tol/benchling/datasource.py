# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List, Optional

from ..core import DataObject, DataSource, unsupported


class BenchlingDataSource(DataSource):
    """
    A (read-only) DataSource for getting objects in Benchling
    """

    @property
    def supported_types(self) -> List[str]:
        return [
            'sequencing_requests',
        ]

    def get_attribute_types(self, object_type: str) -> Dict:
        return {}

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs
    ) -> Iterable[Optional[DataObject]]:
        return []

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass
