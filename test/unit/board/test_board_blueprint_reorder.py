# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, call

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataSourceError
from tol.sql import SqlDataSource


class TestBoardBlueprintReorder:

    def test_reorder__400_missing_order_payload_field(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH without the required order field -> payload error (400).
        """

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.patch('/reorder/v_I', json={})

        assert e.value.title == 'Payload Error'
        assert e.value.detail == 'You must specify all of: order'
        assert e.value.status_code == 400
        board_ds.get_list.assert_not_called()

    def test_reorder__400_order_must_be_list_of_strings(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH with a malformed order field -> payload error (400).
        """

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.patch('/reorder/v_I', json={'order': ['zone_a', 1]})

        assert e.value.title == 'Bad Request'
        assert e.value.detail == 'The field "order" must be a list of strings.'
        assert e.value.status_code == 400
        board_ds.get_list.assert_not_called()

    def test_reorder__200(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH /reorder/v_I with a valid new order -> 200,
        upsert_batch called with correctly ordered factory objects.
        """

        board_auth_ctx.user_id = '100'

        # v_I (view) has children zone_a, zone_b, zone_c (zones) via zone_view joiners
        joiner_objs = [
            self.__mock_joiner('j0', 'zone_a'),
            self.__mock_joiner('j1', 'zone_b'),
            self.__mock_joiner('j2', 'zone_c'),
        ]
        board_ds.get_list.return_value = joiner_objs

        r = board_client.patch('/reorder/v_I', json={'order': ['zone_c', 'zone_a', 'zone_b']})
        assert r.status_code == 200
        assert r.json['order'] == ['zone_c', 'zone_a', 'zone_b']

        # factory should be called once per child, in new-order sequence
        assert board_ds.data_object_factory.call_args_list == [
            call(type_='zone_view', id_='j2', attributes={'order': 0}),
            call(type_='zone_view', id_='j0', attributes={'order': 1}),
            call(type_='zone_view', id_='j1', attributes={'order': 2}),
        ]

        board_ds.upsert.assert_called_once()
        upsert_type = board_ds.upsert.call_args.args[0]
        assert upsert_type == 'zone_view'

    def test_reorder__missing_child__400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH with a new order missing one child ID -> 400.
        """

        board_auth_ctx.user_id = '100'

        joiner_objs = [
            self.__mock_joiner('j0', 'zone_a'),
            self.__mock_joiner('j1', 'zone_b'),
            self.__mock_joiner('j2', 'zone_c'),
        ]
        board_ds.get_list.return_value = joiner_objs

        # 'zone_c' is missing
        with pytest.raises(DataSourceError):
            board_client.patch('/reorder/v_I', json={'order': ['zone_a', 'zone_b']})

        board_ds.upsert_batch.assert_not_called()

    def test_reorder__extra_child__400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH with an ID that is not a child of the parent -> 400.
        """

        board_auth_ctx.user_id = '100'

        joiner_objs = [
            self.__mock_joiner('j0', 'zone_a'),
            self.__mock_joiner('j1', 'zone_b'),
            self.__mock_joiner('j2', 'zone_c'),
        ]
        board_ds.get_list.return_value = joiner_objs

        # 'zone_d' does not belong to v_I
        with pytest.raises(DataSourceError):
            board_client.patch(
                '/reorder/v_I', json={'order': ['zone_a', 'zone_b', 'zone_c', 'zone_d']}
            )

        board_ds.upsert_batch.assert_not_called()

    def test_reorder__wrong_ids__400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ):
        """
        PATCH with completely wrong child IDs -> 400.
        """

        board_auth_ctx.user_id = '100'

        joiner_objs = [
            self.__mock_joiner('j0', 'zone_a'),
            self.__mock_joiner('j1', 'zone_b'),
            self.__mock_joiner('j2', 'zone_c'),
        ]
        board_ds.get_list.return_value = joiner_objs

        with pytest.raises(DataSourceError):
            board_client.patch('/reorder/v_I', json={'order': ['zone_x', 'zone_y', 'zone_z']})

        board_ds.upsert_batch.assert_not_called()

    def __mock_joiner(self, joiner_id: str, child_id: str) -> MagicMock:
        """Creates a minimal mock joiner object for zone_view."""

        child = MagicMock()
        child.id = child_id

        obj = MagicMock()
        obj.id = joiner_id
        obj.to_one_relationships = {'zone': child}

        return obj
