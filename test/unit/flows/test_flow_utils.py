# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from tol.core import (
    DataSource,
    DataSourceFilter,
    core_data_object,
)
from tol.flows.converters import (
    ElasticObjectToPortaldbObjectConverter,
)
from tol.flows.flow_utils import FlowUtils


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['user', 'user_extra']

    @property
    def attribute_types(self):
        raise NotImplementedError()


@pytest.fixture
def mock_portaldb_ds():
    ds = _MockDataSource(config={})
    core_data_object(ds)
    portal_user = ds.data_object_factory(
        'user',
        id_='portal-1',
        attributes={'oidc_id': 'user@example.com'}
    )
    ds.get_one = MagicMock(return_value=portal_user)
    ds.get_list = MagicMock(return_value=[])
    return ds


@pytest.fixture
def mock_sts_ds():
    sts_user = MagicMock()
    sts_user.id = 'sts-1'
    sts_user.fullname = 'Test User'

    sts_user_extra = MagicMock()
    sts_user_extra.eln_api_key = 'secret-key'

    ds = MagicMock()
    ds.get_list.return_value = [sts_user]
    ds.get_one.return_value = sts_user_extra
    return ds


@pytest.fixture
def mock_objects_data_loader():
    with patch('tol.flows.flow_utils.ObjectsDataLoader') as mock_loader:
        yield mock_loader


@pytest.fixture
def mock_ids_data_loader():
    with patch('tol.flows.flow_utils.IdsDataLoader') as mock_loader:
        yield mock_loader


@pytest.fixture
def mock_sync_events_to_portal():
    with patch('tol.flows.flow_utils.FlowUtils.sync_events_to_portal') as m:
        yield m


@pytest.fixture
def data_source_instance():
    instance = MagicMock()
    instance.data_source_config.id = 'cfg-1'
    return instance


@pytest.fixture
def event_objects():
    objs = [MagicMock(), MagicMock()]
    for i, obj in enumerate(objs):
        obj.id = str(i)
    return objs


@pytest.fixture
def mock_eds():
    return MagicMock()


@pytest.fixture
def objects():
    return [MagicMock(), MagicMock()]


@pytest.fixture
def mock_benchling_ds():
    worklist_a = MagicMock()
    worklist_a.name = 'Worklist A'

    worklist_b = MagicMock()
    worklist_b.name = 'Worklist B'

    ds = MagicMock()
    ds.get_list.return_value = [worklist_a, worklist_b]
    return ds


class TestFlowUtilsGetUserNameAndElnApiKey:

    def test_returns_fullname_and_eln_api_key(self, mock_portaldb_ds, mock_sts_ds):
        mock_sts_ds.get_list.return_value[0].fullname = 'Jane Smith'
        mock_sts_ds.get_one.return_value.eln_api_key = 'my-api-key'

        fullname, api_key = FlowUtils.get_user_name_and_eln_api_key(
            portaldb_ds=mock_portaldb_ds, sts_ds=mock_sts_ds, portal_user_id='portal-1'
        )

        assert fullname == 'Jane Smith'
        assert api_key == 'my-api-key'

    def test_raises_if_user_extra_not_found(self, mock_portaldb_ds, mock_sts_ds):
        mock_sts_ds.get_list.return_value[0].id = 'sts-99'
        mock_sts_ds.get_one.return_value = None

        with pytest.raises(ValueError, match='sts-99'):
            FlowUtils.get_user_name_and_eln_api_key(
                portaldb_ds=mock_portaldb_ds, sts_ds=mock_sts_ds, portal_user_id='portal-1'
            )

    def test_raises_if_multiple_sts_users_found(self, mock_portaldb_ds, mock_sts_ds):
        extra_user = MagicMock()
        extra_user.id = 'sts-2'
        mock_sts_ds.get_list.return_value = [mock_sts_ds.get_list.return_value[0], extra_user]

        with pytest.raises(AssertionError):
            FlowUtils.get_user_name_and_eln_api_key(
                portaldb_ds=mock_portaldb_ds, sts_ds=mock_sts_ds, portal_user_id='portal-1'
            )

    def test_raises_if_no_sts_user_found(self, mock_portaldb_ds, mock_sts_ds):
        mock_sts_ds.get_list.return_value = []

        with pytest.raises(AssertionError):
            FlowUtils.get_user_name_and_eln_api_key(
                portaldb_ds=mock_portaldb_ds, sts_ds=mock_sts_ds, portal_user_id='portal-1'
            )

    def test_filters_sts_users_by_email(self, mock_portaldb_ds, mock_sts_ds):
        FlowUtils.get_user_name_and_eln_api_key(
            portaldb_ds=mock_portaldb_ds, sts_ds=mock_sts_ds, portal_user_id='portal-1'
        )

        call_args = mock_sts_ds.get_list.call_args
        passed_filter: DataSourceFilter = call_args.kwargs.get(
            'object_filters', call_args.args[1] if len(call_args.args) > 1 else None
        )
        assert passed_filter.and_['email']['eq']['value'] == 'user@example.com'


