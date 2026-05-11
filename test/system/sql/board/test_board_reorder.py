# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataSourceFilter
from tol.sql import SqlDataSource

from .utils import insert_board_hierarchy


class TestBoardReorder:
    """
    `board_blueprint` reorder endpoint against a real database.
    """

    def test__reorder__200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Reordering zones within a view with a valid new order -> 200
        and order values updated in the DB.
        """

        hierarchy = {
            'zone': {
                'a': ('100', []),
                'b': ('100', []),
                'c': ('100', []),
            },
            'view': {
                'I': ('100', ['a', 'b', 'c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        r = board_client.patch(
            '/reorder/I',
            json={'order': ['c', 'a', 'b']}
        )
        assert r.status_code == 200
        assert r.json['order'] == ['c', 'a', 'b']

        # Verify the order values in the DB
        joiner_objs = list(board_ds.get_list(
            'zone_view',
            object_filters=DataSourceFilter(
                and_={'view.id': {'eq': {'value': 'I'}}}
            )
        ))
        order_by_zone_id = {
            obj.zone.id: obj.order
            for obj in joiner_objs
        }
        assert order_by_zone_id['c'] == 0
        assert order_by_zone_id['a'] == 1
        assert order_by_zone_id['b'] == 2

    def test__reorder__missing_child__400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Reordering with a missing child ID -> 400.
        """

        hierarchy = {
            'zone': {
                'a': ('100', []),
                'b': ('100', []),
                'c': ('100', []),
            },
            'view': {
                'I': ('100', ['a', 'b', 'c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        # 'c' is missing
        r = board_client.patch(
            '/reorder/I',
            json={'order': ['a', 'b']}
        )
        assert r.status_code == 400

    def test__reorder__extra_child__400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Reordering with an ID that doesn't belong to the parent -> 400.
        """

        hierarchy = {
            'zone': {
                'a': ('100', []),
                'b': ('100', []),
                'c': ('100', []),
                'd': ('100', []),
            },
            'view': {
                'I': ('100', ['a', 'b', 'c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        # 'd' is not a child of 'I'
        r = board_client.patch(
            '/reorder/I',
            json={'order': ['a', 'b', 'c', 'd']}
        )
        assert r.status_code == 400

    def test__reorder__same_order__200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Reordering with the same order as currently in the DB -> 200,
        no change.
        """

        hierarchy = {
            'zone': {
                'a': ('100', []),
                'b': ('100', []),
            },
            'view': {
                'I': ('100', ['a', 'b'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        r = board_client.patch(
            '/reorder/I',
            json={'order': ['a', 'b']}
        )
        assert r.status_code == 200
