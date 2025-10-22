# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Iterable, Optional
from urllib.parse import quote

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
        bold_portal_url: str,
        bold_api_key: str,
        retries: int = 5
    ) -> None:
        super().__init__(token=bold_api_key, token_header='api-key', retries=retries)
        self.__bold_url = bold_url
        self.__bold_portal_url = bold_portal_url

    def get_detail(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[BoldApiTransfer]:
        """
        Gets a list of BOLD API transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """
        if object_type == 'bin':
            return (
                self.__get_detail_portal(object_type, object_id)
                for object_id in object_ids
            )
        else:
            return self.__get_detail_data(object_type, object_ids)

    def __get_detail_data(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[BoldApiTransfer]:
        """
        Gets a list of BOLD API transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url, params = self.__detail_url(object_type, object_ids)
        headers = self._merge_headers()
        return self.__fetch_detail(url, params=params, headers=headers)

    def __get_detail_portal(
        self,
        object_type: str,
        object_id: str
    ) -> Optional[BoldApiTransfer]:
        """
        Gets a list of BOLD API transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url, params = self.__query_url(object_type, object_id)
        headers = self._merge_headers()
        query_id = self.__fetch_query(url, params=params, headers=headers)
        if not query_id:
            return None
        return self.__fetch_bin(self.__bin_url(query_id), object_id, headers=headers)

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

    def __query_url(self, object_type: str, object_id: str) -> str:
        url = f'{self.__bold_portal_url}/query'
        params = {
            'query': f'{object_type}:uri:{object_id}'
        }
        return url, params

    def __fetch_query(
        self,
        url: str,
        params: Dict = {},
        headers: Dict = {},
    ) -> Optional[BoldApiTransfer]:

        session = self._get_session_with_retries()
        r = session.get(url, params=params, headers=headers)
        if r.status_code in [400, 404]:
            return None
        r.raise_for_status()
        results = r.json()
        return results['query_id'] if 'query_id' in results else None

    def __bin_url(self, query_id: str) -> str:
        url = f'{self.__bold_portal_url}/taxonomy/{quote(query_id)}'
        return url

    def __fetch_bin(
        self,
        url: str,
        object_id: str,
        params: Dict = {},
        headers: Dict = {},
    ) -> Optional[BoldApiTransfer]:

        session = self._get_session_with_retries()
        r = session.get(url, params=params, headers=headers)
        if r.status_code in [400, 404]:
            return None
        r.raise_for_status()
        results = r.json()
        # Unmatched queries just return empty dicts
        return results | {'binid': object_id} \
            if 'taxonomy' in results \
            and 'kingdom' in results['taxonomy'] \
            and results['taxonomy']['kingdom'] != {} \
            else None
