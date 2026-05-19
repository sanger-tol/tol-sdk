# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import reduce
from unittest.mock import _Call

from flask.testing import FlaskClient

import pytest

from tol.api_base.auth import ForbiddenError
from tol.api_base.misc import AuthContext
from tol.sql import SqlDataSource

from .utils import (
    mock_board_get_count,
    mock_board_get_list,
    mock_board_get_one,
    mock_board_hierarchy,
    mock_board_obj,
)


class TestBoardBlueprintDelete:

    def test_delete_smallest__200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        DELETE smallest where user_id matches -> success
        """

        board_auth_ctx.user_id = '100'

        mock_small = mock_board_obj('zone', 'z_delete_me', user_id='100')
        board_ds.get_one.side_effect = lambda *_: mock_small
        board_ds.get_list.return_value = []
        board_ds.get_count.return_value = 0

        r = board_client.delete('/z_delete_me', json={})
        assert r.status_code == 200

        board_ds.delete.assert_any_call('zone', ['z_delete_me'])

    def test_delete_smallest__403(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource
    ):
        """
        DELETE smallest where user_id doesn't match
        -> failure (403)
        """

        board_auth_ctx.user_id = '100'

        mock_small = mock_board_obj('zone', 'z_delete_me', user_id='no_match')
        board_ds.get_one.return_value = mock_small

        with pytest.raises(ForbiddenError):
            board_client.delete('/z_delete_me', json={})

    def test_delete_biggest__total(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        DELETE biggest where:

        - all recursive children are owned by the user
        - none are used elsewhere (by other users)

        -> everything cascade deletes.
        """

        board_auth_ctx.user_id = '100'

        hierarchy = {
            'zone': {
                'z_1': ('100', []),
                'z_2': ('100', []),
                'z_3': ('100', [])
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_3']),
                'v_b': ('100', ['z_2', 'z_3'])
            },
            'board': {
                'b_I': ('100', ['v_a', 'v_b'])
            }
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.side_effect = mock_board_get_count(objs)

        r = board_client.delete('/b_I', json={})
        assert r.status_code == 200

        observed_deletes = self.__format_type_deletes(board_ds)
        assert observed_deletes['view'] == {'v_a', 'v_b'}
        assert observed_deletes['board'] == {'b_I'}
        assert len(observed_deletes['view_board']) == 2

    def test_delete_biggest__partial(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        DELETE biggest where some recursive children are either:

        - not owned by the current user
        - used elsewhere by other users

        -> only recursive children with sole user ownership get
           deleted, up to the point of divergence
        """

        board_auth_ctx.user_id = '100'

        # view 'v_b' and zone 'z_2' must not be deleted
        hierarchy = {
            'zone': {
                'z_1': ('100', []),
                'z_2': ('someone_else', []),
                'z_3': ('100', [])
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_3']),
                'v_b': ('someone_else', ['z_2', 'z_3'])
            },
            'board': {
                'b_I': ('100', ['v_a', 'v_b'])
            }
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.side_effect = mock_board_get_count(objs)

        r = board_client.delete('/b_I', json={})
        assert r.status_code == 200

        observed_deletes = self.__format_type_deletes(board_ds)
        assert observed_deletes['view'] == {'v_a'}
        assert observed_deletes['board'] == {'b_I'}
        assert len(observed_deletes['view_board']) == 2  # all joins under b_I removed

    def __format_type_deletes(
        self,
        board_ds: SqlDataSource
    ) -> dict[str, set[str]]:
        """
        Returns a `dict` mapping object type to its deleted ID's via
        the given `board_ds`.
        """

        call_list = board_ds.delete.call_args_list

        def __effect(
            so_far: dict[str, set[str]],
            element: _Call
        ) -> dict[str, set[str]]:
            object_type, ids = element.args
            current_ids = so_far.get(object_type, {})
            so_far[object_type] = {*current_ids, *ids}
            return so_far

        return reduce(__effect, call_list, {})

    def test_delete__403_unauthenticated(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
    ) -> None:
        """
        DELETE without authentication -> 403 Forbidden.
        """

        with pytest.raises(ForbiddenError) as exc:
            board_client.delete('/z_something', json={})

        assert exc.value.status_code == 403

    def test_delete__200_warden_bypasses_owner_check(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str],
    ) -> None:
        """
        DELETE a zone owned by another user succeeds when the
        requesting user has the 'warden' role.
        """

        board_auth_ctx.user_id = '100'
        board_auth_ctx.roles = ['warden']

        mock_small = mock_board_obj('zone', 'z_delete_me', user_id='other_user')
        board_ds.get_one.return_value = mock_small
        board_ds.get_list.return_value = []

        r = board_client.delete('/z_delete_me', json={})

        assert r.status_code == 200
        assert r.get_json() == {'deleted': True}
