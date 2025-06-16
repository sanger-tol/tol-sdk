# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from typing import Optional

import requests
from requests.adapters import HTTPAdapter, Retry


class HttpClient:
    """
    Core functionality for HTTP clients
    """

    def __init__(
        self,
        token: Optional[str] = None,
        token_header: str = 'token',
        retries: int = 5
    ) -> None:
        self.__token = self._token_header(token_header, token)
        self.__retries = retries

    def _token_header(
        self,
        key: str,
        token: Optional[str],
    ) -> Optional[dict[str, str]]:

        return None if token is None else {key: token}

    def _merge_headers(
        self,
        headers: Optional[dict[str, str]] = None
    ) -> dict[str, str]:
        """
        Merges (possibly `None`) headers with the
        `Optional[str]` token. Returns `None` if both are
        undefined
        """

        def __empty_if_none(
            d: Optional[dict[str, str]]
        ) -> dict[str, str]:
            return {} if d is None else d

        if self.__token is None and headers is None:
            return None
        return {
            **__empty_if_none(headers),
            **__empty_if_none(self.__token)
        }

    def _get_session(self) -> requests.Session:

        cert_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'certs',
            'cacert.pem'
        )

        session = requests.Session()
        session.verify = cert_path

        return session

    def _get_session_with_retries(self) -> requests.Session:
        """
        Attempts a call to the endpoint 5 times, with a delay of 1 second
        """
        session = self._get_session()

        retry_strategy = Retry(
            total=self.__retries,
            backoff_factor=1,
            status_forcelist=[429, 502, 503, 504]
        )
        session.mount('http://', HTTPAdapter(max_retries=retry_strategy))
        session.mount('https://', HTTPAdapter(max_retries=retry_strategy))

        return session
