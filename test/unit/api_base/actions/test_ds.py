# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest.mock import create_autospec

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError
from tol.prefect import PrefectDataSource
from tol.sql import SqlDataSource


class TestActionsWithDataSources:
    """
    `action_blueprint()` using stub `DataSource` mocks.
    """

    def test__404(
        self,
        client: FlaskClient,
        ctx: AuthContext,
        sql_ds: SqlDataSource,
        role: str
    ):
        """
        no action found -> raise 404 error
        """

        ctx.user_id = '100'
        ctx.roles = [role]

        sql_ds.get_list.return_value = []

        with pytest.raises(DataSourceError) as e:
            client.post(
                '/run-action',
                json={
                    'data': {
                        'ids': list('abc'),
                        'action_name': 'flowexample',
                        'object_type': 'test',
                        'params': {
                            'additional': 'indeeeeed'
                        }
                    }
                }
            )

        assert e.value.status_code == 404

    def test__200(
        self,
        client: FlaskClient,
        ctx: AuthContext,
        sql_ds: SqlDataSource,
        prefect_ds: PrefectDataSource,
        role: str
    ):

        """
        Valid transaction:

        - `sql_ds.get_one()` on action
        - `sql_ds.get_one()` on user
        - `sql_ds.insert()` on user_action
        - `prefect_ds.insert()` on flow_run
        """

        ctx.user_id = '100'
        ctx.roles = [role]

        sql_ds.data_object_factory.side_effect = self.__do_factory
        sql_ds.get_list.return_value = [self.__mock_action('123')]
        sql_ds.get_one.return_value = self.__mock_user('100')

        response = client.post(
            '/run-action',
            json={
                'data': {
                    'ids': list('abc'),
                    'action_name': 'flowexample',
                    'object_type': 'test',
                    'params': {
                        'additional': 'indeeeeed'
                    }
                }
            }
        )

        assert response.status_code == 200
        assert sql_ds.data_object_factory.call_count == 1

        args, kwargs = sql_ds.data_object_factory.call_args_list[0]

        assert args[0] == 'user_action'

        attributes = kwargs['attributes']
        created_at = attributes.pop('created_at')
        assert isinstance(created_at, datetime)
        assert kwargs['attributes'] == {
            'ids': list('abc'),
            'params': {
                'additional': 'indeeeeed',
                'ids': list('abc'),
                'bool': True,
                'answer': 42
            }
        }

        to_ones = kwargs['to_one']
        assert len(to_ones) == 2

        user = to_ones['user']
        assert user.id == '100'

        action = to_ones['action']
        assert action.id == '123'

        assert sql_ds.insert.call_count == 1
        assert sql_ds.insert.call_args[0][0] == 'user_action'
        mock_data_object_list = sql_ds.insert.call_args[0][1]
        assert len(mock_data_object_list) == 1

        prefect_calls = prefect_ds.data_object_factory.call_args_list
        assert len(prefect_calls) == 1

        args, kwargs = prefect_calls[0]
        assert args[0] == 'flow_run'
        assert kwargs['attributes']['flow_name'] == 'example_flow'
        assert kwargs['attributes']['deployment_name'] == 'example_flow'
        assert kwargs['attributes']['parameters'] == {
            'extra_params': {
                'additional': 'indeeeeed',
                'bool': True,
                'answer': 42,
            },
            'object_type': 'test',
            'ids': list('abc'),
            'user_id': '100'
        }

        assert prefect_ds.insert.call_count == 1

    def __do_factory(
        self,
        type_: str,
        id_=None,
        attributes={},
        **kwargs
    ) -> DataObject:

        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = type_
        mock_obj.id = id_

        mock_obj.attributes = attributes
        for k, v in attributes.items():
            setattr(mock_obj, k, v)

        return mock_obj

    def __mock_action(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'action'
        mock_obj.id = id_

        attributes = {
            'flow_name': 'example_flow',
            'params': {
                'bool': True,
                'answer': 42
            }
        }
        mock_obj.attributes = attributes
        for k, v in attributes.items():
            setattr(mock_obj, k, v)

        return mock_obj

    def __mock_user(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'user'
        mock_obj.id = id_

        return mock_obj
