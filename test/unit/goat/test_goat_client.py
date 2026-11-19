# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import responses

from tol.goat.client import GoatApiClient


FAKE_API_URL = 'http://test.lan/api'


class TestGoatApiClient:
    """The `GoatApiClient` and its methods"""

    @responses.activate
    def test_get_detail(self):
        """Default values, no token"""

        client = GoatApiClient(FAKE_API_URL)
        resp = {
            'results': [
                {
                    'result': {
                        'taxon_id': '9662',
                        'scientific_name': 'Meles meles',
                        'fields': {
                            'genome_size': {'value': 1000},
                            'chromosome_number': {'value': 44},
                            'haploid_number': {'value': 22},
                            'assembly_level': {'value': 'Chromosome'},
                            'ploidy': {'value': 2},
                            'isb_wildlife_act_1976': {'value': 'IWA-Sch5'},
                            'protection_of_badgers_act_1992': {'value': 'Badgers92'},
                            'family_representative': {'value': 'DTOL'},
                            'sample_collected': {'value': 'DTOL'},
                            'country_list': {'value': ['AT', 'BE']}
                        }
                    }
                },
                {
                    'result': {
                        'taxon_id': '9663',
                        'scientific_name': 'Molos molos',
                        'fields': {
                            'genome_size': {'value': 2000},
                            'chromosome_number': {'value': 88},
                            'haploid_number': {'value': 44},
                            'assembly_level': {'value': 'Contig'},
                            'ploidy': {'value': 4},
                            'echabs92': {'value': 'Ech'},
                            'habreg_2017': {'value': 'Hab'},
                            'marhabreg-2017': {'value': 'Mar'},
                            'waca_1981': {'value': 'Shakira'},
                            'family_representative': {'value': ['PROJ_A', 'PROJ_B']},
                            'sample_collected': {'value': 'ZOONOMIA'},
                            'country_list': {'value': ['BG', 'CA']}
                        }
                    }
                }
            ],
            'status': {
                'success': True,
                'hits': 2
            }
        }

        responses.post(
            f'{FAKE_API_URL}/search',
            json=resp
        )

        observed = client.get_detail('taxon', ['9662', '9663'])
        assert observed == (resp['results'], 2)

        body = json.loads(responses.calls[0].request.body)
        assert body['query']['taxa'] == ['9662', '9663']
        assert body['query']['taxon_filter_type'] == 'name'
        assert body['query']['index'] == 'taxon'
        assert body['params']['size'] == 2
        assert body['params']['taxonomy'] == 'ncbi'
        assert body['params']['include_estimates'] is True
        assert body['params']['include_taxon_names'] is True
        assert body['params']['include_lineage'] is True

    @responses.activate
    def test_get_list_page(self):
        """A page with query filters, sorting and a search_after cursor"""

        client = GoatApiClient(FAKE_API_URL)
        resp = {
            'results': [
                {'result': {'taxon_id': '9662'}},
                {'result': {'taxon_id': '9663'}}
            ],
            'status': {
                'success': True,
                'hits': 10
            },
            'search_after': ['molos molos', '9663']
        }

        responses.post(
            f'{FAKE_API_URL}/search',
            json=resp
        )

        observed = client.get_list_page(
            'taxon',
            page=1,
            page_size=2,
            query_filters={
                'attributes': [
                    {'name': 'long_list', 'operator': 'eq', 'value': 'DTOL'}
                ]
            },
            sort_by='-scientific_name'
        )
        assert observed == (
            resp['results'], 10, ['molos molos', '9663']
        )

        body = json.loads(responses.calls[0].request.body)
        assert body['query']['attributes'] == [
            {'name': 'long_list', 'operator': 'eq', 'value': 'DTOL'}
        ]
        assert body['params']['page'] == 1
        assert body['params']['size'] == 2
        assert body['params']['sort'] == [
            {'by': 'scientific_name', 'order': 'desc'},
            {'by': 'taxon_id', 'order': 'asc'}
        ]
        assert 'search_after' not in body['params']

    @responses.activate
    def test_get_list_page_search_after(self):
        """search_after takes precedence over page"""

        client = GoatApiClient(FAKE_API_URL)
        resp = {
            'results': [
                {'result': {'taxon_id': '9664'}}
            ],
            'status': {
                'success': True,
                'hits': 10
            }
        }

        responses.post(
            f'{FAKE_API_URL}/search',
            json=resp
        )

        observed = client.get_list_page(
            'taxon',
            page=2,
            page_size=2,
            sort_by='id',
            search_after=['9663']
        )
        assert observed == (resp['results'], 10, None)

        body = json.loads(responses.calls[0].request.body)
        assert body['params']['search_after'] == ['9663']
        assert 'page' not in body['params']
        assert body['params']['sort'] == [
            {'by': 'taxon_id', 'order': 'asc'}
        ]

    @responses.activate
    def test_rank_without_taxa(self):
        """A rank filter alone is scoped to the whole tree"""

        client = GoatApiClient(FAKE_API_URL)
        resp = {
            'results': [],
            'status': {
                'success': True,
                'hits': 0
            }
        }

        responses.post(
            f'{FAKE_API_URL}/search',
            json=resp
        )

        observed = client.get_list_page(
            'taxon',
            page=1,
            page_size=10,
            query_filters={'rank': 'species'}
        )
        assert observed == ([], 0, None)

        body = json.loads(responses.calls[0].request.body)
        assert body['query']['rank'] == 'species'
        assert body['query']['taxa'] == ['2759']
        assert body['query']['taxon_filter_type'] == 'tree'
