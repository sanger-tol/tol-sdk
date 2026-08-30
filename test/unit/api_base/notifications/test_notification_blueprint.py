# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

from flask import Flask

import pytest

from tol.api_base.notification import notification_blueprint
from tol.core import ErrorObject
from tol.core.datasource_error import DataSourceError
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource


@pytest.fixture
def mock_ds():
    """Create a mock RabbitmqDataSource for testing purposes."""
    return create_autospec(RabbitmqDataSource, spec_set=True)


@pytest.fixture
def client(mock_ds):
    """
    Create a Flask test client with the notification blueprint registered.
    """
    app = Flask(__name__)
    app.testing = True
    app.register_blueprint(notification_blueprint(mock_ds))
    return app.test_client()


def _body(**overrides):
    """Return a base notification request dictionary."""
    base = {
        'id': 'notification-1',
        'channels': ['email'],
        'type': 'test_type',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    base.update(overrides)
    return base


class TestNotify:
    def test_valid_request_returns_202(self, client, mock_ds):
        """
        Test that a valid notification request returns a 202 status code.
        """
        message = Mock()
        mock_ds.data_object_factory.return_value = message
        mock_ds.insert_batch.return_value = [message]

        response = client.post('/notification', json=_body())

        assert response.status_code == 202
        assert response.get_json() == {'notification_id': 'notification-1'}

        mock_ds.data_object_factory.assert_called_once()
        factory_kwargs = mock_ds.data_object_factory.call_args

        assert factory_kwargs.args[0] == 'notification_message'
        assert factory_kwargs.kwargs['id_'] == 'notification-1'
        assert factory_kwargs.kwargs['attributes']['body']['id'] == (
            'notification-1'
        )

        mock_ds.insert_batch.assert_called_once_with(
            'notification_message',
            [message]
        )

    def test_empty_recipients_raises_400(self, client, mock_ds):
        """
        Test that a notification request
        with empty recipients raises a 400 error.
        """
        with pytest.raises(DataSourceError) as exc_info:
            client.post(
                '/notification',
                json=_body(recipients=[])
            )

        assert exc_info.value.status_code == 400
        mock_ds.insert_batch.assert_not_called()

    def test_missing_id_raises_400(self, client, mock_ds):
        """
        Test that a notification request missing
        the 'id' field raises a 400 error.
        """
        body = _body()
        del body['id']

        with pytest.raises(DataSourceError) as exc_info:
            client.post('/notification', json=body)

        assert exc_info.value.status_code == 400
        mock_ds.insert_batch.assert_not_called()

    def test_non_json_raises_400(self, client, mock_ds):
        """
        Test that a non-JSON notification request raises a 400 error.
        """
        with pytest.raises(DataSourceError) as exc_info:
            client.post(
                '/notification',
                data='not json',
                content_type='text/plain'
            )

        assert exc_info.value.status_code == 400
        mock_ds.insert_batch.assert_not_called()

    def test_publish_failure_raises_500(self, client, mock_ds):
        """
        Test that a publish failure raises a 500 error.
        """
        mock_ds.insert_batch.return_value = [
            ErrorObject(
                details={'exception': 'broker down'},
                object_type='notification_message',
                object_id='notification-1',
                http_code=500
            )
        ]

        with pytest.raises(DataSourceError) as exc_info:
            client.post('/notification', json=_body())

        assert exc_info.value.status_code == 500
