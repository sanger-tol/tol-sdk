# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Optional, cast
from unittest.mock import MagicMock

from flask.testing import FlaskClient

import pytest

import tol.board.utils as board_utils_module
from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError
from tol.sql import SqlDataSource

from .utils import (
    mock_board_get_list,
    mock_board_get_one,
    mock_board_hierarchy,
    mock_board_obj,
)


class TestBoardBlueprintCopyEntity:

    def __factory(
        self,
        *,
        type_: str,
        id_: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        to_one: Optional[Dict[str, DataObject]] = None,
    ) -> DataObject:
        return mock_board_obj(
            type_,
            id_=id_,
            attributes=attributes,
            to_one=to_one,
        )

    def test_copy_entity__201(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        POST copy a single view (no children) -> 201, title updated, new ID assigned.
        """

        board_auth_ctx.user_id = '100'

        view = mock_board_obj('view', 'v_orig', attributes={'title': 'My View'}, user_id='100')
        board_ds.get_one.return_value = view
        board_ds.get_list.return_value = []
        board_ds.get_count.return_value = 0

        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: 'viewcopy1234')

        cast(MagicMock, board_ds).data_object_factory.side_effect = self.__factory

        r = board_client.post(
            '/copy/view/v_orig',
            json={'new_parent_entity_title': 'Copied View'},
        )

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['title'] == 'Copied View'
        assert payload['type'] == 'view'
        assert payload['id'] == 'v_viewcopy1234'

        inserted_types = [call.args[0] for call in cast(MagicMock, board_ds).insert.call_args_list]
        assert inserted_types == ['view']

    def test_copy_entity__404(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
    ) -> None:
        """
        POST copy where entity does not exist -> 404 DataSourceError.
        """

        board_auth_ctx.user_id = '100'

        board_ds.get_one.return_value = None

        with pytest.raises(DataSourceError) as exc:
            board_client.post(
                '/copy/view/v_missing',
                json={'new_parent_entity_title': 'Copied View'},
            )

        assert exc.value.title == 'Not Found'
        assert exc.value.status_code == 404

    def test_copy_entity__board_and_children_201(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
        type_hierarchy: list,
    ) -> None:
        """
        POST copy a board with one view child -> 201, board + view + view_board inserted.
        """

        board_auth_ctx.user_id = '100'

        hierarchy = {
            'zone': {},
            'view': {
                'v_a': ('100', []),
            },
            'board': {
                'b_I': ('100', ['v_a']),
            },
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.return_value = 0

        id_seq = iter(['boardcopy12', 'viewcopy123'])
        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: next(id_seq))

        cast(MagicMock, board_ds).data_object_factory.side_effect = self.__factory

        r = board_client.post(
            '/copy/board/b_I',
            json={'new_parent_entity_title': 'Board Copy'},
        )

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['title'] == 'Board Copy'
        assert payload['type'] == 'board'
        assert payload['id'] == 'b_boardcopy12'
        assert payload['order'] == ['v_viewcopy123']
        assert 'v_viewcopy123' in payload['children']

        inserted_types = [call.args[0] for call in cast(MagicMock, board_ds).insert.call_args_list]
        assert 'board' in inserted_types
        assert 'view' in inserted_types
        assert 'view_board' in inserted_types

    def test_copy_entity__view_and_children_201(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        board_ds: SqlDataSource,
        monkeypatch: pytest.MonkeyPatch,
        type_hierarchy: list,
    ) -> None:
        """
        POST copy a view with two zone children -> 201, zones appear in children,
        view + zones + zone_view joiners all inserted.
        """

        board_auth_ctx.user_id = '100'

        hierarchy = {
            'component': {},
            'zone': {
                'z_1': ('100', []),
                'z_2': ('100', []),
            },
            'view': {
                'v_a': ('100', ['z_1', 'z_2']),
            },
            'board': {},
        }

        objs = mock_board_hierarchy(hierarchy, type_hierarchy=type_hierarchy)

        board_ds.get_one.side_effect = mock_board_get_one(objs)
        board_ds.get_list.side_effect = mock_board_get_list(objs)
        board_ds.get_count.return_value = 0

        id_seq = iter(['viewcopy123', 'zonecopy123', 'zonecopy456'])
        monkeypatch.setattr(board_utils_module, 'generate', lambda *_: next(id_seq))

        cast(MagicMock, board_ds).data_object_factory.side_effect = self.__factory

        r = board_client.post(
            '/copy/view/v_a',
            json={'new_parent_entity_title': 'View Copy'},
        )

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['title'] == 'View Copy'
        assert payload['type'] == 'view'
        assert payload['id'] == 'v_viewcopy123'
        assert len(payload['order']) == 2

        inserted_types = [call.args[0] for call in cast(MagicMock, board_ds).insert.call_args_list]
        assert inserted_types.count('view') == 1
        assert inserted_types.count('zone') == 2
        assert inserted_types.count('zone_view') == 2

    def test_copy_entity__parent_id_400(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
    ) -> None:
        """
        POST copy without required new_parent_entity_title field -> PayloadError (400).
        """

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as exc:
            board_client.post(
                '/copy/view/v_orig',
                json={},
            )

        assert exc.value.title == 'Payload Error'
        assert exc.value.status_code == 400
