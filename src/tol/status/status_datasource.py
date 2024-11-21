# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cache
from typing import Iterable, Optional

from cachetools.func import ttl_cache

import requests

from ..core import (
    DataObject,
    DataSource,
    DataSourceFilter
)
from ..core.operator import (
    PageGetter
)

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


class StatusDataSource(
    DataSource,

    # the supported operators
    PageGetter,
):
    """
    A `DataSource` that gets status from a remote URL
    """
    @ttl_cache(ttl=60)
    def get_status(self, url) -> dict:
        try:
            r = requests.head(url, verify=False)
            return r.ok, r.status_code
        except Exception:
            return False, 500

    @property
    @cache
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'status': {
                'ok': 'bool',
                'status_code': 'int'
            }
        }

    @property
    @cache
    def supported_types(self) -> list[str]:
        return list(self.attribute_types.keys())

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None,
        session: Optional[OperableSession] = None
    ) -> tuple[Iterable[DataObject], int]:

        urls = object_filters.and_['id']['in_list']['value']

        ret = []
        for url in urls:
            ok, status_code = self.get_status(url)
            ret.append(self.data_object_factory(
                'status',
                url,
                attributes={
                    'ok': ok,
                    'status_code': status_code
                }
            ))

        return ret, len(ret)
