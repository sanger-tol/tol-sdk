# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from flask.testing import FlaskClient

from tol.api_base2.misc import AuthContext
from tol.api_client2.view import View
from tol.core import (
    DataSourceFilter,
    OperableDataSource
)


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
        in the `component_zone` table.
        """

        self.__test_sorting(
            'zone',
            'component',
            ctx,
            ds,
            view,
            client,
            admin_role,
        )

    def test_sorting__zones_of_view(
        self,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):
        """
        `GET /zone/{id}/components` respects `order`
        in the `component_zone` table.
        """

        self.__test_sorting(
            'view',
            'zone',
            ctx,
            ds,
            view,
            client,
            admin_role,
        )

    def test_sorting__views_of_board(
        self,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):
        """
        `GET /zone/{id}/components` respects `order`
        in the `component_zone` table.
        """

        self.__test_sorting(
            'board',
            'view',
            ctx,
            ds,
            view,
            client,
            admin_role,
        )

    def __test_sorting(
        self,
        container_type: str,
        smaller_type: str,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):
        """The common logic of the "sorting" tests."""

        joining_type = f'{smaller_type}_{container_type}'

        ctx.authenticated = True
        ctx.user_id = 100
        ctx.roles = [admin_role]

        ds.get_list_page.return_value = [
            {
                'type': joining_type,
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
            f'/{container_type}/605/{smaller_type}'
            '?page=1&page_size=20'
        )

        assert r.status_code == 200
        assert r.json == mock_json
        assert ds.get_list_page.called_once_with(
            joining_type,
            1,
            page_size=20,
            object_filters=DataSourceFilter(
                and_={
                    f'{container_type}.id': {
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
        assert type_ == smaller_type
        assert list(ids) == ['c', 'b', 'a']
        assert view.dump_bulk.called_once_with(
            mock_detail
        )

