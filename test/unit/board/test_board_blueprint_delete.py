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

        mock_small = mock_board_obj('S', 'delete_me', user_id='100')
        board_ds.get_one.side_effect = lambda *_: mock_small
        board_ds.get_count.return_value = 0

        r = board_client.delete('/S/delete_me')
        assert r.status_code == 200

        board_ds.delete.assert_called_once_with('S', ['delete_me'])

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

        mock_small = mock_board_obj('S', 'delete_me', user_id='no_match')
        board_ds.get_one.return_value = mock_small

        with pytest.raises(ForbiddenError):
            board_client.delete('/S/delete_me')

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
            'S': {
                '1': ('100', []),
                '2': ('100', []),
                '3': ('100', [])
            },
            'M': {
                'a': ('100', ['1', '3']),
                'b': ('100', ['2', '3'])
            },
            'L': {
                'I': ('100', ['a', 'b'])
            }
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.side_effect = mock_board_get_count(objs)

        r = board_client.delete('/L/I')
        assert r.status_code == 200

        observed_deletes = self.__format_type_deletes(board_ds)
        assert observed_deletes['S'] == {'1', '2', '3'}
        assert observed_deletes['M'] == {'a', 'b'}
        assert observed_deletes['L'] == {'I'}
        assert len(observed_deletes['S_M']) == 4
        assert len(observed_deletes['M_L']) == 2

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

        # "small" with ID's 2 and 3 must not be deleted. Only 1
        hierarchy = {
            'S': {
                # fine to delete
                '1': ('100', []),
                # no delete - owned by another user
                '2': ('someone_else', []),
                # no delete - other "higher" types depend on it
                '3': ('100', [])
            },
            'M': {
                'a': ('100', ['1', '3']),
                'b': ('someone_else', ['2', '3'])
            },
            'L': {
                'I': ('100', ['a', 'b'])
            }
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.side_effect = mock_board_get_count(objs)

        r = board_client.delete('/L/I')
        assert r.status_code == 200

        observed_deletes = self.__format_type_deletes(board_ds)
        assert observed_deletes['S'] == {'1'}
        assert observed_deletes['M'] == {'a'}
        assert observed_deletes['L'] == {'I'}
        assert len(observed_deletes['S_M']) == 2  # a->1, a->3
        assert len(observed_deletes['M_L']) == 2  # I->a, I->b

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
