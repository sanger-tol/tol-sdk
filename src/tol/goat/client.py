# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Optional

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

    def __fetch_detail(
        self,
        url: str,
        params: Dict = {}
    ) -> Optional[GoatApiTransfer]:

        r = requests.get(url, params=params)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()['results'] if 'results' in r.json() else []

    def __detail_url(self, object_type: str, object_ids: str) -> str:
        url = f'{self.__goat_url}/search'
        obj_ids_str = ','.join(object_ids)
        params = {
            'query': f'tax_name({obj_ids_str})',
            'result': 'taxon',
            'size': len(object_ids),
            'includeEstimates': 'false',
            'summaryValues': 'count',
            'taxonomy': 'ncbi',
            'fields': 'genome_size,chromosome_number,haploid_number,ploidy,echabs92,'
                      'habreg_2017,marhabreg-2017,waca_1981,isb_wildlife_act_1976,'
                      'protection_of_badgers_act_1992,family_representative',
            'ranks': 'subspecies,species,genus,family,order,class,phylum,kingdom,superkingdom'
        }
        return url, params
