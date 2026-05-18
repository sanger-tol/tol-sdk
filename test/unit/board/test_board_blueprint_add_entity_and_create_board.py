# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, cast
from unittest.mock import MagicMock

from flask.testing import FlaskClient

import pytest

import tol.board.utils as board_utils_module
from tol.api_base.auth import ForbiddenError
from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError
from tol.sql import SqlDataSource


class TestBoardBlueprintAddEntityAndCreateBoard:

    def test_create_board__201(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST create_board creates board + first view + join row,
        then returns full serialized board JSON.
        """

        board_auth_ctx.user_id = '100'

        ids = iter(['board12345678', 'view123456789'])
        monkeypatch.setattr(
            board_utils_module,
            'generate',
            lambda *_args: next(ids)
        )

        def _factory(*, type_, id_=None, attributes=None, to_one=None):
            return self.__mock_obj(
                type_,
                id_=id_,
                attributes=attributes or {},
                to_one=to_one or {},
            )

        cast(MagicMock, board_ds).data_object_factory.side_effect = _factory

        r = board_client.post(
            '/create-board',
            json={}
        )

        assert r.status_code == 201
        payload = r.get_json()

        assert payload['id'] == 'b_board12345678'
        assert payload['type'] == 'board'
        assert payload['title'] == 'Untitled board'
        assert payload['order'] == ['v_view123456789']
        children = (
            payload['children'][0]
            if isinstance(payload['children'], list)
            else payload['children']
        )
        assert 'v_view123456789' in children
        assert children['v_view123456789']['title'] == 'View 1'

        inserted_types = [call.args[0] for call in cast(MagicMock, board_ds).insert.call_args_list]
        assert inserted_types == ['board', 'view', 'view_board']

    def test_create_board__404_snake_case_alias_removed(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST create_board snake_case alias is not registered.
        """

        board_auth_ctx.user_id = '100'

        ids = iter(['board12345678', 'view123456789'])
        monkeypatch.setattr(
            board_utils_module,
            'generate',
            lambda *_args: next(ids)
        )

        def _factory(*, type_, id_=None, attributes=None, to_one=None):
            return self.__mock_obj(
                type_,
                id_=id_,
                attributes=attributes or {},
                to_one=to_one or {},
            )

        cast(MagicMock, board_ds).data_object_factory.side_effect = _factory

        r = board_client.post('/create_board', json={})
        assert r.status_code == 405

    def test_create_board__next_order_from_existing_joins(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST create_board sets view_board.order to max(existing)+1.
        """

        board_auth_ctx.user_id = '100'

        ids = iter(['board12345678', 'view123456789'])
        monkeypatch.setattr(
            board_utils_module,
            'generate',
            lambda *_args: next(ids)
        )

        existing_join = self.__mock_obj('view_board', id_='j1', attributes={'order': 2})
        cast(MagicMock, board_ds).get_list.return_value = [existing_join]

        def _factory(*, type_, id_=None, attributes=None, to_one=None):
            return self.__mock_obj(
                type_,
                id_=id_,
                attributes=attributes or {},
                to_one=to_one or {},
            )

        cast(MagicMock, board_ds).data_object_factory.side_effect = _factory

        r = board_client.post('/create-board', json={})
        assert r.status_code == 201

        factory_calls = cast(MagicMock, board_ds).data_object_factory.call_args_list
        assert any(
            call.kwargs.get('type_') == 'view_board'
            and call.kwargs.get('attributes') == {'order': 3}
            for call in factory_calls
        )

    def test_add_entity__201(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST add where parent exists and user owns parent -> success.

        Inserts both the child entity and the joiner row with next order.
        """

        board_auth_ctx.user_id = '100'

        parent_obj = self.__mock_obj('view', 'v_parent', user_id='100')

        existing_join_1 = self.__mock_obj('zone_view', id_='j1', attributes={'order': 1})
        existing_join_2 = self.__mock_obj('zone_view', id_='j2', attributes={'order': 3})

        cast(MagicMock, board_ds).get_one.return_value = parent_obj
        cast(MagicMock, board_ds).get_list.return_value = [existing_join_1, existing_join_2]

        r = board_client.post(
            '/add-entity/v_parent',
            json={'attributes': {'title': 'New S', 'filter': {'a': 1}}}
        )

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['type'] == 'zone'
        assert payload['parent_id'] == 'v_parent'
        assert payload['parent_order'] == 4
        assert payload['order'] == []
        assert payload['children'] == {}
        assert payload['title'] == 'New S'

        inserted_types = [call.args[0] for call in cast(MagicMock, board_ds).insert.call_args_list]
        assert inserted_types == ['zone', 'zone_view']

        factory_calls = cast(MagicMock, board_ds).data_object_factory.call_args_list
        assert any(
            call.kwargs.get('type_') == 'zone'
            and call.kwargs.get('id_', '').startswith('z_')
            for call in factory_calls
        )
        assert any(
            call.kwargs.get('type_') == 'zone_view'
            and call.kwargs.get('attributes') == {'order': 4}
            for call in factory_calls
        )

    def test_add_entity__400_bad_parent_type(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
    ):
        """
        POST add where parent is a leaf node (component has no children) -> failure.
        """

        board_auth_ctx.user_id = '100'

        with pytest.raises(Exception):
            board_client.post('/add-entity/c_component123', json={'attributes': {'title': 'New zone'}})

    def test_add_entity__400_unknown_object_type(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
    ):
        """
        POST add with an unrecognized parent ID prefix -> failure.
        """

        board_auth_ctx.user_id = '100'

        with pytest.raises(ValueError):
            board_client.post(
                '/add-entity/x_unknown123',
                json={'attributes': {'title': 'New X'}},
            )

    def test_add_entity__404_parent_not_found(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST add where the resolved parent does not exist -> failure (404).
        """

        board_auth_ctx.user_id = '100'

        cast(MagicMock, board_ds).get_one.return_value = None

        with pytest.raises(DataSourceError) as e:
            board_client.post('/add-entity/v_missing', json={'attributes': {'title': 'New zone'}})

        assert e.value.title == 'Not Found'
        assert e.value.status_code == 404

    def test_add_entity__403(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST add where parent is not owned by current user -> failure (403).
        """

        board_auth_ctx.user_id = '100'

        parent_obj = self.__mock_obj('view', 'v_parent', user_id='other_user')
        cast(MagicMock, board_ds).get_one.return_value = parent_obj

        with pytest.raises(ForbiddenError):
            board_client.post('/add-entity/v_parent', json={'attributes': {'title': 'New zone'}})

    def test_add_entity__201_defaults_title(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST add defaults title when attributes.title is missing.
        """

        board_auth_ctx.user_id = '100'

        parent_obj = self.__mock_obj('view', 'v_parent', user_id='100')
        cast(MagicMock, board_ds).get_one.return_value = parent_obj
        cast(MagicMock, board_ds).get_list.return_value = []

        r = board_client.post('/add-entity/v_parent', json={'attributes': {}})

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['title'] == 'New zone'
        assert payload['parent_order'] == 1
        assert payload['order'] == []

    def __mock_obj(
        self,
        type_: str,
        id_: str | None = None,
        attributes: dict[str, Any] = {},
        to_one: dict[str, DataObject] = {},
        user_id: str | None = None
    ) -> DataObject:

        obj = MagicMock()

        obj.type = type_
        obj.id = id_
        obj.oidc_id = None
        obj.data_source_instance = MagicMock()
        obj.data_source_instance.id = None
        obj.data_source_instance.ui_api_details = None

        obj._to_one_objects = to_one
        obj.to_one_relationships = to_one  # type: ignore
        for k, v in to_one.items():
            setattr(obj, k, v)

        obj.attributes = attributes
        for k, v in attributes.items():
            setattr(obj, k, v)

        if user_id is not None:
            user = self.__mock_obj('user', user_id)
            obj.user = user
            obj._to_one_objects['user'] = user

        return cast(DataObject, obj)
