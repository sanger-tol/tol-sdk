# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataSourceError
from tol.sql import SqlDataSource

from .utils import insert_board_hierarchy


class TestBoardDelete:
    """
    `board_blueprint` against a real database.
    """

    def test__middle_type(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Deleting a `middle` row unlinks above (e.g. deletes `zone_view`
        entry), if there is only one.
        """

        hierarchy = {
            'component': {
                'c_1': ('100', []),
            },
            'zone': {
                'z_a': ('100', ['c_1'])
            },
            'view': {
                'v_I': ('100', ['z_a'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        r = board_client.delete(
            '/z_a'
        )
        assert r.status_code == 200

        assert board_ds.get_count('zone') == 0
        assert board_ds.get_count('component_zone') == 0
        assert board_ds.get_count('component') == 0

        # unlinked
        assert board_ds.get_count('zone_view') == 0

        # upstream not deleted
        assert board_ds.get_count('view') == 1

    def test__middle_type__different_owner_upstream_fail(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Deleting a middle row, where its sole upstream
        link (e.g. a `view` for a `zone`) belongs to
        another user -> `DataSourceError` and HTTP 400
        """

        hierarchy = {
            'component': {
                'c_1': ('100', []),
            },
            'zone': {
                'z_a': ('100', ['c_1'])
            },
            'view': {
                # someone else owns this view
                'v_I': ('303', ['z_a'])
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100', '303'])

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.delete(
                '/z_a'
            )
        assert e.value.status_code == 400

    def test__middle_type__multiple_upstream_fail(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        type_hierarchy: list[str]
    ):
        """
        Deleting a `middle` row with multiple upstream links
        (e.g. a `zone` with multiple `zone_view` rows pointing to it)
        fails with a `DataSourceError`.
        """

        hierarchy = {
            'component': {
                'c_1': ('100', []),
            },
            'zone': {
                'z_a': ('100', ['c_1'])
            },
            'view': {
                # four views point to the above zone, and
                # all belong to user `100`
                'v_I': ('100', ['z_a']),
                'v_II': ('100', ['z_a']),
                'v_III': ('100', ['z_a']),
                'v_IV': ('100', ['z_a']),
            }
        }

        insert_board_hierarchy(board_ds, hierarchy, type_hierarchy, ['100'])

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.delete(
                '/z_a'
            )
        assert e.value.status_code == 400
