# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import pytest

from tol.core import DataSource, DataSourceFilter, core_data_object
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
