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
            'staging': {'old': '2024-08', 'new': '2024-09'},
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


class TestEnrichObjects:

    def test_calls_enrich_for_each_target_type(self, mock_eds):
        mock_eds.relationships_to_enrich = {
            'sample': {'species': {}, 'tolid': {}}
        }
        source_objects = [mock.Mock(), mock.Mock()]
        mock_eds.get_by_ids.return_value = source_objects

        ElasticUtils.enrich_objects(eds=mock_eds, object_type='sample', ids=['1', '2'])

        assert mock_eds.enrich.call_count == 2
        called_targets = {c.args[2] for c in mock_eds.enrich.call_args_list}
        assert called_targets == {'species', 'tolid'}

    def test_fetches_source_objects_by_ids(self, mock_eds):
        mock_eds.relationships_to_enrich = {'sample': {'species': {}}}
        mock_eds.get_by_ids.return_value = []

        ElasticUtils.enrich_objects(eds=mock_eds, object_type='sample', ids=['10', '20'])

        mock_eds.get_by_ids.assert_called_once_with('sample', ['10', '20'])

    def test_passes_source_objects_to_enrich(self, mock_eds):
        source_objects = [mock.Mock(), mock.Mock()]
        mock_eds.relationships_to_enrich = {'sample': {'species': {}}}
        mock_eds.get_by_ids.return_value = source_objects

        ElasticUtils.enrich_objects(eds=mock_eds, object_type='sample', ids=['1'])

        mock_eds.enrich.assert_called_once_with('sample', source_objects, 'species')

    def test_does_nothing_when_no_relationships(self, mock_eds):
        mock_eds.relationships_to_enrich = {'sample': {}}

        ElasticUtils.enrich_objects(eds=mock_eds, object_type='sample', ids=['1'])

        mock_eds.enrich.assert_not_called()
        mock_eds.get_by_ids.assert_not_called()


class TestSummariseObjects:

    @pytest.fixture
    def mock_portaldb_ds(self):
        return mock.Mock()

    @pytest.fixture
    def data_source_instance(self):
        instance = mock.Mock()
        instance.data_source_config.id = 'cfg-42'
        return instance

    def test_queries_summaries_by_object_type_and_config(
        self, mock_eds, mock_portaldb_ds, data_source_instance
    ):
        mock_portaldb_ds.get_list.return_value = []
        mock_eds.resummarise_by_ids.return_value = {}

        ElasticUtils.summarise_objects(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            object_type='sample',
            ids=['1', '2'],
            data_source_instance=data_source_instance
        )

        call_args = mock_portaldb_ds.get_list.call_args
        assert call_args.args[0] == 'data_source_config_summary'
        f = call_args.kwargs.get(
            'object_filters',
            call_args.args[1] if len(call_args.args) > 1 else None
        )
        assert f.and_['source_object_type']['eq']['value'] == 'sample'
        assert f.and_['data_source_config.id']['eq']['value'] == 'cfg-42'

    def test_calls_resummarise_with_summaries_and_ids(
        self, mock_eds, mock_portaldb_ds, data_source_instance
    ):
        summaries = [mock.Mock(), mock.Mock()]
        mock_portaldb_ds.get_list.return_value = summaries
        mock_eds.resummarise_by_ids.return_value = {}

        ElasticUtils.summarise_objects(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            object_type='sample',
            ids=['1', '2'],
            data_source_instance=data_source_instance
        )

        mock_eds.resummarise_by_ids.assert_called_once_with(
            summaries,
            source_object_type='sample',
            source_object_ids=['1', '2']
        )

    def test_returns_changes_from_resummarise(
        self, mock_eds, mock_portaldb_ds, data_source_instance
    ):
        mock_portaldb_ds.get_list.return_value = []
        expected = {'species': ['sp-1', 'sp-2']}
        mock_eds.resummarise_by_ids.return_value = expected

        result = ElasticUtils.summarise_objects(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            object_type='sample',
            ids=['1'],
            data_source_instance=data_source_instance
        )

        assert result == expected
