# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import DataSourceError, ReqFieldsTree


class TestRequestedFieldsTree:
    def test_all_to_ones(self, mock_rel_ds):
        rft1 = ReqFieldsTree('sample_typ', mock_rel_ds, include_all_to_ones=False)
        assert rft1.to_paths() == []

        rft2 = ReqFieldsTree('sample_typ', mock_rel_ds, include_all_to_ones=True)
        assert rft2.to_paths() == [
            'accession_rel',
            'edited_by',
            'project_rel',
            'specimen_rel',
            'study_rel',
        ]

    def test_is_stub(self, mock_rel_ds):
        rft1 = ReqFieldsTree('sample_typ', mock_rel_ds, requested_fields=['id'])
        assert rft1.is_stub

        rft2 = ReqFieldsTree(
            'sample_typ', mock_rel_ds, requested_fields=['specimen_rel.id']
        )
        assert rft2.get_sub_tree('specimen_rel').is_stub

        rft3 = ReqFieldsTree('sample_typ', mock_rel_ds, requested_fields=[])
        assert not rft3.is_stub

        rft4 = ReqFieldsTree(
            'sample_typ', mock_rel_ds, requested_fields=['specimen_rel']
        )
        assert not rft4.is_stub

    @pytest.mark.parametrize(
        'rel_path',
        [
            'specimen_rel.species_rel.data_accession_rel',
            'specimen_rel.species_rel.data_accession_rel.id',
        ],
    )
    def test_multiple_hop(self, mock_rel_ds, rel_path):
        rft1 = ReqFieldsTree(
            'sample_typ',
            mock_rel_ds,
            requested_fields=[rel_path],
        )
        assert rft1.to_paths() == [rel_path]

    def test_to_many_paths(self, mock_rel_ds):
        to_many_paths = [
            'specimen_rel.species_rel.specimen_list.id',
            'specimen_rel.sample_list',
        ]
        rft = ReqFieldsTree(
            'sample_typ',
            mock_rel_ds,
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
    def test_bad_path(self, mock_rel_ds, bad_path):
        with pytest.raises(DataSourceError):
            ReqFieldsTree('sample_typ', mock_rel_ds, requested_fields=[bad_path])

    def test_de_dup_paths(self, mock_rel_ds):
        rft1 = ReqFieldsTree(
            'sample_typ',
            mock_rel_ds,
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
