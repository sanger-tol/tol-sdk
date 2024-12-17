# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

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
                            'family_representative': {'value': 'DTOL'}
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
                            'family_representative': {'value': ['PROJ_A', 'PROJ_B']}
                        }
                    }
                }
            ],
            'status': {
                'hits': 2
            }
        }
        expected = [
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
                        'family_representative': {'value': 'DTOL'}
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
                        'family_representative': {'value': ['PROJ_A', 'PROJ_B']}
                    }
                }
            }
        ]

        responses.get(
            f'{FAKE_API_URL}/search',
            json=resp
        )

        observed = client.get_detail('taxon', ['6992', '6993'])
        assert observed == (expected, 2)
