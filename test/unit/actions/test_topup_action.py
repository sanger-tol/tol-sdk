# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from tol.action.actions.topup_action import TopupAction
from tol.core import DataSourceError


@pytest.fixture
def action():
    return TopupAction()


@pytest.fixture
def mock_portaldb_ds():
    ds = MagicMock()
    ds.get_one.return_value = MagicMock()  # data_source_instance
    return ds


@pytest.fixture
def mock_eds():
    return MagicMock()


@pytest.fixture
def mock_sts_ds():
    return MagicMock()


@pytest.fixture
def mock_benchling_superuser():
    return MagicMock()


@pytest.fixture
def mock_benchling_user_bds():
    return MagicMock()


@pytest.fixture
def mock_folder():
    folder = MagicMock()
    folder.id = 'folder-1'
    return folder


@pytest.fixture
def mock_worklist():
    wl = MagicMock()
    wl.name = 'My Worklist'
    return wl


def _patch_all(
    *,
    portaldb_ds,
    eds,
    sts_ds,
    benchling_superuser,
    benchling_user_bds,
    user_name='Test User',
    api_key='key-1',
    folder=None,
    worklist=None,
    perform_errors=None,
):
    """Return a context-manager stack that wires up all external dependencies."""
    perform_errors = perform_errors or []
    return [
        patch('tol.action.actions.topup_action.portaldb', return_value=portaldb_ds),
        patch('tol.action.actions.topup_action.sts', return_value=sts_ds),
        patch(
            'tol.action.actions.topup_action.benchling',
            side_effect=[benchling_superuser, benchling_user_bds]
        ),
        patch(
            'tol.action.actions.topup_action.DataSourceUtils'
            '.get_datasource_by_datasource_instance',
            return_value=eds,
        ),
        patch(
            'tol.action.actions.topup_action.FlowUtils.get_user_name_and_eln_api_key',
            return_value=(user_name, api_key),
        ),
        patch('tol.action.actions.topup_action.FlowUtils.get_folder', return_value=folder),
        patch('tol.action.actions.topup_action.FlowUtils.get_worklist', return_value=worklist),
        patch(
            'tol.action.actions.topup_action.FlowUtils.perform_topup_action',
            return_value=iter(perform_errors),
        ),
    ]


class TestTopupActionValidation:

    def test_raises_when_params_missing(self, action, mock_portaldb_ds):
        with pytest.raises(DataSourceError) as exc_info:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params=None,
            )
        assert exc_info.value.status_code == 400

    def test_raises_when_action_not_in_params(self, action):
        with pytest.raises(DataSourceError) as exc_info:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'user_id': 'u-1'},
            )
        assert exc_info.value.status_code == 400

    def test_raises_when_ids_is_none(self, action):
        with pytest.raises(DataSourceError) as exc_info:
            action.run(
                datasource=MagicMock(),
                ids=None,
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1'},
            )
        assert exc_info.value.status_code == 400

    def test_raises_when_ids_is_empty(self, action):
        with pytest.raises(DataSourceError) as exc_info:
            action.run(
                datasource=MagicMock(),
                ids=[],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1'},
            )
        assert exc_info.value.status_code == 400

    def test_raises_when_user_id_missing(self, action):
        with pytest.raises(DataSourceError) as exc_info:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum'},
            )
        assert exc_info.value.status_code == 400


