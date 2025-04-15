# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Optional

from .converter import BoldApiTransfer
from ..core import HttpClient


class BoldApiClient(HttpClient):
    """
    Takes BOLD API transfers and connects to a remote
    BOLD API.
    """

    def __init__(
        self,
        bold_url: str,
        bold_api_key: str,
        retries: int = 5
    ) -> None:
        super().__init__(token=bold_api_key, token_header='api-key', retries=retries)
        self.__bold_url = bold_url

    def get_detail(
        self,
        object_type: str,
        object_ids: str
    ) -> Optional[BoldApiTransfer]:
        """
        Gets a list of BOLD API transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url, params = self.__detail_url(object_type, object_ids)
        headers = self._merge_headers()
        return self.__fetch_detail(url, params=params, headers=headers)

    def __fetch_detail(
        self,
        url: str,
        params: Dict = {},
        headers: Dict = {},
    ) -> Optional[BoldApiTransfer]:

        session = self._get_session_with_retries()
        r = session.get(url, params=params, headers=headers)
        if r.status_code in [400, 404]:
            return []
        r.raise_for_status()
        results = []
        lines = r.text.splitlines()
        for line in lines:
            result = json.loads(line)
            results.append(result)
        return results

    def __detail_url(self, object_type: str, object_ids: str) -> str:
        url = f'{self.__bold_url}/records'
        obj_ids_str = ','.join(object_ids)
        params = {
            'sampleids': obj_ids_str
        }
        return url, params
