# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import pytest

from tol.core import DataSourceError, ReqFieldsTree
from tol.core.datasource import DataSource
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig


class MockRelaionalDatasource(DataSource, Relational):
    pass


@pytest.fixture
def data_source():
    return Mock(
        spec_set=MockRelaionalDatasource,
        attribute_types={
            'accession_typ': {
                'id': 'str',
                'secondary': 'str',
            },
            'authority_typ': {
                'id': 'str',
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
            },
            'study_typ': {
                'id': 'str',
                'name': 'str',
                'description': 'str',
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
            'sample_typ': RelationshipConfig(
                to_one={
                    'accession_rel': 'accession_typ',
                    'project_rel': 'project_typ',
                    'specimen_rel': 'specimen_typ',
                    'study_rel': 'study_typ',
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


class TestRequestedFieldsTree:
    def test_all_to_ones(self, data_source):
        rft1 = ReqFieldsTree('sample_typ', data_source, include_all_to_ones=False)
        assert rft1.to_paths() == []

        rft2 = ReqFieldsTree('sample_typ', data_source, include_all_to_ones=True)
        assert rft2.to_paths() == [
            'accession_rel',
            'project_rel',
            'specimen_rel',
            'study_rel',
        ]

    def test_is_stub(self, data_source):
        rft1 = ReqFieldsTree('sample_typ', data_source, requested_fields=['id'])
        assert rft1.is_stub

        rft2 = ReqFieldsTree(
            'sample_typ', data_source, requested_fields=['specimen_rel.id']
        )
        assert rft2.get_sub_tree('specimen_rel').is_stub

        rft3 = ReqFieldsTree('sample_typ', data_source, requested_fields=[])
        assert not rft3.is_stub

        rft4 = ReqFieldsTree(
            'sample_typ', data_source, requested_fields=['specimen_rel']
        )
        assert not rft4.is_stub

    @pytest.mark.parametrize(
        'rel_path',
        [
            'specimen_rel.species_rel.data_accession_rel',
            'specimen_rel.species_rel.data_accession_rel.id',
        ],
    )
    def test_multiple_hop(self, data_source, rel_path):
        rft1 = ReqFieldsTree(
            'sample_typ',
            data_source,
            requested_fields=[rel_path],
        )
        assert rft1.to_paths() == [rel_path]

    def test_to_many_paths(self, data_source):
        to_many_paths = [
            'specimen_rel.species_rel.specimen_list.id',
            'specimen_rel.sample_list',
        ]
        rft = ReqFieldsTree(
            'sample_typ',
            data_source,
            requested_fields=to_many_paths,
        )
        assert rft.to_paths() == to_many_paths

    @pytest.mark.parametrize(
        'bad_path',
        [
            '.specimen_rel',  # Leading dot
            'specimen_rel.',  # Trailing dot
            'specimen_rel..species_rel',  # Double dot
            'specimen_rel.id.x',  # Path element after attribute
            'nonesuch',  # Non-existent attribute on root
            'specimen_rel.nonesuch',  # Non-existent attribute on relation
        ],
    )
    def test_bad_path(self, data_source, bad_path):
        with pytest.raises(DataSourceError):
            ReqFieldsTree('sample_typ', data_source, requested_fields=[bad_path])

    def test_de_dup_paths(self, data_source):
        rft1 = ReqFieldsTree(
            'sample_typ',
            data_source,
            requested_fields=[
                'specimen_rel.id',
                'specimen_rel.species_rel',
                'specimen_rel.species_rel.taxon_id',
                'specimen_rel.species_rel.common_name',
                'specimen_rel.sex_rel',
                'specimen_rel.sex_rel.id',
                'specimen_rel.sex_rel.id',
            ],
        )
        assert rft1.to_paths() == [
            'specimen_rel.id',
            'specimen_rel.species_rel.taxon_id',
            'specimen_rel.species_rel.common_name',
            'specimen_rel.sex_rel.id',
        ]
