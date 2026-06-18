# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest

from tol.action.action_utils import ActionUtils
from tol.core import DataSourceError


def _make_action(class_name: str) -> MagicMock:
    action = MagicMock()
    action.class_name = class_name
    action.params = {'action_param': 'value_from_action'}
    return action


def _make_action_class(run_return=({'success': True}, 200)):
    """Return a mock action class whose instance.run() returns run_return."""
    instance = MagicMock()
    instance.run.return_value = run_return
    action_class = MagicMock(return_value=instance)
    return action_class, instance


class TestActionUtilsRunActionSuccess:

    def test_returns_action_run_result(self):
        action_class, instance = _make_action_class(({'success': True}, 200))

        tol_module = MagicMock()
        tol_module.MyAction = action_class

        with patch('importlib.import_module', return_value=tol_module):
            result = ActionUtils.run_action(
                action=_make_action('MyAction'),
                params={},
                user_id='u-1',
                ids=['id-1'],
                object_type='sample',
            )

        assert result == ({'success': True}, 200)

    def test_passes_ids_object_type_and_datasource_to_run(self):
        action_class, instance = _make_action_class()
        tol_module = MagicMock()
        tol_module.MyAction = action_class
        ds = MagicMock()

        with patch('importlib.import_module', return_value=tol_module):
            ActionUtils.run_action(
                action=_make_action('MyAction'),
                params={},
                user_id='u-1',
                ids=['id-1', 'id-2'],
                object_type='extraction',
                action_ds=ds,
            )

        instance.run.assert_called_once_with(
            ids=['id-1', 'id-2'],
            params={'user_id': 'u-1', 'action_param': 'value_from_action'},
            object_type='extraction',
            datasource=ds,
        )

    def test_user_id_merged_into_params(self):
        action_class, instance = _make_action_class()
        tol_module = MagicMock()
        tol_module.MyAction = action_class

        with patch('importlib.import_module', return_value=tol_module):
            ActionUtils.run_action(
                action=_make_action('MyAction'),
                params={'a': 1},
                user_id='u-99',
                ids=['id-1'],
                object_type='sample',
            )

        _, call_kwargs = instance.run.call_args
        assert call_kwargs['params']['user_id'] == 'u-99'

    def test_action_params_and_params_merged(self):
        action_class, instance = _make_action_class()
        tol_module = MagicMock()
        tol_module.MyAction = action_class

        with patch('importlib.import_module', return_value=tol_module):
            ActionUtils.run_action(
                action=_make_action('MyAction'),
                params={'key_from_action': 'val_a', 'key_from_params': 'val_b'},
                user_id='u-1',
                ids=['id-1'],
                object_type='sample',
            )

        _, call_kwargs = instance.run.call_args
        merged = call_kwargs['params']
        assert merged['key_from_action'] == 'val_a'
        assert merged['key_from_params'] == 'val_b'

    def test_action_ds_defaults_to_none(self):
        action_class, instance = _make_action_class()
        tol_module = MagicMock()
        tol_module.MyAction = action_class

        with patch('importlib.import_module', return_value=tol_module):
            ActionUtils.run_action(
                action=_make_action('MyAction'),
                params={},
                user_id='u-1',
                ids=['id-1'],
                object_type='sample',
            )

        _, call_kwargs = instance.run.call_args
        assert call_kwargs['datasource'] is None


class TestActionUtilsRunActionErrors:

    def test_raises_404_when_class_not_in_tol_actions(self):
        tol_module = MagicMock(spec=[])  # no attributes at all

        with patch('importlib.import_module', return_value=tol_module):
            with pytest.raises(DataSourceError) as exc_info:
                ActionUtils.run_action(
                    action=_make_action('NonExistentAction'),
                    params={},
                    user_id='u-1',
                    ids=['id-1'],
                    object_type='sample',
                )

        assert exc_info.value.status_code == 404

    def test_raises_500_on_import_error(self):
        with patch('importlib.import_module', side_effect=ImportError('no module')):
            with pytest.raises(DataSourceError) as exc_info:
                ActionUtils.run_action(
                    action=_make_action('AnyAction'),
                    params={},
                    user_id='u-1',
                    ids=['id-1'],
                    object_type='sample',
                )

        assert exc_info.value.status_code == 500

    def test_404_error_message_includes_class_name(self):
        tol_module = MagicMock(spec=[])

        with patch('importlib.import_module', return_value=tol_module):
            with pytest.raises(DataSourceError) as exc_info:
                ActionUtils.run_action(
                    action=_make_action('MissingAction'),
                    params={},
                    user_id='u-1',
                    ids=['id-1'],
                    object_type='sample',
                )

        assert 'MissingAction' in exc_info.value.detail
