# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.core import DataObject
from tol.goat import create_goat_datasource


FAKE_API_URL = 'http://fake.lan/api'


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one

    return data_object


class TestCreateGoatDatasource:
    """larger-than unit tests on `create_goat_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_api_datasource().get_by_id()` + no token"""

        goat_ds = create_goat_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='taxon',
            id_='9662'
        )
        mock_do_factory.return_value = mock_data_object
        goat_ds.data_object_factory = mock_do_factory

        in_ = {
            'results': [{
                'result': {
                    'taxon_id': '9662',
                    'taxon_rank': 'species',
                    'scientific_name': 'Meles meles',
                    'fields': {
                        'genome_size': {'value': 1000},
                        'chromosome_number': {'value': 44},
                        'haploid_number': {'value': 22},
                        'assembly_level': {'value': 'Chromosome'},
                        'ploidy': {'value': 2},
                        'isb_wildlife_act_1976': {'value': 'IWA-Sch5'},
                        'protection_of_badgers_act_1992': {'value': 'Badgers92'}
                    },
                    'names': {
                        'tolid_prefix': {
                            'class': [
                                'tolid_prefix'
                            ],
                            'name': [
                                'mMelMel'
                            ],
                            'source': [
                                'dtol sample naming'
                            ]
                        },
                        'common_name': {
                            'class': [
                                'common_name'
                            ],
                            'name': [
                                'Melon'
                            ],
                            'source': [
                                'animal genome size database'
                            ]
                        },
                        'synonym': {
                            'class': [
                                'synonym'
                            ],
                            'name': [
                                'Meles alba',
                                'Meles britannicus'
                            ],
                            'source': [
                                'some source'
                            ]
                        }
                    },
                }
            }],
            'status': {
                'hits': 1
            }
        }

        responses.get(
            f'{FAKE_API_URL}/search',
            json=in_
        )

        observed = list(goat_ds.get_by_id('taxon', ['9662']))
        mock_do_factory.assert_called_once_with(
            'taxon',
            id_='9662',
            attributes={
                'taxon_rank': 'species',
                'scientific_name': 'Meles meles',
                'genome_size': 1000,
                'chromosome_number': 44,
                'haploid_number': 22,
                'assembly_level': 'Chromosome',
                'ploidy': 2,
                'isb_wildlife_act_1976': ['IWA-Sch5'],
                'protection_of_badgers_act_1992': ['Badgers92'],
                'tolid_prefix': 'mMelMel',
                'common_name': 'Melon',
                'synonym': ['Meles alba', 'Meles britannicus']
            },
            to_one={}
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        api_ds = create_goat_datasource(
            FAKE_API_URL
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='taxon',
            id_='9662'
        )
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        in_ = {
            'results': [{
                'result': {
                    'taxon_id': '9662',
                    'taxon_rank': 'species',
                    'scientific_name': 'Meles meles',
                    'fields': {
                        'genome_size': {'value': 1000},
                        'chromosome_number': {'value': 44},
                        'haploid_number': {'value': 22},
                        'assembly_level': {'value': 'Chromosome'},
                        'ploidy': {'value': 2},
                        'isb_wildlife_act_1976': {'value': 'IWA-Sch5'},
                        'protection_of_badgers_act_1992': {'value': 'Badgers92'}
                    },
                    'names': {
                        'tolid_prefix': {
                            'class': [
                                'tolid_prefix'
                            ],
                            'name': [
                                'mMelMel'
                            ],
                            'source': [
                                'dtol sample naming'
                            ]
                        },
                        'common_name': {
                            'class': [
                                'common_name'
                            ],
                            'name': [
                                'Melon'
                            ],
                            'source': [
                                'animal genome size database'
                            ]
                        },
                        'synonym': {
                            'class': [
                                'synonym'
                            ],
                            'name': [
                                'Meles alba',
                                'Meles britannicus'
                            ],
                            'source': [
                                'some source'
                            ]
                        }
                    },
                }
            }],
            'status': {
                'hits': 1
            }
        }

        responses.get(
            f'{FAKE_API_URL}/search',
            json=in_
        )

        observed = list(
            api_ds.get_by_id('taxon', ['404', '9662'])
        )
        mock_do_factory.assert_called_once_with(
            'taxon',
            id_='9662',
            attributes={
                'taxon_rank': 'species',
                'scientific_name': 'Meles meles',
                'genome_size': 1000,
                'chromosome_number': 44,
                'haploid_number': 22,
                'assembly_level': 'Chromosome',
                'ploidy': 2,
                'isb_wildlife_act_1976': ['IWA-Sch5'],
                'protection_of_badgers_act_1992': ['Badgers92'],
                'tolid_prefix': 'mMelMel',
                'common_name': 'Melon',
                'synonym': ['Meles alba', 'Meles britannicus']
            },
            to_one={}
        )
        assert observed == [None, mock_data_object]
