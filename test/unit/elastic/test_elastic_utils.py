# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

import pytest

from tol.elastic.elastic_utils import ElasticUtils


@pytest.fixture
def mock_eds():
    eds = mock.Mock()
    eds.index_prefix = 'tol-production'
    eds.supported_types = ['sample', 'species', 'run_data']
    return eds


class TestCreateIndexSet:

    def test_dry_run_does_not_call_create(self, mock_eds):
        ElasticUtils.create_index_set(eds=mock_eds, build_number='2024-10', dry_run=True)

        mock_eds.es.indices.create.assert_not_called()

    def test_non_dry_run_calls_create_for_each_type(self, mock_eds):
        ElasticUtils.create_index_set(eds=mock_eds, build_number='2024-10', dry_run=False)

        assert mock_eds.es.indices.create.call_count == len(mock_eds.supported_types)

    def test_non_dry_run_uses_kebabcase_index_names(self, mock_eds):
        ElasticUtils.create_index_set(eds=mock_eds, build_number='2024-10', dry_run=False)

        calls = [c.kwargs['index'] for c in mock_eds.es.indices.create.call_args_list]
        assert 'tol-2024-10-run-data' in calls

    def test_dry_run_is_default(self, mock_eds):
        ElasticUtils.create_index_set(eds=mock_eds, build_number='2024-10')

        mock_eds.es.indices.create.assert_not_called()


class TestDeleteIndexSet:

    def test_dry_run_does_not_call_delete(self, mock_eds):
        ElasticUtils.delete_index_set(eds=mock_eds, build_number='2024-09', dry_run=True)

        mock_eds.es.indices.delete.assert_not_called()

    def test_non_dry_run_calls_delete_for_each_type(self, mock_eds):
        ElasticUtils.delete_index_set(eds=mock_eds, build_number='2024-09', dry_run=False)

        assert mock_eds.es.indices.delete.call_count == len(mock_eds.supported_types)

    def test_non_dry_run_uses_kebabcase_index_names(self, mock_eds):
        ElasticUtils.delete_index_set(eds=mock_eds, build_number='2024-09', dry_run=False)

        calls = [c.kwargs['index'] for c in mock_eds.es.indices.delete.call_args_list]
        assert 'tol-2024-09-run-data' in calls

    def test_dry_run_is_default(self, mock_eds):
        ElasticUtils.delete_index_set(eds=mock_eds, build_number='2024-09')

        mock_eds.es.indices.delete.assert_not_called()


class TestUpdateAliases:

    @pytest.fixture
    def mappings(self):
        return {
            'production': {'old': '2024-09', 'new': '2024-10'},
            'staging':    {'old': '2024-08', 'new': '2024-09'},
        }

    def test_dry_run_does_not_call_update_aliases(self, mock_eds, mappings):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings, dry_run=True)

        mock_eds.es.indices.update_aliases.assert_not_called()

    def test_non_dry_run_calls_update_aliases_once(self, mock_eds, mappings):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings, dry_run=False)

        mock_eds.es.indices.update_aliases.assert_called_once()

    def test_non_dry_run_actions_contain_remove_and_add_per_type_and_env(
        self, mock_eds, mappings
    ):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings, dry_run=False)

        actions = mock_eds.es.indices.update_aliases.call_args[0][0]['actions']
        # 3 types × 2 envs × 2 actions (remove + add) = 12
        assert len(actions) == 12
        action_types = {list(a.keys())[0] for a in actions}
        assert action_types == {'remove', 'add'}

    def test_non_dry_run_uses_correct_index_names(self, mock_eds, mappings):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings, dry_run=False)

        actions = mock_eds.es.indices.update_aliases.call_args[0][0]['actions']
        indices = {list(a.values())[0]['index'] for a in actions}
        assert 'tol-2024-09-run-data' in indices
        assert 'tol-2024-10-run-data' in indices

    def test_non_dry_run_uses_correct_alias_names(self, mock_eds, mappings):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings, dry_run=False)

        actions = mock_eds.es.indices.update_aliases.call_args[0][0]['actions']
        aliases = {list(a.values())[0]['alias'] for a in actions}
        assert 'tol-production-run-data' in aliases
        assert 'tol-staging-run-data' in aliases

    def test_dry_run_is_default(self, mock_eds, mappings):
        ElasticUtils.update_aliases(eds=mock_eds, mappings=mappings)

        mock_eds.es.indices.update_aliases.assert_not_called()
