# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from tol.core import (
    DataSource,
    DataSourceFilter,
    ErrorObject,
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
def mock_bds():
    return MagicMock()


@pytest.fixture
def mock_default_data_loader():
    with patch('tol.flows.flow_utils.DefaultDataLoader') as mock_loader:
        yield mock_loader


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
def mock_record_events():
    with patch('tol.flows.flow_utils.FlowUtils.record_events') as m:
        yield m


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
            id_field='tolid.id',
            incremental=True,
        )

        _, kwargs = mock_ids_data_loader.call_args
        converter = kwargs['converter']
        assert isinstance(converter, ElasticObjectToPortaldbObjectConverter)
        assert converter.config.destination_object_type == 'sample_event'
        assert converter.config.id_field == 'tolid.id'
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


class TestFlowUtilsTolIdIdField:

    def test_tolid_returns_id(self):
        assert FlowUtils._tolid_id_field('tolid') == 'id'

    def test_sample_returns_sts_tolid_id(self):
        assert FlowUtils._tolid_id_field('sample') == 'tolid.id'

    def test_other_returns_benchling_tolid_id(self):
        assert FlowUtils._tolid_id_field('extraction') == 'tolid.id'


class TestFlowUtilsRecordTolIdEvents:

    def test_passes_eds_portaldb_and_ids(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=['id-1'], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['eds'] is mock_eds
        assert kwargs['portaldb_ds'] is mock_portaldb_ds
        assert kwargs['ids'] == ['id-1']

    def test_source_object_type_is_object_type(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='extraction', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['source_object_type'] == 'extraction'

    def test_destination_object_type_is_tolid_event(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['destination_object_type'] == 'tolid_event'

    def test_incremental_is_true(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['incremental'] is True

    def test_fields_contain_topup_date_and_user_id(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-99'
        )

        _, kwargs = mock_record_events.call_args
        assert 'date_topup_actioned' in kwargs['fields']
        assert kwargs['fields']['topup_actioned_by'] == 'user-99'

    def test_id_field_uses_tolid_id_field(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_tolid_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['id_field'] == 'tolid.id'


class TestFlowUtilsRecordActionedEvents:

    def test_destination_object_type_includes_object_type(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_actioned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='extraction', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['destination_object_type'] == 'extraction_event'

    def test_fields_contain_topup_date_and_user(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_actioned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-42'
        )

        _, kwargs = mock_record_events.call_args
        assert 'date_topup_actioned' in kwargs['fields']
        assert kwargs['fields']['topup_actioned_by'] == 'user-42'

    def test_no_id_field_override(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_actioned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert 'id_field' not in kwargs


class TestFlowUtilsRecordAbandonedEvents:

    def test_destination_object_type_includes_object_type(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_abandoned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='extraction', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['destination_object_type'] == 'extraction_event'

    def test_fields_contain_abandoned_date_and_user(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_abandoned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-7'
        )

        _, kwargs = mock_record_events.call_args
        assert 'date_abandoned' in kwargs['fields']
        assert kwargs['fields']['abandoned_by'] == 'user-7'

    def test_no_id_field_override(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_abandoned_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert 'id_field' not in kwargs


class TestFlowUtilsRecordReviewEvents:

    def test_destination_object_type_is_tolid_event(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_review_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['destination_object_type'] == 'tolid_event'

    def test_in_review_true_sets_date_and_user_and_flag(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_review_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-5', in_review=True
        )

        _, kwargs = mock_record_events.call_args
        assert 'date_sent_to_review' in kwargs['fields']
        assert kwargs['fields']['sent_to_review_by'] == 'user-5'
        assert kwargs['fields']['in_review'] is True

    def test_in_review_false_sets_only_flag(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_review_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-5', in_review=False
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['fields'] == {'in_review': False}

    def test_id_field_uses_tolid_id_field(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_review_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='extraction', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['id_field'] == 'tolid.id'

    def test_in_review_defaults_to_true(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_review_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], object_type='sample', user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['fields']['in_review'] is True


class TestFlowUtilsRecordSpeciesEvents:

    def test_source_and_destination_types(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_species_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['source_object_type'] == 'species'
        assert kwargs['destination_object_type'] == 'species_event'

    def test_id_field_is_id(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_species_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['id_field'] == 'id'

    def test_fields_contain_date_user_and_reason(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_species_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], user_id='user-3', recollection_reason='damaged'
        )

        _, kwargs = mock_record_events.call_args
        assert 'date_marked_for_recollection' in kwargs['fields']
        assert kwargs['fields']['marked_for_recollection_by'] == 'user-3'
        assert kwargs['fields']['marked_for_recollection_reason'] == 'damaged'

    def test_none_reason_passed_through(
        self, mock_record_events, mock_eds, mock_portaldb_ds
    ):
        FlowUtils.record_species_events(
            eds=mock_eds, portaldb_ds=mock_portaldb_ds,
            ids=[], user_id='user-1'
        )

        _, kwargs = mock_record_events.call_args
        assert kwargs['fields']['marked_for_recollection_reason'] is None


class TestFlowUtilsSyncSamplesToPortalByIds:

    def test_uses_sts_as_source_and_eds_as_destination(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=['id-1'], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        _, kwargs = mock_default_data_loader.call_args
        assert kwargs['source'] is mock_sts_ds
        assert kwargs['destination'] is mock_eds

    def test_source_and_destination_object_types(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        _, kwargs = mock_default_data_loader.call_args
        assert kwargs['source_object_type'] == 'sample_project'
        assert kwargs['destination_object_type'] == 'sample'

    def test_filter_contains_ids(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=['s-1', 's-2'], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        _, kwargs = mock_default_data_loader.call_args
        f: DataSourceFilter = kwargs['object_filters']
        assert f.and_['sample.id']['in_list']['value'] == ['s-1', 's-2']

    def test_fetches_requested_fields_from_loader_14(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        mock_portaldb_ds.get_one.assert_called_once_with('loader', 14)

    def test_passes_requested_fields_to_loader(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        requested_fields = MagicMock()
        mock_portaldb_ds.get_one.return_value.requested_fields = requested_fields

        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        _, kwargs = mock_default_data_loader.call_args
        assert kwargs['requested_fields'] is requested_fields

    def test_uses_sts_sample_project_converter(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        from tol.flows.converters import StsSampleProjectToElasticSampleConverter

        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        _, kwargs = mock_default_data_loader.call_args
        assert kwargs['convert_class'] is StsSampleProjectToElasticSampleConverter

    def test_calls_load_with_sts_provenance(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        mock_default_data_loader.return_value.load.assert_called_once_with(provenance='sts')

    def test_returns_empty_list_on_exception(
        self, mock_default_data_loader, mock_eds, mock_sts_ds, mock_portaldb_ds
    ):
        mock_default_data_loader.side_effect = Exception('connection error')

        result = FlowUtils.sync_samples_to_portal_by_ids(
            eds=mock_eds, ids=[], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds
        )

        assert result == []


class TestFlowUtilsCreateBenchlingEntitiesFromElasticSamples:

    @pytest.fixture
    def mock_tissue_converter(self):
        with patch('tol.flows.flow_utils.ElasticSampleToBenchlingTissueConverter') as m:
            yield m

    def test_ids_loader_source_and_destination(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=['s-1'], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['source'] is mock_eds
        assert kwargs['destination'] is mock_bds

    def test_ids_loader_object_types(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['source_object_type'] == 'sample'
        assert kwargs['destination_object_type'] == 'tissue'

    def test_ids_loader_passes_ids(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=['s-1', 's-2'], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['object_ids'] == ['s-1', 's-2']

    def test_ids_loader_load_called_with_insert_and_no_auto_exhaust(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        mock_ids_data_loader.return_value.load.assert_called_once_with(
            method='insert', auto_exhaust=False
        )

    def test_converter_config_passes_additional_fields(
        self, mock_ids_data_loader, mock_objects_data_loader, mock_tissue_converter,
        mock_eds, mock_bds, mock_sts_ds
    ):
        extra = {'custom_field': 'value'}
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds,
            additional_fields=extra
        )

        mock_tissue_converter.Config.assert_called_once_with(extra_attributes=extra)

    def test_converter_uses_empty_additional_fields_by_default(
        self, mock_ids_data_loader, mock_objects_data_loader, mock_tissue_converter,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        mock_tissue_converter.Config.assert_called_once_with(extra_attributes={})

    def test_objects_loader_destination_is_sts_ds(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['destination'] is mock_sts_ds

    def test_objects_loader_object_types(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['source_object_type'] == 'tissue'
        assert kwargs['destination_object_type'] == 'sample'

    def test_objects_loader_uses_benchling_tissue_to_sts_converter(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        from tol.flows.converters import BenchlingTissueToStsSampleConverter

        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, kwargs = mock_objects_data_loader.call_args
        assert kwargs['convert_class'] is BenchlingTissueToStsSampleConverter

    def test_objects_loader_load_called_without_auto_exhaust(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        mock_objects_data_loader.return_value.load.assert_called_once_with(auto_exhaust=False)

    def test_objects_loader_receives_ids_loader_output_as_objects(
        self, mock_ids_data_loader, mock_objects_data_loader,
        mock_eds, mock_bds, mock_sts_ds
    ):
        FlowUtils.create_benchling_entities_from_elastic_samples(
            ids=[], eds=mock_eds, bds=mock_bds, sts_ds=mock_sts_ds
        )

        _, objects_kwargs = mock_objects_data_loader.call_args
        # The objects passed to the second loader must derive from the first loader's output
        assert objects_kwargs['objects'] is not None


class TestFlowUtilsLoadEntitiesOntoWorklist:

    @pytest.fixture
    def mock_worklist_converter(self):
        with patch('tol.flows.flow_utils.ElasticObjectToBenchlingWorklistItemConverter') as m:
            yield m

    @pytest.fixture
    def worklist(self):
        return MagicMock()

    def test_ids_loader_source_and_destination(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=['id-1'], object_type='sample', worklist=worklist
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['source'] is mock_eds
        assert kwargs['destination'] is mock_bds

    def test_ids_loader_object_types(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=[], object_type='extraction', worklist=worklist
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['source_object_type'] == 'extraction'
        assert kwargs['destination_object_type'] == 'worklist_item'

    def test_ids_loader_passes_ids(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=['id-1', 'id-2'],
            object_type='sample', worklist=worklist
        )

        _, kwargs = mock_ids_data_loader.call_args
        assert kwargs['object_ids'] == ['id-1', 'id-2']

    def test_converter_config_passes_object_type_and_worklist(
        self, mock_ids_data_loader, mock_worklist_converter, mock_eds, mock_bds, worklist
    ):
        FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=[], object_type='sample', worklist=worklist
        )

        mock_worklist_converter.Config.assert_called_once_with(
            object_type='sample',
            worklist=worklist,
        )
        mock_worklist_converter.assert_called_once_with(
            data_object_factory=mock_bds.data_object_factory,
            config=mock_worklist_converter.Config.return_value,
        )

    def test_load_called_with_insert_and_no_auto_exhaust(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=[], object_type='sample', worklist=worklist
        )

        mock_ids_data_loader.return_value.load.assert_called_once_with(
            method='insert', auto_exhaust=False
        )

    def test_returns_iterable_of_loaded_objects(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        sentinel = iter([MagicMock()])
        mock_ids_data_loader.return_value.load.return_value = sentinel

        result = FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=[], object_type='sample', worklist=worklist
        )

        assert result is not None

    def test_returns_empty_list_on_exception(
        self, mock_ids_data_loader, mock_eds, mock_bds, worklist
    ):
        mock_ids_data_loader.side_effect = Exception('connection error')

        result = FlowUtils.load_entities_onto_worklist(
            eds=mock_eds, bds=mock_bds, ids=[], object_type='sample', worklist=worklist
        )

        assert result == []


class TestFlowUtilsGetSectionFilter:

    def test_returns_expected_filters_for_all_sections(self):
        destination_id = 'cfg-1'
        result = FlowUtils.get_section_filters(destination_id)

        assert result == {
            '1': {
                'loader.candidate_key': {'exists': {'negate': True}},
                'loader.ids_attribute': {'exists': {'negate': True}},
                'ids_data_source_instance.id': {'exists': {'negate': True}},
                'destination_data_source_instance.id': {'eq': {'value': destination_id}},
            },
            '2': {
                'loader.candidate_key': {'exists': {'negate': True}},
                'ids_data_source_instance.id': {
                    'exists': {},
                    'eq': {'value': destination_id, 'negate': True},
                },
                'destination_data_source_instance.id': {'eq': {'value': destination_id}},
            },
            '3': {
                'loader.candidate_key': {'exists': {'negate': True}},
                'ids_data_source_instance.id': {'eq': {'value': destination_id}},
                'destination_data_source_instance.id': {'eq': {'value': destination_id}},
            },
            '4': {
                'loader.candidate_key': {'exists': {'negate': True}},
                'source_data_source_instance.id': {'eq': {'value': destination_id}},
                'destination_data_source_instance.id': {'eq': {'value': destination_id}},
            },
            '5': {
                'loader.candidate_key': {'exists': {}},
                'destination_data_source_instance.id': {'eq': {'value': destination_id}},
            },
        }

    def test_raises_for_invalid_section(self):
        with pytest.raises(ValueError, match='Invalid section: 99'):
            FlowUtils.get_filter_for_section('99', 'cfg-1')


class TestFlowUtilsPerformTopupAction:

    @pytest.fixture
    def mock_create_benchling_entities(self):
        with patch(
            'tol.flows.flow_utils.FlowUtils.create_benchling_entities_from_elastic_samples'
        ) as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_sync_samples_to_portal(self):
        with patch('tol.flows.flow_utils.FlowUtils.sync_samples_to_portal_by_ids') as m:
            yield m

    @pytest.fixture
    def mock_load_entities_onto_worklist(self):
        with patch('tol.flows.flow_utils.FlowUtils.load_entities_onto_worklist') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_record_tolid_events(self):
        with patch('tol.flows.flow_utils.FlowUtils.record_tolid_events') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_record_actioned_events(self):
        with patch('tol.flows.flow_utils.FlowUtils.record_actioned_events') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_record_review_events(self):
        with patch('tol.flows.flow_utils.FlowUtils.record_review_events') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_record_abandoned_events(self):
        with patch('tol.flows.flow_utils.FlowUtils.record_abandoned_events') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_record_species_events(self):
        with patch('tol.flows.flow_utils.FlowUtils.record_species_events') as m:
            m.return_value = []
            yield m

    @pytest.fixture
    def mock_sync_summarise_enrich(self):
        with patch('tol.flows.flow_utils.FlowUtils.sync_summarise_enrich') as m:
            yield m

    @pytest.fixture
    def worklist(self):
        return MagicMock()

    @pytest.fixture
    def an_error(self):
        return ErrorObject(details={'message': 'something failed'}, object_type='sample')

    def _call(
        self,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
        ids=None, object_type='sample', action='tum',
        user_id='user-1', user_name='Test User',
        recollection_reason=None,
    ):
        return list(FlowUtils.perform_topup_action(
            eds=mock_eds,
            bds=mock_bds,
            ids=ids if ids is not None else ['id-1'],
            sts_ds=mock_sts_ds,
            portaldb_ds=mock_portaldb_ds,
            data_source_instance=data_source_instance,
            object_type=object_type,
            worklist=worklist,
            action=action,
            user_id=user_id,
            user_name=user_name,
            recollection_reason=recollection_reason,
            sleep_time=0,
        ))

    def test_returns_empty_when_ids_empty(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, ids=[],
        )

        assert result == []
        mock_create_benchling_entities.assert_not_called()
        mock_load_entities_onto_worklist.assert_not_called()
        mock_sync_summarise_enrich.assert_not_called()

    def test_benchling_creation_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_create_benchling_entities.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, object_type='sample',
        )

        assert an_error in result

    def test_benchling_creation_non_errors_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_create_benchling_entities.return_value = [MagicMock(), MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, object_type='sample',
        )

        assert result == []

    def test_sync_samples_called_for_sample_type(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, object_type='sample',
        )

        mock_sync_samples_to_portal.assert_called_once_with(
            eds=mock_eds, ids=['id-1'], sts_ds=mock_sts_ds, portaldb_ds=mock_portaldb_ds,
        )

    def test_benchling_creation_skipped_for_non_sample_type(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, object_type='extraction',
        )

        mock_create_benchling_entities.assert_not_called()
        mock_sync_samples_to_portal.assert_not_called()

    def test_worklist_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_load_entities_onto_worklist.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist,
        )

        assert an_error in result

    def test_worklist_non_errors_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_load_entities_onto_worklist.return_value = [MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist,
        )

        assert result == []

    def test_worklist_step_skipped_when_none(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance,
    ):
        self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist=None,
        )

        mock_load_entities_onto_worklist.assert_not_called()

    def test_tum_tolid_event_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_record_tolid_events.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='tum',
        )

        assert an_error in result

    def test_tum_actioned_event_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_record_actioned_events.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='tum',
        )

        assert an_error in result

    def test_tum_non_errors_from_events_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_record_tolid_events.return_value = [MagicMock()]
        mock_record_actioned_events.return_value = [MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='tum', object_type='extraction',
        )

        assert result == []

    def test_tum_sync_summarise_enrich_called_twice(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='tum', object_type='extraction',
        )

        assert mock_sync_summarise_enrich.call_count == 2
        types_synced = [c.kwargs['object_type'] for c in mock_sync_summarise_enrich.call_args_list]
        assert 'tolid' in types_synced
        assert 'extraction' in types_synced

    def test_in_ara_review_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_review_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_record_review_events.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='in_ara_review', object_type='extraction',
        )

        assert an_error in result

    def test_out_of_ara_review_passes_in_review_false(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_review_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='out_of_ara_review', object_type='extraction',
        )

        mock_record_review_events.assert_called_once()
        assert mock_record_review_events.call_args.kwargs['in_review'] is False

    def test_review_non_errors_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_review_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_record_review_events.return_value = [MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='in_ara_review', object_type='extraction',
        )

        assert result == []

    def test_abandon_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_abandoned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_record_abandoned_events.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='abandon', object_type='extraction',
        )

        assert an_error in result

    def test_abandon_non_errors_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_abandoned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_record_abandoned_events.return_value = [MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='abandon', object_type='extraction',
        )

        assert result == []

    def test_recollect_errors_propagated(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_species_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist, an_error,
    ):
        mock_record_species_events.return_value = [an_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='recollect', object_type='sample',
        )

        assert an_error in result

    def test_recollect_non_errors_filtered_out(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_species_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        mock_record_species_events.return_value = [MagicMock()]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist, action='recollect', object_type='sample',
        )

        assert result == []

    def test_errors_collected_from_all_stages(
        self,
        mock_create_benchling_entities, mock_sync_samples_to_portal,
        mock_load_entities_onto_worklist, mock_sync_summarise_enrich,
        mock_record_tolid_events, mock_record_actioned_events,
        mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
        data_source_instance, worklist,
    ):
        benchling_error = ErrorObject(details={}, object_type='sample', error_id='e-benchling')
        worklist_error = ErrorObject(details={}, object_type='sample', error_id='e-worklist')
        tolid_error = ErrorObject(details={}, object_type='sample', error_id='e-tolid')
        actioned_error = ErrorObject(details={}, object_type='sample', error_id='e-actioned')

        mock_create_benchling_entities.return_value = [benchling_error]
        mock_load_entities_onto_worklist.return_value = [worklist_error]
        mock_record_tolid_events.return_value = [tolid_error]
        mock_record_actioned_events.return_value = [actioned_error]

        result = self._call(
            mock_eds, mock_bds, mock_sts_ds, mock_portaldb_ds,
            data_source_instance, worklist,
            object_type='sample', action='tum',
        )

        assert benchling_error in result
        assert worklist_error in result
        assert tolid_error in result
        assert actioned_error in result
        assert len(result) == 4
