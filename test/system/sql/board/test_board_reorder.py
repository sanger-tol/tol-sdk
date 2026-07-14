# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataSourceError, DataSourceFilter
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
                'z_a': ('100', []),
                'z_b': ('100', []),
                'z_c': ('100', []),
            },
            'view': {
                'v_I': ('100', ['z_a', 'z_b', 'z_c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        r = board_client.patch(
            '/reorder/v_I',
            json={'order': ['z_c', 'z_a', 'z_b']}
        )
        assert r.status_code == 200
        assert r.json['order'] == ['z_c', 'z_a', 'z_b']

        # Verify the order values in the DB
        joiner_objs = list(board_ds.get_list(
            'zone_view',
            object_filters=DataSourceFilter(
                and_={'view.id': {'eq': {'value': 'v_I'}}}
            )
        ))
        order_by_zone_id = {
            obj.zone.id: obj.order
            for obj in joiner_objs
        }
        assert order_by_zone_id['z_c'] == 0
        assert order_by_zone_id['z_a'] == 1
        assert order_by_zone_id['z_b'] == 2

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
                'z_a': ('100', []),
                'z_b': ('100', []),
                'z_c': ('100', []),
            },
            'view': {
                'v_I': ('100', ['z_a', 'z_b', 'z_c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        # 'z_c' is missing
        with pytest.raises(DataSourceError):
            board_client.patch(
                '/reorder/v_I',
                json={'order': ['z_a', 'z_b']}
            )

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
                'z_a': ('100', []),
                'z_b': ('100', []),
                'z_c': ('100', []),
                'z_d': ('100', []),
            },
            'view': {
                'v_I': ('100', ['z_a', 'z_b', 'z_c'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        # 'z_d' is not a child of 'v_I'
        with pytest.raises(DataSourceError):
            board_client.patch(
                '/reorder/v_I',
                json={'order': ['z_a', 'z_b', 'z_c', 'z_d']}
            )

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
                'z_a': ('100', []),
                'z_b': ('100', []),
            },
            'view': {
                'v_I': ('100', ['z_a', 'z_b'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        r = board_client.patch(
            '/reorder/v_I',
            json={'order': ['z_a', 'z_b']}
        )
        assert r.status_code == 200