class TestFlowUtilsGetWorklist:

    def test_returns_matching_worklist(self, mock_benchling_ds):
        result = FlowUtils.get_worklist(bds=mock_benchling_ds, worklist_name='Worklist A')

        assert result is mock_benchling_ds.get_list.return_value[0]
        assert result.name == 'Worklist A'
        mock_benchling_ds.get_list.assert_called_once_with('worklist')

    def test_returns_none_if_name_is_none(self, mock_benchling_ds):
        result = FlowUtils.get_worklist(bds=mock_benchling_ds, worklist_name=None)

        assert result is None
        mock_benchling_ds.get_list.assert_not_called()

    def test_returns_none_if_not_found(self, mock_benchling_ds):
        result = FlowUtils.get_worklist(bds=mock_benchling_ds, worklist_name='Nonexistent')

        assert result is None

    def test_returns_none_if_get_list_raises(self, mock_benchling_ds):
        mock_benchling_ds.get_list.side_effect = Exception('connection error')

        result = FlowUtils.get_worklist(bds=mock_benchling_ds, worklist_name='Worklist A')

        assert result is None


class TestFlowUtilsGetFolder:

    def test_returns_folder_when_found(self, mock_benchling_ds):
        folder = MagicMock()
        folder.name = 'My Folder'
        mock_benchling_ds.get_list.return_value = iter([folder])

        result = FlowUtils.get_folder(bds=mock_benchling_ds, folder_name='My Folder')
        assert result is folder
        call_args = mock_benchling_ds.get_list.call_args
        assert call_args.args[0] == 'folder'

    def test_returns_none_when_name_is_none(self, mock_benchling_ds):
        result = FlowUtils.get_folder(bds=mock_benchling_ds, folder_name=None)

        assert result is None
        mock_benchling_ds.get_list.assert_not_called()

    def test_returns_none_when_not_found(self, mock_benchling_ds):
        mock_benchling_ds.get_list.return_value = iter([])

        result = FlowUtils.get_folder(bds=mock_benchling_ds, folder_name='Missing Folder')

        assert result is None

    def test_returns_none_if_get_list_raises(self, mock_benchling_ds):
        mock_benchling_ds.get_list.side_effect = Exception('connection error')

        result = FlowUtils.get_worklist(bds=mock_benchling_ds, worklist_name='Worklist A')

        assert result is None


