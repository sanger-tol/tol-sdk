# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask

import pytest

from tol.api_base.blueprint import _core_blueprint
from tol.api_client.view import DefaultView
from tol.core import DataSource, ReqFieldsTree
from tol.core.data_source_dict import DataSourceDict


# Default requested fields tree for the "test" object type
test_req_flds_tree = ReqFieldsTree(
    'test',
    create_autospec(DataSource),
)


@pytest.fixture
def sample_req_fields_tree(mock_rel_ds):
    return ReqFieldsTree('sample_typ', mock_rel_ds, include_all_to_ones=True)


class TestDefaultView:
    def test_dump_one_object(self, mock_data_object, sample_req_fields_tree):
        """
        Test dumping one object with no relationships
        """
        obj = mock_data_object(
            'sample_typ',
            id_='SMPL9606',
            attributes={'lims_id': 'ID45980'},
        )
        dump = DefaultView(sample_req_fields_tree).dump(obj)
        expected = {
            'data': {
                'type': 'sample_typ',
                'id': 'SMPL9606',
                'attributes': {'lims_id': 'ID45980'},
                'relationships': {
                    'dna_rel': {
                        'links': {'related': '/sample_typ/SMPL9606/dna_rel'},
                    }
                },
            },
        }
        assert dump == expected

    def test_dump_many_objects(self, mock_data_object, sample_req_fields_tree):
        """
        Dump a list of objects with no relationships
        """
        objs = [
            mock_data_object(
                'sample_typ',
                id_=f'SMPL{i}',
                attributes={'lims_id': f'LIMS{i}'},
            )
            for i in range(5)
        ]
        dump = DefaultView(sample_req_fields_tree).dump_bulk(objs)
        expected = {
            'data': [
                {
                    'type': 'sample_typ',
                    'id': f'SMPL{i}',
                    'attributes': {'lims_id': f'LIMS{i}'},
                    'relationships': {
                        'dna_rel': {
                            'links': {'related': f'/sample_typ/SMPL{i}/dna_rel'},
                        }
                    },
                }
                for i in range(5)
            ]
        }
        assert dump == expected

    def test_relationships(self, mock_data_object, mock_rel_ds):
        """
        Dump with relationships. Doesn't include non set to_one objects
        """

        (mock_specimen,) = mock_rel_ds.get_by_id('specimen_typ', ['SPMN/5678'])

        # the expected dumped output
        expected1 = {
            'data': {
                'type': 'specimen_typ',
                'id': 'SPMN/5678',
                'attributes': {
                    'provenance': {
                        'species_rel': {
                            'source_1': {
                                'data': {
                                    'type': 'species_typ',
                                    'id': 'Species mockus',
                                }
                            },
                            'source_2': {
                                'data': {
                                    'type': 'species_typ',
                                    'id': 'Species anothermockus',
                                }
                            }
                        }
                    },
                },
                'relationships': {
                    'accession_rel': None,
                    'sex_rel': None,
                    'species_rel': {
                        'data': {
                            'type': 'species_typ',
                            'id': 'Species mockus',
                        },
                    },
                    'sample_list': {
                        'links': {'related': '/random/specimen_typ/SPMN%2F5678/sample_list'},
                    },
                },
            }
        }
        rft1 = ReqFieldsTree('specimen_typ', mock_rel_ds, include_all_to_ones=False)
        dump1 = DefaultView(rft1, prefix='/random').dump(mock_specimen)
        assert dump1 == expected1

        # The `species_typ` object will be present in an `included` list when
        # `include_all_to_ones=True`
        expected2 = {
            **expected1,
            'included': [
                {
                    'type': 'species_typ',
                    'id': 'Species mockus',
                    'attributes': {
                        'common_name': 'common mock species',
                        'provenance': {
                            'common_name': {'source_1': 'common mock species'}
                        }
                    },
                    'relationships': {
                        'specimen_list': {
                            'links': {
                                'related': '/random/species_typ/Species%20mockus/specimen_list',
                            },
                        }
                    },
                }, {
                    'type': 'species_typ',
                    'id': 'Species anothermockus',
                    'attributes': {
                        'common_name': 'another mock species',
                        'provenance': {
                            'common_name': {'source_1': 'another mock species'}
                        }
                    },
                    'relationships': {
                        'specimen_list': {
                            'links': {
                                'related': '/random/species_typ/Species%20anothermockus/specimen_list',
                            },
                        }
                    },
                },
            ],
        }

        rft2 = ReqFieldsTree('specimen_typ', mock_rel_ds, include_all_to_ones=True)
        dump2 = DefaultView(rft2, prefix='/random').dump(mock_specimen)
        assert dump2 == expected2

    def test_to_many_dump(self, mock_data_object, mock_rel_ds):
        """
        Test that a list of to-many objects is dumped.
        """

        view = DefaultView(
            ReqFieldsTree(
                'sample_typ',
                mock_rel_ds,
                requested_fields=['dna_rel'],
            ),
            prefix='/data',
        )

        # Two DNA objects
        dna_obj = [
            mock_data_object('dna_typ', id_='DNA1', attributes={'bases': 1_000_000}),
            mock_data_object('dna_typ', id_='DNA2', attributes={'bases': 2_000_000}),
        ]
        smpl1 = mock_data_object(
            'sample_typ',
            id_='SMPL#many_dna',
            to_many={'dna_rel': dna_obj},
        )
        dump1 = view.dump(smpl1)
        expected1 = {
            'data': {
                'type': 'sample_typ',
                'id': 'SMPL#many_dna',
                'relationships': {
                    'dna_rel': {
                        'data': [
                            {'type': 'dna_typ', 'id': 'DNA1'},
                            {'type': 'dna_typ', 'id': 'DNA2'},
                        ]
                    },
                },
            },
            'included': [
                {'type': 'dna_typ', 'id': 'DNA1', 'attributes': {'bases': 1_000_000}},
                {'type': 'dna_typ', 'id': 'DNA2', 'attributes': {'bases': 2_000_000}},
            ],
        }
        assert dump1 == expected1

        # No DNA objects
        smpl2 = mock_data_object(
            'sample_typ',
            id_='SMPL#no_dna',
            to_one={
                'accession_rel': None,
                'study_rel': None,
            },
            to_many={'dna_rel': []},
        )
        dump2 = view.dump(smpl2)
        expected2 = {
            'data': {
                'type': 'sample_typ',
                'id': 'SMPL#no_dna',
                'relationships': {
                    'accession_rel': None,
                    'study_rel': None,
                    'dna_rel': {'data': []},
                },
            },
        }
        assert dump2 == expected2

    def test_relationship_no_id(self, mock_data_object, mock_rel_ds):
        """
        Test that we get the expected `ValueError` exceptions with to-one and
        to-many objects with null IDs.
        """

        view = DefaultView(
            ReqFieldsTree(
                'sample_typ',
                mock_rel_ds,
                requested_fields=['specimen_rel', 'dna_rel'],
            ),
            prefix='/data',
        )

        bad_specimen = mock_data_object('specimen_typ', None)
        smpl1 = mock_data_object(
            'sample_typ',
            id_='SMPL#fail1',
            to_one={'specimen_rel': bad_specimen},
        )
        with pytest.raises(ValueError, match=r'Cannot serialise.+no `id` attribute'):
            view.dump(smpl1)

        bad_dna = mock_data_object('dna_typ', None)
        smpl2 = mock_data_object(
            'sample_typ',
            id_='SMPL#fail2',
            to_many={'dna_rel': [bad_dna]},
        )
        with pytest.raises(ValueError, match=r'Cannot serialise.+no `id` attribute'):
            view.dump(smpl2)

    def test_meta(self, mock_data_object, sample_req_fields_tree):
        """Dump a single object with document meta"""
        obj = mock_data_object(
            'sample_typ',
            id_='SMPL009',
            attributes={'lims_id': 'LIMS009'},
        )
        meta = {
            'meta': 'you bet!',
            '2+2': '5',
        }
        expected = {
            'meta': meta,
            'data': {
                'type': 'sample_typ',
                'id': 'SMPL009',
                'attributes': {'lims_id': 'LIMS009'},
                'relationships': {
                    'dna_rel': {
                        'links': {'related': '/sample_typ/SMPL009/dna_rel'},
                    }
                },
            },
        }
        observed = DefaultView(sample_req_fields_tree).dump(obj, document_meta=meta)
        assert expected == observed

    def test_bulk_meta(self, mock_data_object, sample_req_fields_tree):
        """Dump many objects with document meta"""
        objs = [
            mock_data_object(
                'sample_typ',
                id_=f'SMPL{i:03d}',
                attributes={'lims_id': f'LIMS{i:03d}'},
            )
            for i in range(50)
        ]
        meta = {
            'meta': 'you bet!',
            '2+2': '5',
        }
        expected = {
            'data': [
                {
                    'type': 'sample_typ',
                    'id': f'SMPL{i:03d}',
                    'attributes': {'lims_id': f'LIMS{i:03d}'},
                    'relationships': {
                        'dna_rel': {
                            'links': {'related': f'/sample_typ/SMPL{i:03d}/dna_rel'},
                        }
                    },
                }
                for i in range(50)
            ],
            'meta': meta,
        }
        observed = DefaultView(sample_req_fields_tree).dump_bulk(objs, document_meta=meta)
        assert expected == observed

    def test_no_relationship_config(self, mock_data_object):
        """
        no `RelationshipConfig` is defined for the given type
        """

        mock_obj = mock_data_object(
            'standalone_typ',
            id_='lol',
        )
        view = DefaultView(test_req_flds_tree)
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']

    def test_empty_relationship_config(self, mock_data_object):
        """
        the `RelationshipConfig` for the given type is empty
        """

        mock_obj = mock_data_object(
            'authority_typ',  # Has no relations defined
            id_='NCBI',
        )
        view = DefaultView(test_req_flds_tree)
        observed = view.dump(mock_obj)
        assert 'relationships' not in observed['data']


