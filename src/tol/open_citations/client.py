# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, Optional
from urllib.parse import quote

from .converter import OpenCitationsApiTransfer
from ..core import HttpClient


class OpenCitationsApiClient(HttpClient):
    """
    Takes OpenCitations API transfers and connects to a remote
    OpenCitations API.
    """

    def __init__(
        self,
        open_citations_url: str,
        access_token: Optional[str] = None,
        retries: int = 5,
    ) -> None:
        super().__init__(
            token=access_token,
            token_header='authorization',
            retries=retries,
        )
        self.__open_citations_url = open_citations_url

    def get_detail(
        self,
        object_type: str,
        object_ids: Iterable[str],
    ) -> Optional[OpenCitationsApiTransfer]:
        """
        Gets a list of OpenCitations API transfers for the objects of specified
        `object_type` and `object_ids`, or returns None if not found.
        """
        if object_type != 'meta':
            raise ValueError(f'Unsupported object type: {object_type}')

        url, params = self.__detail_url(object_ids)
        headers = self._merge_headers()
        return self.__fetch_detail(url, params=params, headers=headers)

    def __detail_url(
        self,
        object_ids: Iterable[str],
    ) -> tuple[str, dict]:
        ids = '__'.join(self.__normalise_id(object_id) for object_id in object_ids)
        url = f'{self.__open_citations_url}/metadata/{quote(ids, safe=":_/()-.")}'
        return url, {}

    def __normalise_id(
        self,
        object_id: str,
    ) -> str:
        object_id = object_id.strip()
        if ':' in object_id:
            return object_id
        return f'doi:{object_id}'

    def __fetch_detail(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Optional[OpenCitationsApiTransfer]:
        """
        Fetches data from the OpenCitations API.
        """
        session = self._get_session_with_retries()
        response = session.get(
            url,
            params=params,
            headers=headers,
        )

        if response.status_code in [400, 404]:
            return []

        response.raise_for_status()

        try:
            data = response.json()
            return data if data else []
        except ValueError:
            return []
