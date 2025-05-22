# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Optional, Tuple
from urllib.parse import quote

import requests

from .converter import GoatApiTransfer


class GoatApiClient:
    """
    Takes GoaT API transfers and connects to a remote
    GoaT API.
    """

    def __init__(
        self,
        goat_url: str,
    ) -> None:
        self.__goat_url = goat_url

    def get_detail(
        self,
        object_type: str,
        object_ids: str
    ) -> Optional[GoatApiTransfer]:
        """
        Gets a list of GoaT API transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """

        url, params = self.__detail_url(object_type, object_ids)
        return self.__fetch_detail(url, params)

    def get_list_page(
        self,
        object_type: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        filter_string: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[GoatApiTransfer, int]:
        url, params = self.__page_url(object_type, page, page_size, filter_string, sort_by)
        return self.__fetch_detail(url, params)

    def __fetch_detail(
        self,
        url: str,
        params: Dict = {}
    ) -> Optional[GoatApiTransfer]:
        r = requests.get(url, params=params)
        if r.status_code == 404:
            return [], 0
        r.raise_for_status()
        return r.json()['results'] if 'results' in r.json() else [], r.json()['status']['hits']

    def __detail_url(self, object_type: str, object_ids: str) -> Tuple[str, Dict]:
        obj_ids_str = ','.join(object_ids)
        return self.__page_url(object_type, 1, len(object_ids), f'tax_name({obj_ids_str})')

    def __page_url(
        self,
        object_type: str,
        page: int,
        page_size: int,
        filter_string: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Tuple[str, Dict]:
        url = f'{self.__goat_url}/search?query={quote(filter_string)}'
        params = {
            # 'query': filter_string,  # We encode the query string manually to ensure space->%20
            'result': object_type,
            'includeEstimates': 'true',
            'summaryValues': 'count',
            'taxonomy': 'ncbi',
            'names': 'common_name,tolid_prefix,synonym',
            'fields': 'genome_size,chromosome_number,assembly_level,haploid_number,ploidy,'
                      'echabs92,habreg_2017,marhabreg-2017,waca_1981,isb_wildlife_act_1976,'
                      'protection_of_badgers_act_1992,family_representative,long_list,'
                      'sample_collected',
            'ranks': 'subspecies,species,genus,family,order,class,phylum,kingdom,superkingdom'
        } | self.__get_sort_params(sort_by) | self.__get_page_params(page, page_size)
        return url, params

    def __get_page_params(self, page: int, page_size: int) -> Dict:
        ret = {}
        if page is not None:
            ret['offset'] = (page - 1) * page_size
        if page_size is not None:
            ret['size'] = page_size
        return ret

    def __get_sort_params(self, sort_by: str) -> Dict:
        if sort_by is None:
            return {}
        elif sort_by.startswith('-'):
            return {
                'sortBy': sort_by[1:] if sort_by[1:] != 'id' else 'taxon_id',
                'sortOrder': 'desc'
            }
        else:
            return {
                'sortBy': sort_by if sort_by != 'id' else 'taxon_id',
                'sortOrder': 'asc'
            }