class TestTopupActionSuccess:

    def _run(
        self,
        action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
        **kwargs,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
            **kwargs,
        )
        with patches[0], patches[1], patches[2], patches[3], \
                patches[4], patches[5], patches[6], patches[7]:
            return action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1'},
            )

    def test_returns_200_on_success(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        result, status = self._run(
            action,
            mock_portaldb_ds, mock_eds, mock_sts_ds,
            mock_benchling_superuser, mock_benchling_user_bds,
        )
        assert status == 200
        assert result == {'success': True}

    def test_returns_500_when_perform_topup_yields_errors(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        error = MagicMock()
        error.__str__ = lambda self: 'something went wrong'

        result, status = self._run(
            action,
            mock_portaldb_ds, mock_eds, mock_sts_ds,
            mock_benchling_superuser, mock_benchling_user_bds,
            perform_errors=[error],
        )
        assert status == 500
        assert 'error' in result
        assert 'something went wrong' in result['error']

    def test_fetches_data_source_instance_from_portaldb(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        self._run(
            action,
            mock_portaldb_ds, mock_eds, mock_sts_ds,
            mock_benchling_superuser, mock_benchling_user_bds,
        )
        mock_portaldb_ds.get_one.assert_called_once_with('data_source_instance', 'tol_production')

    def test_passes_user_id_to_get_user_name_and_eln_api_key(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4] \
                as mock_get_user, patches[5], patches[6], patches[7]:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-99'},
            )

        mock_get_user.assert_called_once_with(
            portaldb_ds=mock_portaldb_ds,
            sts_ds=mock_sts_ds,
            portal_user_id='u-99',
        )

    def test_folder_id_passed_to_user_benchling_when_folder_found(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds, mock_folder,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
            folder=mock_folder,
        )
        with patches[0], patches[1], patches[2] as mock_benchling_factory, \
                patches[3], patches[4], patches[5], patches[6], patches[7]:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1', 'folder_name': 'My Folder'},
            )

        # Second call to benchling() is the user bds — should receive folder_id
        second_call_kwargs = mock_benchling_factory.call_args_list[1].kwargs
        assert second_call_kwargs.get('folder_id') == 'folder-1'

    def test_folder_id_is_none_when_no_folder_found(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
            folder=None,
        )
        with patches[0], patches[1], patches[2] as mock_benchling_factory, patches[3], \
                patches[4], patches[5], patches[6], patches[7]:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1'},
            )

        second_call_kwargs = mock_benchling_factory.call_args_list[1].kwargs
        assert second_call_kwargs.get('folder_id') is None

    def test_perform_topup_action_called_with_correct_args(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds, mock_worklist,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
            user_name='Alice',
            worklist=mock_worklist,
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
                patches[7] as mock_perform:
            action.run(
                datasource=MagicMock(),
                ids=['id-1', 'id-2'],
                object_type='extraction',
                params={
                    'action': 'abandon',
                    'user_id': 'u-1',
                    'recollection_reason': 'damaged',
                },
            )

        mock_perform.assert_called_once()
        kwargs = mock_perform.call_args.kwargs
        assert kwargs['ids'] == ['id-1', 'id-2']
        assert kwargs['object_type'] == 'extraction'
        assert kwargs['action'] == 'abandon'
        assert kwargs['user_id'] == 'u-1'
        assert kwargs['user_name'] == 'Alice'
        assert kwargs['recollection_reason'] == 'damaged'
        assert kwargs['worklist'] is mock_worklist
        assert kwargs['eds'] is mock_eds
        assert kwargs['sts_ds'] is mock_sts_ds
        assert kwargs['portaldb_ds'] is mock_portaldb_ds
        assert kwargs['bds'] is mock_benchling_user_bds

    def test_worklist_name_looked_up_via_superuser_benchling(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        patches = _patch_all(
            portaldb_ds=mock_portaldb_ds,
            eds=mock_eds,
            sts_ds=mock_sts_ds,
            benchling_superuser=mock_benchling_superuser,
            benchling_user_bds=mock_benchling_user_bds,
        )
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
                patches[6] as mock_get_worklist, patches[7]:
            action.run(
                datasource=MagicMock(),
                ids=['id-1'],
                object_type='sample',
                params={'action': 'tum', 'user_id': 'u-1', 'worklist_name': 'WL-1'},
            )

        mock_get_worklist.assert_called_once_with(
            bds=mock_benchling_superuser,
            worklist_name='WL-1',
        )

    def test_multiple_errors_concatenated_in_response(
        self, action,
        mock_portaldb_ds, mock_eds, mock_sts_ds,
        mock_benchling_superuser, mock_benchling_user_bds,
    ):
        e1, e2 = MagicMock(), MagicMock()
        e1.__str__ = lambda self: 'error one'
        e2.__str__ = lambda self: 'error two'

        result, status = self._run(
            action,
            mock_portaldb_ds, mock_eds, mock_sts_ds,
            mock_benchling_superuser, mock_benchling_user_bds,
            perform_errors=[e1, e2],
        )

        assert status == 500
        assert 'error one' in result['error']
        assert 'error two' in result['error']
