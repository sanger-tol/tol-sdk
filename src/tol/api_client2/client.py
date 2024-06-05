# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional

import requests

from .converter import JsonApiTransfer, JsonRelationshipConfig
from ..core.datasource_error import DataSourceError
from ..core.operator import OperatorDict


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
    ) -> Optional[JsonApiTransfer]:
        """
        Gets a single JSON:API transfer for the object of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url = self.__detail_url(object_type, object_id)
        headers = self.__merge_headers()
        return self.__fetch_detail(url, headers=headers)

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
        return self.__fetch_list(url, params=params, headers=headers)

    def get_count(
        self,
        object_type: str,
        filter_string: Optional[str] = None
    ) -> JsonApiTransfer:
        """
        Gets count transfer for the objects of specified
        `object_type`.
        """

        url = self.__count_url(object_type)
        params = self.__no_none_value_dict(
            filter=filter_string
        )
        headers = self.__merge_headers()
        return self.__fetch_list(url, params=params, headers=headers)

    def get_stats(
        self,
        object_type: str,
        stats_string: Optional[str],
        stats_fields_string: Optional[str],
        filter_string: Optional[str] = None
    ) -> JsonApiTransfer:
        """
        Gets stats transfer for the objects of specified
        `object_type`.
        """

        url = self.__stats_url(object_type)
        params = self.__no_none_value_dict(
            stats=stats_string,
            stats_fields=stats_fields_string,
            filter=filter_string
        )
        headers = self.__merge_headers()
        return self.__fetch_list(url, params=params, headers=headers)

    def delete(self, object_type: str, object_id: str) -> None:
        """
        Deletes the remote-API `DataObject` of specified type and ID.
        """
        url = self.__detail_url(object_type, object_id)
        headers = self.__merge_headers()
        r = requests.delete(url, headers=headers)
        self.__assert_no_error(r)

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
        self.__assert_no_error(r)

    def insert(
        self,
        object_type: str,
        transfer: JsonApiTransfer
    ) -> None:
        """
        Takes a `JsonApiTransfer` containing a `list` of
        serialized `DataObject` instances to be inserted.
        """

        url = self.__insert_url(object_type)
        headers = self.__merge_headers()
        r = requests.post(url, headers=headers, json=transfer)
        self.__assert_no_error(r)

    def get_to_one_relation_recursive(
        self,
        object_type: str,
        object_id: str,
        relationship_hops: list[str]
    ) -> Optional[JsonApiTransfer]:
        """
        Fetches the nested to-one relation, on the source
        specified by the `object_type` and `object_id`,
        defined by the given `relationship_hops`.
        """

        url = self.__to_one_relation_url(
            object_type,
            object_id,
            relationship_hops
        )
        headers = self.__merge_headers()
        return self.__fetch_detail(url, headers=headers)

    def get_to_many_relations_page(
        self,
        object_type: str,
        object_id: str,
        relationship_name: str,
        page: int,
        page_size: int
    ) -> JsonApiTransfer:
        """
        Fetches a page of to-many results for the given
        `relationship_name`, on the object specified by
        `object_type` and `object_id`.
        """

        url = self.__to_many_relation_url(
            object_type,
            object_id,
            relationship_name
        )
        params = {'page': page, 'page_size': page_size}
        headers = self.__merge_headers()

        return self.__fetch_list(url, params=params, headers=headers)

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

    def config_attribute_metadata(self) -> dict[str, dict[str, dict[str, str | bool]]]:
        """
        Fetches the `attribute_metadata` config for each
        `object_type` published by `api_base2`.
        """

        url = self.__config_attribute_metadata_url()
        return self.__fetch_config(url)

    def config_relationships(self) -> JsonRelationshipConfig:
        """
        Fetches the `relationship_config` transfer for each
        `object_type` published by `api_base2`.
        """

        url = self.__config_rel_url()
        return self.__fetch_config(url)

    def __fetch_config(self, url: str) -> Any:
        headers = self.__merge_headers()
        r = requests.get(url, headers=headers)
        self.__assert_no_error(r)
        return r.json()

    def __fetch_detail(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None
    ) -> Optional[JsonApiTransfer]:

        r = requests.get(url, params=params, headers=headers)
        if r.status_code == 404:
            return None
        self.__assert_no_error(r)
        return r.json()

    def __assert_no_error(
        self,
        r: requests.Response
    ) -> None:

        if r.headers.get('content-type') == 'application/json':
            return_body = r.json()

            if 'errors' in return_body:
                e: dict[str, str] = return_body['errors'][0]

                raise DataSourceError(
                    title=e.get('title'),
                    detail=e.get('detail'),
                    status_code=r.status_code
                )

        r.raise_for_status()

    def __fetch_list(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None
    ) -> JsonApiTransfer:

        r = requests.get(url, params=params, headers=headers)
        self.__assert_no_error(r)
        return r.json()

    def __detail_url(self, object_type: str, object_id: str) -> str:
        return f'{self.__data_url}/{object_type}/{object_id}'

    def __list_url(self, object_type: str) -> str:
        return f'{self.__data_url}/{object_type}'

    def __count_url(self, object_type: str) -> str:
        return f'{self.__list_url(object_type)}:count'

    def __stats_url(self, object_type: str) -> str:
        return f'{self.__list_url(object_type)}:stats'

    def __upsert_url(self, object_type: str) -> str:
        return f'{self.__list_url(object_type)}:upsert'

    def __insert_url(self, object_type: str) -> str:
        return f'{self.__list_url(object_type)}:insert'

    def __to_one_relation_url(
        self,
        object_type: str,
        object_id: str,
        relationship_hops: list[str]
    ) -> str:

        hop_string = '/'.join(relationship_hops)
        base_url = (
            f'{self.__data_url}/{object_type}:to-one/{object_id}'
        )
        return f'{base_url}/{hop_string}'

    def __to_many_relation_url(
        self,
        object_type: str,
        object_id: str,
        relationship_name: str
    ) -> str:

        base_url = (
            f'{self.__data_url}/{object_type}:to-many/{object_id}'
        )
        return f'{base_url}/{relationship_name}'

    def __config_operations_url(self) -> str:
        return f'{self.__config_url}/operations'

    def __config_attr_types_url(self) -> str:
        return f'{self.__config_url}/attribute_types'

    def __config_attribute_metadata_url(self) -> str:
        return f'{self.__config_url}/attribute_metadata'

    def __config_rel_url(self) -> str:
        return f'{self.__config_url}/relationships'

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
