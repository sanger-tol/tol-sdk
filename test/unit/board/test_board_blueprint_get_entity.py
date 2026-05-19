# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataSourceError
from tol.sql import SqlDataSource

from .utils import (
    mock_board_get_list,
    mock_board_get_one,
    mock_board_hierarchy,
    mock_board_obj,
)


class TestBoardBlueprintGetEntity:

    def test_get_entity__200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        GET a single zone entity with no children -> 200 and correct response body.
        """

        board_auth_ctx.user_id = '100'

        zone = mock_board_obj('zone', 'z_abc', attributes={'title': 'My Zone'}, user_id='100')
        board_ds.get_one.return_value = zone
        board_ds.get_list.return_value = []

        r = board_client.get('/get-entity/z_abc')
        assert r.status_code == 200

        payload = r.get_json()
        assert payload['id'] == 'z_abc'
        assert payload['type'] == 'zone'
        assert payload['title'] == 'My Zone'
        assert payload['order'] == []
        assert payload['children'] == {}

    def test_get_entity__404(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        GET a non-existent entity -> 404 DataSourceError raised.
        """

        board_auth_ctx.user_id = '100'

        board_ds.get_one.return_value = None

        with pytest.raises(DataSourceError) as e:
            board_client.get('/get-entity/z_missing')

        assert e.value.title == 'Not Found'
        assert e.value.status_code == 404

    def test_get_entity__board_and_children_200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str],
    ):
        """
        GET a board entity -> 200, response includes all nested views and their zones.
        """

        board_auth_ctx.user_id = '100'

        hierarchy = {
            'zone': {
                'z_1': ('100', []),
                'z_2': ('100', []),
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_2']),
            },
            'board': {
                'b_I': ('100', ['v_a']),
            },
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)

        r = board_client.get('/get-entity/b_I')
        assert r.status_code == 200

        payload = r.get_json()
        assert payload['id'] == 'b_I'
        assert payload['type'] == 'board'
        assert 'v_a' in payload['order']

        view_data = payload['children']['v_a']
        assert view_data['type'] == 'view'
        assert set(view_data['order']) == {'z_1', 'z_2'}

    def test_get_entity__zone_and_children_200(
        self,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str],
    ):
        """
        GET a zone entity -> 200, response includes nested components.

        No user authenticated so the board_diff lookup for components is skipped.
        """

        hierarchy = {
            'component': {
                'c_1': ('100', []),
                'c_2': ('100', []),
            },
            'zone': {
                'z_a': ('100', ['c_1', 'c_2']),
            },
            'view': {},
            'board': {},
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)

        r = board_client.get('/get-entity/z_a')
        assert r.status_code == 200

        payload = r.get_json()
        assert payload['id'] == 'z_a'
        assert payload['type'] == 'zone'
        assert set(payload['order']) == {'c_1', 'c_2'}
        assert 'c_1' in payload['children']
        assert 'c_2' in payload['children']
