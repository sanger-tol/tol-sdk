# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base2.misc import AuthContext
from tol.api_client2.view import View
from tol.board import dashboard_blueprint
from tol.core import (
    DataSource,
    DataSourceFilter,
    OperableDataSource
)
from tol.core.operator import (
    DetailGetter,
    PageGetter,
    Relational
)


@pytest.fixture
def ds() -> OperableDataSource:
    ds_class = type(
        '',
        (
            DataSource,
            DetailGetter,
            PageGetter,
            Relational,
        ),
        {}
    )

    mock_ds: OperableDataSource = create_autospec(
        ds_class,
        spec_set=True
    )

    mock_ds.supported_types = [
        'component',
        'component_zone',
        'zone',
        'zone_view',
        'view',
        'view_board',
        'board',
        'user'
    ]

    return mock_ds


@pytest.fixture
def ctx() -> AuthContext:
    return create_autospec(
        AuthContext,
        spec_set=True
    )


@pytest.fixture
def view() -> View:
    return create_autospec(
        View,
        spec_set=True
    )


@pytest.fixture
def admin_role() -> str:
    return 'adminzzzz'


@pytest.fixture
def app(
    ds: OperableDataSource,
    ctx: AuthContext,
    view: View,
    admin_role: str,
) -> Flask:

    app = Flask(__name__)
    app.testing = True

    bp = dashboard_blueprint(
        ds,
        admin_role=admin_role,
        ctx_getter=lambda: ctx,
        view_factory=lambda: view
    )
    app.register_blueprint(bp)

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


class TestDashboardBlueprint:
    """
    Tests `dashboard_blueprint()` for both:

    - methods called on the given `DataSource`
    - permissions for various roles
    """

    def test_sorting__components_of_zone(
        self,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):
        """
        `GET /zone/{id}/components` respects `order`
        in `component_zone` table
        """

        ctx.authenticated = True
        ctx.user_id = 100
        ctx.roles = [admin_role]

        ds.get_list_page.return_value = [
            {
                'type': 'component_zone',
                'id': c,
                'order': 50 - i * 3  # descending order
            }
            for i, c in enumerate('abc')
        ]

        mock_detail = MagicMock()
        ds.get_by_ids.return_value = mock_detail

        mock_json = [{'does not': 'matter'}]
        view.dump_bulk.return_value = mock_json

        r = client.get(
            '/zone/605/components?page=1&page_size=20'
        )

        assert r.status_code == 200
        assert r.json == mock_json
        assert ds.get_list_page.called_once_with(
            'component_zone',
            1,
            page_size=20,
            object_filters=DataSourceFilter(
                and_={
                    'zone.id': {
                        'eq': {
                            'value': '605'
                        }
                    }
                }
            ),
            sort_by='order'
        )
        assert ds.get_by_ids.call_count == 1
        (type_, ids) = ds.get_by_ids.call_args_list[0]
        assert type_ == 'component'
        assert list(ids) == ['c', 'b', 'a']
        assert view.dump_bulk.called_once_with(
            mock_detail
        )

