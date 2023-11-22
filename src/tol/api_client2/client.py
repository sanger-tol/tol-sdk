# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

import requests

from .converter import JsonApiTransfer
from ..api_base2.misc.operator_config import OperatorDict


class JsonApiClient:
    """
    Takes JSON:API transfers and connects to a remote
    API.
    """

    def __init__(
        self,
        api_url: str,
        token: Optional[str] = None,

        data_prefix: str = '/data',
        config_prefix: str = '/_config',
        token_header: str = 'token'
    ) -> None:

        self.__token = self.__token_header(token_header, token)
        self.__data_url = f'{api_url}{data_prefix}'
        self.__config_url = f'{self.__data_url}{config_prefix}'

    def get_detail(
        self,
        object_type: str,
        object_id: str
    ) -> JsonApiTransfer:
        """
        Gets a single JSON:API transfer for the object of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url = self.__detail_url(object_type, object_id)
        headers = self.__merge_headers()
        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def get_list_page(
        self,
        object_type: str,
        page: int,
        page_size: int,
        filter_string: Optional[str] = None,
        sort_string: Optional[str] = None
    ) -> JsonApiTransfer:
        """
        Gets a (paged) list-JSON:API transfer for the objects of specified
        `object_type`.
        """

        url = self.__list_url(object_type)
        params = self.__no_none_value_dict(
            page=page,
            page_size=page_size,
            filter=filter_string,
            sort_by=sort_string
        )
        headers = self.__merge_headers()
        r = requests.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

    def delete(self, object_type: str, object_id: str) -> None:
        """
        Deletes the remote-API `DataObject` of specified type and ID.
        """
        url = self.__detail_url(object_type, object_id)
        headers = self.__merge_headers()
        r = requests.delete(url, headers=headers)
        r.raise_for_status()

    def upsert(
        self,
        object_type: str,
        transfer: JsonApiTransfer
    ) -> None:
        """
        Takes a `JsonApiTransfer` containing a `list` of
        serialized `DataObject` instances to be upserted.
        """

        url = self.__upsert_url(object_type)
        headers = self.__merge_headers()
        r = requests.post(url, headers=headers, json=transfer)
        r.raise_for_status()

    def config_operations(self) -> dict[str, OperatorDict]:
        """
        Fetches the supported `Operator` config for each
        `object_type` published by `api_base2`.
        """

        url = self.__config_operations_url()
        return self.__fetch_config(url)

    def config_attribute_types(self) -> dict[str, dict[str, str]]:
        """
        Fetches the `attribute_types` config for each
        `object_type` published by `api_base2`.
        """

        url = self.__config_attr_types_url()
        return self.__fetch_config(url)

    def __fetch_config(self, url: str) -> Any:
        headers = self.__merge_headers()
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

    def __detail_url(self, object_type: str, object_id: str) -> str:
        return f'{self.__data_url}/{object_type}/{object_id}'

    def __list_url(self, object_type: str) -> str:
        return f'{self.__data_url}/{object_type}'

    def __upsert_url(self, object_type: str) -> str:
        return f'{self.__list_url(object_type)}:upsert'

    def __config_operations_url(self) -> str:
        return f'{self.__config_url}/operations'

    def __config_attr_types_url(self) -> str:
        return f'{self.__config_url}/attribute_types'

    def __no_none_value_dict(self, **kwargs) -> dict[str, Any]:
        return {
            k: v for k, v in kwargs.items()
            if v is not None
        }

    def __token_header(
        self,
        key: str,
        token: Optional[str],
    ) -> Optional[dict[str, str]]:

        return None if token is None else {key: token}

    def __merge_headers(
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
