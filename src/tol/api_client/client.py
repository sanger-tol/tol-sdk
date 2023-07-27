# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

from .converter import ObjectDump
from ..api_base2.misc import AllOperationsDict


class ApiClient(ABC):
    """Makes requests to a remote API"""

    @abstractmethod
    def get_detail(
        self,
        type_: str,
        id_: str
    ) -> Optional[ObjectDump]:
        """
        Gets the dict-dump of a `DataObject` with the
        specified type and ID.
        """

    @abstractmethod
    def get_page(
        self,
        type_: str,
        page_number: int,
        page_size: Optional[int],
        filters: Optional[dict[str, Any]],
        sort_by: Optional[str]
    ) -> list[ObjectDump]:
        """
        Gets the page of results, sorted as specified,
        matching the given filters.
        """

    @abstractmethod
    def get_operations_config(self) -> AllOperationsDict:
        """
        Gets the supported operations for each type of
        `DataObject` supported by the API.
        """


class DefaultApiClient(ApiClient):

    def __init__(
        self,
        url: str,
        token: str,
        data_prefix: str = '/data',
        config_prefix: str = '/_config',
        header_name: str = 'Token'
    ) -> None:

        self.__data_url = f'{url}{data_prefix}'
        self.__config_url = f'{self.__data_url}{config_prefix}'
        self.__headers = {
            header_name: token
        }

    def get_detail(
        self,
        type_: str,
        id_: str
    ) -> Optional[ObjectDump]:

        url = f'{self.__data_url}/{type_}/{id_}'
        r = requests.get(
            url,
            headers=self.__headers
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()['data']

    def get_page(
        self,
        type_: str,
        page_number: int,
        page_size: int,
        filters: Optional[dict[str, Any]] = None,
        sort_by: Optional[str] = None
    ) -> list[ObjectDump]:

        url = f'{self.__data_url}/{type_}'
        r = requests.get(
            url,
            headers=self.__headers,
            params=self.__get_list_params(
                page_number,
                page_size,
                filters,
                sort_by
            )
        )
        r.raise_for_status()
        return r.json()['data']

    def get_operations_config(self) -> AllOperationsDict:
        url = f'{self.__config_url}/operations'
        r = requests.get(
            url,
            headers=self.__headers
        )
        r.raise_for_status()
        return r.json()

    def __get_list_params(
        self,
        page_number: int,
        page_size: int,
        filters: Optional[dict[str, Any]],
        sort_by: Optional[str]
    ) -> dict[str, Any]:

        params = {
            'page': page_number,
            'page_size': page_size,
        }
        if filter is not None:
            params['filter'] = json.dumps(filters)
        if sort_by is not None:
            params['sort_by'] = sort_by

        return params
