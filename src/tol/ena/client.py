# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Optional, Tuple

import requests

from .converter import EnaApiTransfer
from ..core import HttpClient


class EnaApiClient(HttpClient):
    """
    Takes ENA API transfers and connects to a remote ENA API.
    """

    def __init__(
        self,
        ena_url: str,
        ena_user: str,
        ena_password: str,
        ena_contact_name: str,
        ena_contact_email: str,
    ) -> None:
        super().__init__(
            retries=5
        )
        self.__ena_url = ena_url
        self.__ena_user = ena_user
        self.__ena_password = ena_password
        self.__ena_contact_name = ena_contact_name
        self.__ena_contact_email = ena_contact_email
        self.__type_mappings = {
            'number': 'float',
            'text': 'str',
            'array': 'List[str]',
            'date': 'datetime',
            'string': 'str',
        }

    def get_detail(
        self,
        object_type: str,
        object_ids: str,
        filter_string: Optional[str] = None
    ) -> Optional[EnaApiTransfer]:
        """
        Gets a list of ENA API transfers for the objects of a specified
        `object_type` and `object_id` or returns None if not found.
        """
        url, params = self.__detail_url(object_type, object_ids, filter_string)
        return self.__fetch_detail(url, params, text=(object_type == 'checklist'))

    def get_list(
        self,
        object_type: str,
        filter_string: Optional[str] = None
    ) -> Tuple[EnaApiTransfer, int]:
        url, params = self.__list_url(object_type, filter_string)
        return self.__fetch_list(url, params)

    def __fetch_detail(
        self,
        url: str,
        params: Dict = {},
        text: bool = False
    ) -> Optional[EnaApiTransfer]:
        """
        Fetches data from the ENA API.
        """
        session = self._get_session_with_retries()
        headers = {'Content-Type': 'application/json'}
        r = session.get(url, params=params, headers=headers)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        if text:
            return r.text
        try:
            data = r.json()
            if isinstance(data, list):
                return data
            return [] if not data else [data]
        except requests.exceptions.JSONDecodeError:
            return []

    def __fetch_list(
        self,
        url: str,
        params: Dict = {}
    ) -> Optional[EnaApiTransfer]:
        """
        Fetches data from the ENA API.
        """
        session = self._get_session_with_retries()
        headers = {'Content-Type': 'application/json'}
        r = session.get(url, params=params, headers=headers)

        if r.status_code == 404:
            return []
        r.raise_for_status()
        try:
            data = r.json()
            return data if data else []
        except requests.exceptions.JSONDecodeError:
            return []

    def __detail_url(
        self,
        object_type: str,
        object_ids: str,
        filter_string: Optional[str] = None
    ) -> str:
        """
        Returns the URL and parameters for a detail query.
        """
        if object_type == 'checklist':
            ids = ','.join(str(id_) for id_ in object_ids)
            url = f'{self.__ena_url}/ena/browser/api/xml/{ids}'
            params = {}
            return url, params
        if object_type == 'submittable_taxon':
            # This is actually called separately for each taxon id
            ids = ','.join(str(id_) for id_ in object_ids)
            url = f'{self.__ena_url}/ena/taxonomy/rest/tax-id/{ids}'
            params = {}
            return url, params

        url = f'{self.__ena_url}/ena/portal/api/search'

        if object_type == 'assembly':
            query_type = 'assembly_set_accession='
            ids = 'OR assembly_set_accession='.join(f' "{id_}" ' for id_ in object_ids)
        elif object_type == 'read_run':
            query_type = 'run_accession='
            ids = 'OR run_accession='.join(f' "{id_}" ' for id_ in object_ids)
        elif object_type == 'sample':
            query_type = 'sample_accession='
            ids = 'OR sample_accession='.join(f' "{id_}" ' for id_ in object_ids)
        elif object_type == 'study':
            query_type = 'study_accession='
            ids = 'OR study_accession='.join(f' "{id_}" ' for id_ in object_ids)
        elif object_type == 'taxon':
            query_type = 'tax_id='
            ids = 'OR tax_id='.join(f' "{id_}" ' for id_ in object_ids)

        query = query_type + ids

        params = {
            'result': object_type,
            'query': query,
            'format': 'json',
            'fields': 'all'
        }

        return url, params

    def __list_url(
        self,
        object_type: str,
        filter_string: Optional[str] = None
    ) -> str:
        """
        Returns the URL and parameters for a detail query.
        """
        url = f'{self.__ena_url}/ena/portal/api/search'
        params = {
            'result': object_type,
            'query': filter_string,
            'format': 'json',
            'fields': 'all'
        }

        return url, params

    def get_fields(
        self,
        object_type
    ) -> dict:
        """
        Returns the fields for a given object type from the ENA portal API.
        """
        if object_type == 'checklist':
            return {'checklist': 'dict[str, Any]'}
        if object_type == 'submittable_taxon':
            return {
                'scientific_name': 'str',
                'formal_name': 'str',
                'rank': 'str',
                'division': 'str',
                'lineage': 'str',
                'genetic_code': 'str',
                'mitochondrial_genetic_code': 'str',
                'submittable': 'boolean',
                'binomial': 'boolean',
                'merged': 'str',
                'authority': 'str',
                'other_names': 'list[str]',
                'metagenome': 'str'
            }
        session = self._get_session_with_retries()
        r = session.get(
            self.__ena_url + '/ena/portal/api/returnFields',
            params={'result': object_type, 'format': 'json'},
            headers={
                'Content-Type': 'application/json'
            }
        )
        fields = {}
        for field in r.json():

            type_ = field['type'] if 'type' in field else 'string'
            ena_type = self.__type_mappings[type_] if type_ in self.__type_mappings else 'str'
            fields[field['columnId']] = ena_type

        return fields
