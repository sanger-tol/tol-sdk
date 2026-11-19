# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional, Tuple

import requests

from .converter import GoatApiTransfer


class GoatApiClient:
    """
    Takes GoaT API transfers and connects to a remote
    GoaT API (v3).
    """

    __names = ['common_name', 'tolid_prefix', 'synonym']
    __fields = [
        'genome_size', 'chromosome_number', 'assembly_level', 'haploid_number',
        'ploidy', 'echabs92', 'habreg_2017', 'marhabreg-2017', 'waca_1981',
        'isb_wildlife_act_1976', 'protection_of_badgers_act_1992',
        'family_representative', 'long_list', 'sample_collected',
        'country_list', 'assembly_span', 'cites_category', 'conservation_list',
        'redlist_category', 'redlist_population_trend', 'redlist_scopes'
    ]
    __ranks = [
        'subspecies', 'species', 'genus', 'family', 'superfamily', 'order',
        'class', 'phylum', 'kingdom', 'superkingdom', 'domain'
    ]

    def __init__(
        self,
        goat_url: str,
    ) -> None:
        self.__goat_url = goat_url

    def get_detail(
        self,
        object_type: str,
        object_ids: list[str]
    ) -> Tuple[GoatApiTransfer, int]:
        """
        Gets a list of GoaT API transfers for the objects of specified
        `object_type` and `object_ids`.
        """

        body = self.__build_body(
            object_type,
            query_filters={'taxa': [str(i) for i in object_ids]},
            page_size=len(object_ids)
        )
        results, total, _ = self.__post_search(body)
        return results, total

    def get_list_page(
        self,
        object_type: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        query_filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        search_after: Optional[list] = None
    ) -> Tuple[GoatApiTransfer, int, Optional[list]]:
        """
        Gets one page of results. If `search_after` (the cursor returned
        by a previous call) is given, it takes precedence over `page`.

        Returns a tuple of:

        - the list of results
        - the total number of hits
        - the `search_after` cursor for the next page (or `None`)
        """

        body = self.__build_body(
            object_type,
            query_filters=query_filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            search_after=search_after
        )
        return self.__post_search(body)

    def __post_search(
        self,
        body: Dict[str, Any]
    ) -> Tuple[GoatApiTransfer, int, Optional[list]]:
        r = requests.post(f'{self.__goat_url}/search', json=body)
        if r.status_code == 404:
            return [], 0, None
        r.raise_for_status()
        payload = r.json()
        status = payload.get('status', {})
        if not status.get('success', True):
            raise requests.HTTPError(
                f'GoaT API error: {status.get("error", "unknown error")}',
                response=r
            )
        return (
            payload.get('results', []),
            status.get('hits', 0),
            payload.get('search_after')
        )

    def __build_body(
        self,
        object_type: str,
        query_filters: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        search_after: Optional[list] = None
    ) -> Dict[str, Any]:
        query = {
            'index': object_type,
            'names': self.__names,
            'fields': self.__fields,
            'ranks': self.__ranks
        }
        if query_filters:
            query.update(query_filters)
        if 'taxa' in query:
            query.setdefault('taxon_filter_type', 'name')
        elif 'rank' in query:
            # A rank restriction only applies within a taxon scope,
            # so search the whole tree from Eukaryota
            query['taxa'] = ['2759']
            query['taxon_filter_type'] = 'tree'
        params = {
            'taxonomy': 'ncbi',
            'include_estimates': True,
            'include_taxon_names': True,
            'include_lineage': True,
            'sort': self.__get_sort(sort_by)
        }
        if page_size is not None:
            params['size'] = page_size
        if search_after is not None:
            params['search_after'] = search_after
        elif page is not None:
            params['page'] = page
        return {'params': params, 'query': query}

    def __get_sort(self, sort_by: Optional[str]) -> List[Dict[str, str]]:
        sort = []
        if sort_by is not None:
            order = 'asc'
            if sort_by.startswith('-'):
                order = 'desc'
                sort_by = sort_by[1:]
            if sort_by == 'id':
                sort_by = 'taxon_id'
            sort.append({'by': sort_by, 'order': order})
        if not any(s['by'] == 'taxon_id' for s in sort):
            # A deterministic tiebreaker, so that search_after
            # cursors are returned and are unambiguous
            sort.append({'by': 'taxon_id', 'order': 'asc'})
        return sort
