# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import pytest

from tol.core.datasource import DataSource
from tol.core.factory import core_data_object
from tol.core.operator import DetailGetter, Relational
from tol.core.relationship import RelationshipConfig


class MockRelaionalDatasource(DataSource, DetailGetter, Relational):
    pass


@pytest.fixture
def mock_rel_ds():
    """
    A mock Relational DataSource. Object type names end with "_typ", to-one
    relationship names end with "_rel" and to-many end with "_list", making
    it clear which names are types or relationships, and ensuring that types
    and relationships are different and are therefore used in the correct
    places.
    """

    mock_ds = Mock(
        spec_set=MockRelaionalDatasource,
        supported_types=(
            'accession_typ',
            'authority_typ',
            'dna_typ',
            'project_typ',
            'sample_typ',
            'sex_typ',
            'species_typ',
            'specimen_typ',
            'standalone_typ',  # No relationship config
            'study_typ',
        ),
        attribute_types={
            'accession_typ': {
                'id': 'str',
                'secondary': 'str',
            },
            'authority_typ': {
                'id': 'str',
            },
            'dna_typ': {
                'id': 'str',
                'date': 'datetime',
                'bases': 'int',
                'reads': 'int',
                'mean_read_length': 'float',
            },
            'project_typ': {
                'id': 'str',
                'name': 'str',
                'description': 'str',
            },
            'sample_typ': {
                'id': 'str',
                'lims_id': 'str',
            },
            'sex_typ': {
                'id': 'str',
            },
            'species_typ': {
                'id': 'str',
                'common_name': 'str',
                'taxon_id': 'int',
            },
            'specimen_typ': {
                'id': 'str',
                'collected_on': 'date',
            },
            'study_typ': {
                'id': 'str',
                'name': 'str',
                'description': 'str',
            },
            'user_typ': {
                'id': 'str',
                'name': 'str',
                'email': 'str',
                'full_name': 'str',
                'organisation': 'str',
            },
        },
        relationship_config={
            'accession_typ': RelationshipConfig(
                to_one={
                    'authority_rel': 'authority_typ',
                },
                to_many={
                    'species_data_list': 'species_typ',
                    'species_umbrella_list': 'species_typ',
                    'sample_list': 'sample_typ',
                    'specimen_list': 'specimen_typ',
                },
            ),
            'dna_typ': RelationshipConfig(
                to_one={
                    'edited_by': 'user_typ',
                    'sample_rel': 'sample_typ',
                },
            ),
            'authority_typ': RelationshipConfig(),
            'project_typ': RelationshipConfig(
                to_many={
                    'sample_list': 'sample_typ',
                },
            ),
            'sample_typ': RelationshipConfig(
                to_one={
                    'accession_rel': 'accession_typ',
                    'edited_by': 'user_typ',
                    'project_rel': 'project_typ',
                    'specimen_rel': 'specimen_typ',
                    'study_rel': 'study_typ',
                },
                to_many={
                    'dna_rel': 'dna_typ',
                },
            ),
            'specimen_typ': RelationshipConfig(
                to_one={
                    'accession_rel': 'accession_typ',
                    'sex_rel': 'sex_typ',
                    'species_rel': 'species_typ',
                },
                to_many={
                    'sample_list': 'sample_typ',
                },
            ),
            'species_typ': RelationshipConfig(
                to_one={
                    'data_accession_rel': 'accession_typ',
                    'umbrella_accession_rel': 'accession_typ',
                },
                to_many={
                    'specimen_list': 'specimen_typ',
                },
            ),
        },
    )

    mdo = core_data_object(mock_ds)
    mock_ds.data_object_factory = mdo

    type_obj = {}
    type_obj['species_typ', 'Species mockus'] = mdo(
        'species_typ',
        id_='Species mockus',
        attributes={
            # Will not be dumped with include_all_to_ones=False
            'common_name': 'common mock species',
        },
        provenance_={
            'common_name': {
                'source_1': 'common mock species'
            }
        }
    )
    type_obj['species_typ', 'Species anothermockus'] = mdo(
        'species_typ',
        id_='Species anothermockus',
        attributes={
            # Will not be dumped with include_all_to_ones=False
            'common_name': 'another mock species',
        },
        provenance_={
            'common_name': {
                'source_1': 'another mock species'
            }
        }
    )
    type_obj['specimen_typ', 'SPMN/5678'] = mdo(
        'specimen_typ',
        id_='SPMN/5678',
        to_one={
            'accession_rel': None,
            'sex_rel': None,
            'species_rel': type_obj['species_typ', 'Species mockus'],
        },
        provenance_={
            'species_rel': {
                'source_1': type_obj['species_typ', 'Species mockus'],
                'source_2': type_obj['species_typ', 'Species anothermockus']
            }
        }
    )

    def mock_get_by_id(object_type: str, object_ids, **kwargs):
        return [type_obj[object_type, x] for x in object_ids]

    mock_ds.get_by_id = mock_get_by_id

    return mock_ds


@pytest.fixture
def mock_data_object(mock_rel_ds):
    return mock_rel_ds.data_object_factory
