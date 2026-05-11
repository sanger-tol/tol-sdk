# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import count
from typing import Any, Iterator

from tol.core import DataObject
from tol.sql import SqlDataSource


def insert_board_hierarchy(
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

    # build up the data_source_config and data_source_instance
    data_source_config = board_ds.data_object_factory(
        'data_source_config',
        id_=1,
        attributes={
            'name': 'tol-test',
            'description': 'Test data source config',
        }
    )
    board_ds.insert('data_source_config', [data_source_config])

    data_source_instance = board_ds.data_object_factory(
        'data_source_instance',
        id_='tol_system_test',
        attributes={
            'builtin_name': 'elastic-test',
            'kwargs': {},
            'publish': True,
            'ui_api_details': {
                'url': 'http://example.com',
                'apiPath': '/v1/data',
                'apiDataPath': '/data',
                'dataspace': 'test_dataspace'
            }
        },
        to_one={
            'data_source_config': data_source_config
        }
    )
    board_ds.insert('data_source_instance', [data_source_instance])

    objs: dict[str, dict[str, DataObject]] = {}

    # build up the exposed types
    for t in type_hierarchy:
        t_objs = {
            id_: board_ds.data_object_factory(
                t,
                id_=id_,
                attributes=get_board_attributes(t, id_),
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

        objs[joiner] = insert_board_joins(
            board_ds,
            objs,
            bigger,
            joiner,
            smaller,
            obj_hierachy.get(bigger, {}),
            join_ids
        )


def get_board_attributes(
    type_: str,
    id_: str
) -> dict[str, Any]:
    """
    Returns appropriate attributes dict for a given board entity type.
    """

    if type_ == 'component':
        return {
            'title': f'component_{id_}',
            'config': {},
            'object_type': 'sample',
            'data_source_instance_id': 'tol_system_test',
            'component_type': 'table',
            'widget_type': 'idk this is a test',
            'filter_pass_through': False
        }

    elif type_ == 'zone':
        return {
            'title': f'zone_{id_}',
            'object_type': 'sample',
            'data_source_instance_id': 'tol_system_test',
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


def insert_board_joins(
    board_ds: SqlDataSource,
    objs: dict[str, dict[str, DataObject]],
    bigger: str,
    joiner: str,
    smaller: str,
    type_def: dict[str, tuple[str, list[str]]],
    join_ids: Iterator[int]
) -> None:
    """
    Inserts joining table rows linking smaller entities to their bigger.
    """

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
