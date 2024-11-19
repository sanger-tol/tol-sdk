# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, create_autospec

from flask.testing import FlaskClient

from tol.api_base2.misc import AuthContext
from tol.api_client2.view import View
from tol.core import (
    DataObject,
    DataSourceFilter,
    OperableDataSource
)


class TestDashboardSorting:
    """
    Tests `dashboard_blueprint()` for correct ordering.
    """

    def test_sorting__components_of_zone(
        self,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):

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
        element_type: str,
        ctx: AuthContext,
        ds: OperableDataSource,
        view: View,
        client: FlaskClient,
        admin_role: str
    ):
        """The common logic of the "sorting" tests."""

        joining_type = f'{element_type}_{container_type}'

        ctx.authenticated = True
        ctx.user_id = '100'
        ctx.roles = [admin_role]

        ds.get_list_page.return_value = [
            self.__mock_obj(
                c,
                i,
                element_type
            )
            for i, c in enumerate('abc')
        ]

        mock_detail = MagicMock()
        ds.get_by_ids.return_value = mock_detail

        mock_json = [{'does not': 'matter'}]
        view.dump_bulk.return_value = mock_json

        r = client.get(
            f'/{container_type}/605/{element_type}s'
            '?page=1&page_size=20'
        )

        assert r.status_code == 200
        assert r.json == mock_json
        ds.get_list_page.assert_called_once_with(
            joining_type,
            1,
            page_size=20,
            object_filters=DataSourceFilter(
                and_={
                    f'{container_type}.id': {
                        'eq': {
                            'value': '605'
                        }
                    },
                    f'{container_type}.user.id': {
                        'eq': {
                            'value': '100'
                        }
                    }
                }
            ),
            sort_by='order'
        )
        assert ds.get_by_ids.call_count == 1
        (type_, ids) = ds.get_by_ids.call_args_list[0].args
        assert type_ == element_type
        assert list(ids) == ['a', 'b', 'c']
        view.dump_bulk.assert_called_once_with(
            mock_detail
        )

    def __mock_obj(
        self,
        id_: str,
        order: str,
        element_type: str
    ) -> DataObject:

        mock_obj: DataObject = create_autospec(
            DataObject
        )
        mock_obj.attributes = {
            'order': order
        }

        mock_element: DataObject = create_autospec(
            DataObject,
            spec_set=True
        )
        mock_element.id = id_

        setattr(mock_obj, element_type, mock_element)

        return mock_obj