class TestFlowUtilsSyncEventsToPortal:

    def test_constructs_loader_with_correct_types(
        self, mock_objects_data_loader, mock_eds, mock_portaldb_ds, objects
    ):
        FlowUtils.sync_events_to_portal(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            objects=objects,
            object_type='sample'
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['source_object_type'] == 'sample_event'
        assert kwargs['destination_object_type'] == 'sample'

    def test_calls_load_with_portaldb_provenance(
        self, mock_objects_data_loader, mock_eds, mock_portaldb_ds, objects
    ):
        FlowUtils.sync_events_to_portal(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            objects=objects,
            object_type='sample'
        )

        mock_objects_data_loader.return_value.load.assert_called_once_with(provenance='portaldb')

    def test_passes_objects_to_loader(
        self, mock_objects_data_loader, mock_eds, mock_portaldb_ds, objects
    ):
        FlowUtils.sync_events_to_portal(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            objects=objects,
            object_type='sample'
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['objects'] is objects

    def test_uses_eds_as_destination_and_portaldb_as_source(
        self, mock_objects_data_loader, mock_eds, mock_portaldb_ds, objects
    ):
        FlowUtils.sync_events_to_portal(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            objects=objects,
            object_type='sample'
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['source'] is mock_portaldb_ds
        assert kwargs['destination'] is mock_eds

    def test_returns_empty_list_on_exception(
        self, mock_objects_data_loader, mock_eds, mock_portaldb_ds, objects
    ):
        mock_objects_data_loader.return_value.load.side_effect = Exception('connection error')

        result = FlowUtils.sync_events_to_portal(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            objects=objects,
            object_type='sample'
        )

        assert result == []


class TestFlowUtilsSyncSummariseEnrich:

    def test_syncs_events_to_portal(
        self, mock_sync_events_to_portal,
        mock_eds, mock_portaldb_ds, data_source_instance, event_objects
    ):
        FlowUtils.sync_summarise_enrich(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            event_objects=iter(event_objects),
            object_type='sample',
            data_source_instance=data_source_instance,
            sleep_time=0
        )

        mock_sync_events_to_portal.assert_called_once()
        _, kwargs = mock_sync_events_to_portal.call_args
        assert kwargs['object_type'] == 'sample'
        assert kwargs['eds'] is mock_eds
        assert kwargs['portaldb_ds'] is mock_portaldb_ds

    def test_summarises_objects(
        self, mock_sync_events_to_portal,
        mock_eds, mock_portaldb_ds, data_source_instance, event_objects
    ):
        FlowUtils.sync_summarise_enrich(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            event_objects=iter(event_objects),
            object_type='sample',
            data_source_instance=data_source_instance,
            sleep_time=0
        )

        # portaldb_ds.get_list returns [] so summaries=[] is passed through to eds
        mock_eds.resummarise_by_ids.assert_called_once_with(
            [],
            source_object_type='sample',
            source_object_ids=[obj.id for obj in event_objects]
        )

    def test_enriches_source_objects(
        self, mock_sync_events_to_portal,
        mock_eds, mock_portaldb_ds, data_source_instance, event_objects
    ):
        mock_eds.relationships_to_enrich = {'sample': {'species': None}}

        FlowUtils.sync_summarise_enrich(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            event_objects=iter(event_objects),
            object_type='sample',
            data_source_instance=data_source_instance,
            sleep_time=0
        )

        mock_eds.get_by_ids.assert_called_with('sample', [obj.id for obj in event_objects])

    def test_enriches_changed_types_from_summarise(
        self, mock_sync_events_to_portal,
        mock_eds, mock_portaldb_ds, data_source_instance, event_objects
    ):
        mock_eds.resummarise_by_ids.return_value = {
            'species': ['sp-1', 'sp-2'],
            'tolid': []  # empty — should NOT trigger enrich
        }
        mock_eds.relationships_to_enrich = {
            'sample': {},
            'species': {'run': None},
        }

        FlowUtils.sync_summarise_enrich(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            event_objects=iter(event_objects),
            object_type='sample',
            data_source_instance=data_source_instance,
            sleep_time=0
        )

        enrich_source_types = [c.args[0] for c in mock_eds.enrich.call_args_list]
        assert 'species' in enrich_source_types
        assert 'tolid' not in enrich_source_types

    def test_total_enrich_calls_with_changes(
        self, mock_sync_events_to_portal,
        mock_eds, mock_portaldb_ds, data_source_instance, event_objects
    ):
        # 2 non-empty change types + 1 for source objects = 3 eds.enrich calls total
        mock_eds.resummarise_by_ids.return_value = {
            'species': ['sp-1'],
            'tolid': ['tol-1'],
        }
        mock_eds.relationships_to_enrich = {
            'sample': {'x': None},
            'species': {'y': None},
            'tolid': {'z': None},
        }

        FlowUtils.sync_summarise_enrich(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            event_objects=iter(event_objects),
            object_type='sample',
            data_source_instance=data_source_instance,
            sleep_time=0
        )

        assert mock_eds.enrich.call_count == 3


class TestFlowUtilsRecordEvents:

    def test_passes_ids_and_object_types_to_loader(
        self, mock_ids_data_loader, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_events(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            ids=['id-1', 'id-2'],
            source_object_type='sample',
            destination_object_type='sample_event',
            fields={'date_abandoned': '2026-01-01'},
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['source'] is mock_eds
        assert kwargs['destination'] is mock_portaldb_ds
        assert kwargs['source_object_type'] == 'sample'
        assert kwargs['destination_object_type'] == 'sample_event'
        assert kwargs['object_ids'] == ['id-1', 'id-2']

    def test_builds_converter_with_correct_config(
        self, mock_ids_data_loader, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_events(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            ids=['id-1'],
            source_object_type='sample',
            destination_object_type='sample_event',
            fields={'date_abandoned': '2026-01-01'},
            id_field='sts_tolid.id',
            incremental=True,
        )

        _, kwargs = mock_ids_data_loader.call_args
        converter = kwargs['converter']
        assert isinstance(converter, ElasticObjectToPortaldbObjectConverter)
        assert converter.config.destination_object_type == 'sample_event'
        assert converter.config.id_field == 'sts_tolid.id'
        assert converter.config.incremental is True
        assert converter.config.fields == {'date_abandoned': '2026-01-01'}

    def test_omits_id_field_from_config_when_not_provided(
        self, mock_ids_data_loader, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_events(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            ids=['id-1'],
            source_object_type='sample',
            destination_object_type='sample_event',
            fields={},
        )

        _, kwargs = mock_ids_data_loader.call_args
        converter = kwargs['converter']
        # id_field should fall back to the dataclass default
        assert converter.config.id_field == 'id'

    def test_calls_load_and_returns_iterable(
        self, mock_ids_data_loader, mock_eds, mock_portaldb_ds
    ):
        sentinel = iter([MagicMock()])
        mock_ids_data_loader.return_value.load.return_value = sentinel

        result = FlowUtils.record_events(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            ids=['id-1'],
            source_object_type='sample',
            destination_object_type='sample_event',
            fields={},
        )

        mock_ids_data_loader.return_value.load.assert_called_once_with(auto_exhaust=False)
        assert result is not None

    def test_returns_empty_list_on_exception(
        self, mock_ids_data_loader, mock_eds, mock_portaldb_ds
    ):
        mock_ids_data_loader.side_effect = Exception('connection error')

        result = FlowUtils.record_events(
            eds=mock_eds,
            portaldb_ds=mock_portaldb_ds,
            ids=['id-1'],
            source_object_type='sample',
            destination_object_type='sample_event',
            fields={},
        )

        assert result == []
