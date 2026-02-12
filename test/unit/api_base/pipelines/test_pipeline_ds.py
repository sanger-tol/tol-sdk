# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime
from unittest.mock import create_autospec

from flask.testing import FlaskClient

import pytest

from tol.api_base.misc import AuthContext
from tol.core import DataObject, DataSourceError
from tol.prefect import PrefectDataSource
from tol.sql import SqlDataSource


class TestRunningPipelinesWithDataSources:
    """
    `pipeline_steps_blueprint()` using stub `DataSource` mocks.
    """

    os.environ['UPLOAD_S3_BUCKET'] = 'some_bucket'

    def test__404(
        self,
        client: FlaskClient,
        ctx: AuthContext,
        sql_ds: SqlDataSource,
        role: str
    ):
        """
        no pipeline found -> raise 404 error
        """

        ctx.user_id = '1001'
        ctx.roles = [role]

        sql_ds.get_one.return_value = None

        with pytest.raises(DataSourceError) as e:
            client.post(
                '/run-pipeline',
                json={
                    'data': {
                        's3_bucket': 's3://bucket/path/to/file',
                        's3_filename': 'file.xlsx',
                        'spreadsheet_config': 'some_config',
                        'pipeline_id': '123123',
                        'destination': 'some_destination',
                        'dry_run': False
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

        ctx.user_id = '1001'
        ctx.roles = [role]

        sql_ds.data_object_factory = self.__do_factory

        sql_ds.get_one.side_effect = [
            self.__mock_pipeline('123123'),
            self.__mock_upload('123456'),
            self.__mock_pipeline_step('567890')
        ]

        sql_ds.insert.return_value = [self.__mock_upload('123456')]

        flow_params = {
            'upload_id': '123456',
            'pipeline_id': '123123',
            'dry_run': False,
        }

        prefect_ds.insert.return_value = [
            self.__do_factory(
                type_='pipeline_run',
                id_='run_123456',
                attributes={
                    'parameters': flow_params,
                },
            )
        ]

        response = client.post(
            '/run-pipeline',
            json={
                'data': {
                    's3_bucket': 's3://bucket/path/to/file',
                    's3_filename': 'file.xlsx',
                    'spreadsheet_config': 'some_config',
                    'pipeline_id': '123123',
                    'destination': 'some_destination',
                    'dry_run': False
                }
            }
        )

        assert response.status_code == 200
        assert response.json == {
            'flow_run_id': 'run_123456',
            'upload_id': '123456',
            'success': True
        }

        prefect_calls = prefect_ds.data_object_factory.call_args_list
        assert len(prefect_calls) == 1

        args, kwargs = prefect_calls[0]
        assert args[0] == 'flow_run'

        assert kwargs['attributes']['parameters']['pipeline_id'] == '123123'
        assert kwargs['attributes']['parameters']['upload_id'] == '123456'
        assert kwargs['attributes']['parameters']['dry_run'] is False

        assert prefect_ds.insert.call_count == 1

    def test_revalidate_upload__200(
        self,
        client: FlaskClient,
        ctx: AuthContext,
        sql_ds: SqlDataSource,
        prefect_ds: PrefectDataSource,
        role: str
    ):

        ctx.user_id = '1001'
        ctx.roles = [role]

        sql_ds.data_object_factory = self.__do_factory

        sql_ds.get_one.side_effect = [
            self.__mock_pipeline('123123'),
        ]

        upload = self.__mock_upload('123456')
        upload.validation_status = 'validation_system_error'
        sql_ds.get_list.return_value = [upload]

        prefect_ds.insert.return_value = [
            self.__do_factory(
                type_='flow_run',
                id_='run_123456',
                attributes={'parameters': {}},
            )
        ]

        response = client.post(
            '/run-pipeline/revalidate',
            json={
                'data': {
                    'upload_ids': ['123456']
                }
            }
        )

        assert response.status_code == 200
        assert response.json == {
            'success': True,
            'upload_and_flow_run_ids': [['123456', 'run_123456']]
        }

    def __do_factory(
        self,
        type_: str,
        id_: str = None,
        attributes: dict = {},
        **kwargs
    ) -> DataObject:

        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = type_
        mock_obj.id = id_ if id_ else 'mock_id'

        mock_obj.attributes = attributes
        for k, v in attributes.items():
            setattr(mock_obj, k, v)

        return mock_obj

    def __mock_pipeline(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'pipeline'
        mock_obj.id = id_

        mock_obj.name = 'Test Pipeline'
        mock_obj.config = {
            'source': 'some_source',
            'destination': 'some_destination'
        }

        mock_obj.attributes = {
            'name': mock_obj.name,
            'config': mock_obj.config
        }

        return mock_obj

    def __mock_upload(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'upload'
        mock_obj.id = id_

        attributes = {
            's3_bucket': 's3://bucket/path/to/file',
            's3_filename': 'file.xlsx',
            'spreadsheet_config': 'some_config',
            'pipeline_id': '123123',
            'destination': 'some_destination',
            'date_started': datetime.now().isoformat()
        }

        mock_obj.attributes = attributes
        for k, v in attributes.items():
            setattr(mock_obj, k, v)

        return mock_obj

    def __mock_pipeline_step(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'pipeline_step'
        mock_obj.id = id_

        attributes = {
            'name': 'Test Step',
            'config': {
                'source': 'some_source',
                'destination': 'some_destination'
            },
            'stage': '1',
            'step': '1'
        }

        mock_obj.attributes = attributes
        for k, v in attributes.items():
            setattr(mock_obj, k, v)

    def __mock_user(self, id_: str) -> DataObject:
        mock_obj: DataObject = create_autospec(DataObject)

        mock_obj.type = 'user'
        mock_obj.id = id_

        return mock_obj