@pytest.fixture
def test_app(mock_rel_ds):
    app = Flask(__name__)
    blueprint = _core_blueprint(
        DataSourceDict(mock_rel_ds),
        '/super_data',
    )
    app.register_blueprint(blueprint)
    app.config.update({'TESTING': True})
    return app


class TestDefaultViewInBlueprint:
    """
    Tests the `DefaultView` within a data blueprint
    """

    def test_relationships(self, test_app):
        """
        relation links work, in a `DataBlueprint`
        """

        response = test_app.test_client().get('/super_data/specimen_typ/SPMN%2F5678')
        assert response.status_code == 200
        expected = {
            'data': {
                'type': 'specimen_typ',
                'id': 'SPMN/5678',
                'attributes': {
                    'provenance': {
                        'species_rel': {
                            'source_1': {
                                'data': {
                                    'type': 'species_typ',
                                    'id': 'Species mockus',
                                }
                            },
                            'source_2': {
                                'data': {
                                    'type': 'species_typ',
                                    'id': 'Species anothermockus',
                                }
                            }
                        }
                    },
                },
                'relationships': {
                    'accession_rel': None,
                    'sample_list': {
                        'links': {'related': '/super_data/specimen_typ/SPMN%2F5678/sample_list'}
                    },
                    'sex_rel': None,
                    'species_rel': {
                        'data': {
                            'type': 'species_typ',
                            'id': 'Species mockus',
                        }
                    },
                },
            },
            'included': [
                {
                    'type': 'species_typ',
                    'id': 'Species mockus',
                    'attributes': {
                        'common_name': 'common mock species',
                        'provenance': {
                            'common_name': {'source_1': 'common mock species'}
                        }
                    },
                    'relationships': {
                        'specimen_list': {
                            'links': {
                                'related': (
                                    '/super_data/species_typ/Species%20mockus/specimen_list'
                                )
                            }
                        }
                    },
                },
{
                    'type': 'species_typ',
                    'id': 'Species anothermockus',
                    'attributes': {
                        'common_name': 'another mock species',
                        'provenance': {
                            'common_name': {'source_1': 'another mock species'}
                        }
                    },
                    'relationships': {
                        'specimen_list': {
                            'links': {
                                'related': (
                                    '/super_data/species_typ/Species%20anothermockus/specimen_list'
                                )
                            }
                        }
                    },
                },
            ],
        }
        observed = response.json
        assert observed == expected
