# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base2.misc import AuthContext
from tol.board import dashboard_blueprint
from tol.core import core_data_object
from tol.sql import SqlDataSource, create_sql_datasource

from ..models import delete_models_list


@pytest.fixture
def board_ctx() -> AuthContext:
    return create_autospec(
        AuthContext,
        spec_set=True
    )


@pytest.fixture
def board_sql_ds():
    sql_ds = create_sql_datasource(
        delete_models_list,
        os.environ['DB_URI']
    )
    core_data_object(sql_ds)

    return sql_ds


@pytest.fixture
def board_app(
    board_sql_ds: SqlDataSource,
    board_ctx: AuthContext,
) -> Flask:

    board_app = Flask(__name__)
    board_app.testing = True

    board_bp = dashboard_blueprint(
        board_sql_ds,
        ctx_getter=lambda: board_ctx
    )
    board_app.register_blueprint(board_bp)

    return board_app


@pytest.fixture
def board_client(board_app: Flask) -> FlaskClient:
    return board_app.test_client()


class TestDashboardSorting:
    """
    Tests dashboard sorting against a real postgres DB,
    with real data.
    """

    def test_sorting__component_zone(
        self,
        board_sql_ds: SqlDataSource,
        board_client: FlaskClient,
        board_ctx: AuthContext
    ):

        board_ctx.user_id = '1'

        user = board_sql_ds.data_object_factory(
            'user',
            '1',
            {
                'changed_lol': 'have to add this'
            }
        )
        board_sql_ds.upsert(
            'user',
            [user]
        )

        zone = board_sql_ds.data_object_factory(
            'zone',
            '100',
            {
                'title': '',
                'object_type': 'test'
            },
            to_one={'user': user}
        )

        board_sql_ds.upsert(
            'zone',
            [zone]
        )

        components = [
            board_sql_ds.data_object_factory(
                'component',
                ord(c),
                {
                    'title': '',
                    'object_type': 'test',
                    'config': {},
                    'base_url': '',
                    'component_type': '',
                    'widget_type': ''
                },
                to_one={'user': user}
            )
            for c in 'abcd'
        ]

        board_sql_ds.upsert(
            'component',
            components
        )

        # decreasing order for component_zone `order`
        board_sql_ds.upsert(
            'component_zone',
            [
                board_sql_ds.data_object_factory(
                    'component_zone',
                    str(i),
                    {
                        'order': i
                    },
                    to_one={
                        'zone': zone,
                        'component': component
                    }
                )
                for i, component in enumerate(
                    reversed(components)
                )
            ]
        )

        container_type = 'zone'
        element_type = 'component'

        r = board_client.get(
            f'/{container_type}/100/{element_type}s'
            '?page=1&page_size=20'
        )

        assert r.status_code == 200

        ids = [
            chr(int(do['id']))
            for do in r.json['data']
        ]
        assert ids == ['d', 'c', 'b', 'a']
