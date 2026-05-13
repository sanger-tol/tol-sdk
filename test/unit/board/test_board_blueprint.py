# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import reduce
from itertools import count
from typing import Any, Callable, Iterator
from unittest.mock import _Call, create_autospec

from flask.testing import FlaskClient

import pytest

import tol.board.blueprint as board_blueprint_module
from tol.api_base.auth import ForbiddenError
from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError, DataSourceFilter
from tol.sql import SqlDataSource


class TestBoardBlueprint:

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
            board_blueprint_module,
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

        board_ds.data_object_factory.side_effect = _factory

        r = board_client.post(
            '/create-board',
            json={
                'board_title': 'My board',
                'first_view_title': 'My first view',
            }
        )

        assert r.status_code == 201
        payload = r.get_json()

        assert payload['id'] == 'l_board12345678'
        assert payload['type'] == 'L'
        assert payload['title'] == 'My board'
        assert payload['order'] == ['m_view123456789']
        children = (
            payload['children'][0]
            if isinstance(payload['children'], list)
            else payload['children']
        )
        assert 'm_view123456789' in children
        assert children['m_view123456789']['title'] == 'My first view'

        inserted_types = [call.args[0] for call in board_ds.insert.call_args_list]
        assert inserted_types == ['L', 'M', 'M_L']

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
            board_blueprint_module,
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

        board_ds.data_object_factory.side_effect = _factory

        r = board_client.post('/create_board', json={})
        assert r.status_code == 404

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
            board_blueprint_module,
            'generate',
            lambda *_args: next(ids)
        )

        existing_join = self.__mock_obj('M_L', id_='j1', attributes={'order': 2})
        board_ds.get_list.return_value = [existing_join]

        def _factory(*, type_, id_=None, attributes=None, to_one=None):
            return self.__mock_obj(
                type_,
                id_=id_,
                attributes=attributes or {},
                to_one=to_one or {},
            )

        board_ds.data_object_factory.side_effect = _factory

        r = board_client.post('/create-board', json={})
        assert r.status_code == 201

        factory_calls = board_ds.data_object_factory.call_args_list
        assert any(
            call.kwargs.get('type_') == 'M_L'
            and call.kwargs.get('attributes') == {'order': 3}
            for call in factory_calls
        )

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

        mock_small = self.__mock_obj(
            'S',
            'delete_me',
            user_id='100'
        )
        board_ds.get_one.side_effect = lambda *_: mock_small
        board_ds.get_count.return_value = 0

        r = board_client.delete('/S/delete_me')
        assert r.status_code == 200

        board_ds.delete.assert_called_once_with('S', ['delete_me'])

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

        monkeypatch.setattr(
            board_blueprint_module,
            'get_entity_type_from_prefix',
            lambda _prefix: 'M'
        )

        parent_obj = self.__mock_obj('M', 'm_parent', user_id='100')

        existing_join_1 = self.__mock_obj('S_M', id_='j1', attributes={'order': 1})
        existing_join_2 = self.__mock_obj('S_M', id_='j2', attributes={'order': 3})

        board_ds.get_one.return_value = parent_obj
        board_ds.get_list.return_value = [existing_join_1, existing_join_2]

        r = board_client.post(
            '/add-entity/S/m_parent',
            json={'attributes': {'title': 'New S', 'filter': {'a': 1}}}
        )

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['type'] == 'S'
        assert payload['parent_id'] == 'm_parent'
        assert payload['order'] == 4
        assert payload['title'] == 'New S'

        inserted_types = [call.args[0] for call in board_ds.insert.call_args_list]
        assert inserted_types == ['S', 'S_M']

        factory_calls = board_ds.data_object_factory.call_args_list
        assert any(
            call.kwargs.get('type_') == 'S'
            and call.kwargs.get('id_', '').startswith('S_')
            for call in factory_calls
        )
        assert any(
            call.kwargs.get('type_') == 'S_M'
            and call.kwargs.get('attributes') == {'order': 4}
            for call in factory_calls
        )

    def test_add_entity__400_bad_parent_type(
        self,
        board_auth_ctx: AuthContext,
        board_client: FlaskClient,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """
        POST add where parent prefix resolves to wrong type -> failure (400).
        """

        board_auth_ctx.user_id = '100'

        monkeypatch.setattr(
            board_blueprint_module,
            'get_entity_type_from_prefix',
            lambda _prefix: 'L'
        )

        with pytest.raises(DataSourceError) as e:
            board_client.post('/add-entity/S/m_parent', json={'attributes': {'title': 'New S'}})

        assert e.value.title == 'Bad Parent'
        assert e.value.status_code == 400

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

        monkeypatch.setattr(
            board_blueprint_module,
            'get_entity_type_from_prefix',
            lambda _prefix: 'M'
        )

        parent_obj = self.__mock_obj('M', 'm_parent', user_id='other_user')
        board_ds.get_one.return_value = parent_obj

        with pytest.raises(ForbiddenError):
            board_client.post('/add-entity/S/m_parent', json={'attributes': {'title': 'New S'}})

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

        monkeypatch.setattr(
            board_blueprint_module,
            'get_entity_type_from_prefix',
            lambda _prefix: 'M'
        )

        parent_obj = self.__mock_obj('M', 'm_parent', user_id='100')
        board_ds.get_one.return_value = parent_obj
        board_ds.get_list.return_value = []

        r = board_client.post('/add-entity/S/m_parent', json={'attributes': {}})

        assert r.status_code == 201
        payload = r.get_json()
        assert payload['title'] == 'New S'
        assert payload['order'] == 1

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

        mock_small = self.__mock_obj(
            'S',
            'delete_me',
            user_id='no_match'
        )
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

        objs = self.__mock_hierarchy(
            hierarchy,
            type_hierarchy=type_hierarchy
        )

        board_ds.get_one.side_effect = self.__mock_get_one(objs)
        board_ds.get_list.side_effect = self.__mock_get_list(objs)
        board_ds.get_count.side_effect = self.__mock_get_count(objs)

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

        objs = self.__mock_hierarchy(
            hierarchy,
            type_hierarchy=type_hierarchy
        )

        board_ds.get_one.side_effect = self.__mock_get_one(objs)
        board_ds.get_list.side_effect = self.__mock_get_list(objs)
        board_ds.get_count.side_effect = self.__mock_get_count(objs)

        r = board_client.delete('/L/I')
        assert r.status_code == 200

        observed_deletes = self.__format_type_deletes(board_ds)
        assert observed_deletes['S'] == {'1'}
        assert observed_deletes['M'] == {'a'}
        assert observed_deletes['L'] == {'I'}
        assert len(observed_deletes['S_M']) == 2  # a->1, a->3
        assert len(observed_deletes['M_L']) == 2  # I->a, I->b

    def __mock_get_one(
        self,
        objs: dict[str, dict[str, DataObject]]
    ) -> Callable[[str, str], DataObject | None]:

        def __get_one(
            object_type: str,
            object_id: str
        ) -> DataObject | None:

            return objs[object_type].get(object_id)

        return __get_one

    def __mock_get_count(
        self,
        objs: dict[str, dict[str, DataObject]]
    ) -> Callable:

        def __get_count(
            joiner_type: str,  # object_type
            *,
            object_filters: DataSourceFilter
        ) -> int:

            smaller_type, bigger_type = joiner_type.split('_')

            smaller_id = object_filters.and_[f'{smaller_type}.id']['eq']['value']

            # note this is a negate term
            all_bigger_ids = object_filters.and_[f'{bigger_type}.id']['in_list']['value']

            joiner_objs = [
                obj for obj in objs[joiner_type].values()
                if getattr(obj, smaller_type).id == smaller_id
                and getattr(obj, bigger_type).id not in all_bigger_ids
            ]
            return len(joiner_objs)

        return __get_count

    def __mock_get_list(
        self,
        objs: dict[str, dict[str, DataObject]]
    ) -> Callable:

        def __get_list(
            object_type: str,  # object_type
            *,
            object_filters: DataSourceFilter
        ) -> list[DataObject]:

            _, bigger = object_type.split('_')

            bigger_id = object_filters.and_[f'{bigger}.id']['eq']['value']

            return [
                obj for obj in objs[object_type].values()
                if getattr(obj, bigger).id == bigger_id
            ]

        return __get_list

    def __mock_hierarchy(
        self,
        obj_hierachy: dict[str, dict[str, tuple[str, list[str]]]],
        *,
        type_hierarchy: list[str]
    ) -> dict[str, dict[str, DataObject]]:
        """
        Mocks all objects in the hierarchy with joins.

        For the smallest one, give an empty list each time.
        """

        objs: dict[str, dict[str, DataObject]] = {}

        # build up the exposed types
        for t in type_hierarchy:
            objs[t] = {
                k: self.__mock_obj(t, id_=k, user_id=user_id)
                for k, (user_id, _)
                in obj_hierachy.get(t, {}).items()
            }

        join_ids = iter(count())

        # build up the joining types
        for i, bigger in enumerate(type_hierarchy[:-1]):
            smaller = type_hierarchy[i + 1]
            joiner = f'{smaller}_{bigger}'

            objs[joiner] = self.__mock_join(
                objs,
                bigger,
                joiner,
                smaller,
                obj_hierachy[bigger],
                join_ids
            )

        return objs

    def __mock_join(
        self,
        objs: dict[str, dict[str, DataObject]],
        bigger: str,
        joiner: str,
        smaller: str,
        type_def: dict[str, tuple[str, list[str]]],
        join_ids: Iterator[str]
    ) -> dict[str, DataObject]:

        all_pairs = (
            (k, v)
            for k, (_, v_list) in type_def.items()
            for v in v_list
        )

        join_defs = (
            (
                str(next(join_ids)),
                (
                    objs[bigger][k],
                    objs[smaller][v]
                )
            )
            for k, v in all_pairs
        )

        return {
            id_: self.__mock_obj(
                joiner,
                id_=id_,
                to_one={
                    bigger: bigger_obj,
                    smaller: smaller_obj
                }
            )
            for id_, (bigger_obj, smaller_obj)
            in join_defs
        }

    def __mock_obj(
        self,
        type_: str,
        id_: str | None = None,
        attributes: dict[str, Any] = {},
        to_one: dict[str, DataObject] = {},
        user_id: str | None = None
    ) -> DataObject:

        obj: DataObject = create_autospec(DataObject)

        obj.type = type_
        obj.id = id_

        obj._to_one_objects = to_one
        for k, v in to_one.items():
            setattr(obj, k, v)

        obj.attributes = attributes
        for k, v in attributes.items():
            setattr(obj, k, v)

        if user_id is not None:
            user = self.__mock_obj('user', user_id)
            obj.user = user
            obj._to_one_objects['user'] = user

        return obj

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

        return reduce(
            __effect,
            call_list,
            {}
        )
