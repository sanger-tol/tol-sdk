# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import count
from typing import Any, Iterator

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError
from tol.sql import SqlDataSource


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
                '1': ('100', []),
            },
            'zone': {
                'a': ('100', ['1'])
            },
            'view': {
                'I': ('100', ['a'])
            }
        }

        self.__insert_hierarchy(
            board_ds,
            hierarchy,
            type_hierarchy,
            ['100']
        )

        board_auth_ctx.user_id = '100'

        r = board_client.delete(
            '/zone/a'
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
                '1': ('100', []),
            },
            'zone': {
                'a': ('100', ['1'])
            },
            'view': {
                # someone else owns this view
                'I': ('303', ['a'])
            }
        }

        self.__insert_hierarchy(
            board_ds,
            hierarchy,
            type_hierarchy,
            ['100', '303']
        )

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.delete(
                '/zone/a'
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
                '1': ('100', []),
            },
            'zone': {
                'a': ('100', ['1'])
            },
            'view': {
                # four views point to the above zone, and
                # all belong to user `100`
                'I': ('100', ['a']),
                'II': ('100', ['a']),
                'III': ('100', ['a']),
                'IV': ('100', ['a']),
            }
        }

        self.__insert_hierarchy(
            board_ds,
            hierarchy,
            type_hierarchy,
            ['100']
        )

        board_auth_ctx.user_id = '100'

        with pytest.raises(DataSourceError) as e:
            board_client.delete(
                '/zone/a'
            )
            assert e.value.status_code == 400

    def __insert_hierarchy(
        self,
        board_ds: SqlDataSource,
        obj_hierachy: dict[str, dict[str, tuple[str, list[str]]]],
        type_hierarchy: list[str],
        user_ids: list[str]
    ) -> None:
        """
        Inserts all objects in the hierarchy with joins.

        For the smallest one, give an empty list each time.
        """

        # build up the users
        users = {
            user_id: board_ds.data_object_factory(
                'user',
                id_=user_id,
                attributes={
                    'changed_lol': f'random_lol....{user_id}'
                }
            )
            for user_id in user_ids
        }
        board_ds.insert('user', list(users.values()))

        objs: dict[str, dict[str, DataObject]] = {}

        # build up the exposed types
        for t in type_hierarchy:
            t_objs = {
                id_: board_ds.data_object_factory(
                    t,
                    id_=id_,
                    attributes=self.__get_attributes(
                        t,
                        id_
                    ),
                    to_one={
                        'user': users[user_id]
                    }
                )
                for id_, (user_id, _)
                in obj_hierachy.get(t, {}).items()
            }
            board_ds.insert(t, list(t_objs.values()))
            objs[t] = t_objs

        join_ids = iter(count())

        # build up the joining types
        for i, bigger in enumerate(type_hierarchy[:-1]):
            smaller = type_hierarchy[i + 1]
            joiner = f'{smaller}_{bigger}'

            objs[joiner] = self.__insert_joins(
                board_ds,
                objs,
                bigger,
                joiner,
                smaller,
                obj_hierachy.get(bigger, {}),
                join_ids
            )

    def __get_attributes(
        self,
        type_: str,
        id_: str
    ) -> dict[str, Any]:

        if type_ == 'component':
            return {
                'title': f'component_{id_}',
                'config': {},
                'object_type': 'sample',
                'datasource': '{"api_prefix": "local", "base_url": "portal.com"}',
                'component_type': 'table',
                'widget_type': 'idk this is a test',
                'filter_pass_through': False
            }

        elif type_ == 'zone':
            return {
                'title': f'zone_{id_}',
                'object_type': 'sample',
                'datasource': '{"api_prefix": "local", "base_url": "portal.com"}',
            }

        elif type_ == 'view':
            return {
                'title': f'view_{id_}'
            }

        # board
        else:
            return {
                'title': f'board_{id_}'
            }

    def __insert_joins(
        self,
        board_ds: SqlDataSource,
        objs: dict[str, dict[str, DataObject]],
        bigger: str,
        joiner: str,
        smaller: str,
        type_def: dict[str, tuple[str, list[str]]],
        join_ids: Iterator[int]
    ) -> None:

        all_pairs = (
            (k, v)
            for k, (_, v_list) in type_def.items()
            for v in v_list
        )

        join_defs = (
            (
                next(join_ids),
                (
                    objs[bigger][k],
                    objs[smaller][v]
                )
            )
            for k, v in all_pairs
        )

        join_objs = (
            board_ds.data_object_factory(
                joiner,
                id_=str(join_id),
                attributes={
                    'order': join_id
                },
                to_one={
                    bigger: bigger_obj,
                    smaller: smaller_obj
                }
            )
            for join_id, (bigger_obj, smaller_obj)
            in join_defs
        )

        board_ds.insert(joiner, join_objs)
