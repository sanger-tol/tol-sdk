# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

import requests

from tol.core import core_data_object
from tol.rabbitmq import (
    NotificationRequest,
    RabbitmqConfig,
    create_rabbitmq_datasource
)
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import NotificationConsumer
from tol.rabbitmq.schema import NotificationChannel


@pytest.fixture(scope='module')
def config():
    return RabbitmqConfig.from_env()


@pytest.fixture(scope='module')
def datasource(config):
    ds = create_rabbitmq_datasource(config)
    core_data_object(ds)
    return ds


@pytest.fixture
def received():
    return []


@pytest.fixture(autouse=True)
def purge_queue(config):
    requests.delete(
        f'{config.management_url}'
        f'/api/queues/%2F/{config.queue}/contents',
        auth=(config.username, config.password),
        timeout=10
    )

    yield


@pytest.fixture(scope='module', autouse=True)
def declare_topology(config):
    with RabbitmqConnection(config):
        pass


def _queue_depth(config):
    response = requests.get(
        f'{config.management_url}/api/queues/%2F/{config.queue}',
        auth=(config.username, config.password),
        timeout=10
    )
    response.raise_for_status()
    return response.json().get('messages', 0)


def _publish(datasource, body, message_id):
    message = datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': body}
    )
    list(datasource.insert_batch('notification_message', [message]))


class TestConsumerAgainstBroker:
    def test_valid_request_dispatches_and_acks(
        self,
        config,
        datasource,
        received
    ):
        request = NotificationRequest.model_validate({
            'id': 'notification-1',
            'channels': ['email', 'slack'],
            'type': 'test_type',
            'recipients': [
                {'email': 'test1@example.com'},
                {'user_id': 'user_2'}
            ],
            'context': {'key': 'value'}
        })

        _publish(
            datasource,
            request.model_dump(mode='json'),
            'notification-1'
        )

        dispatchers = {
            NotificationChannel.EMAIL: received.append,
            NotificationChannel.SLACK: received.append
        }

        consumer = NotificationConsumer(
            RabbitmqConnection(config),
            config.queue,
            dispatchers
        )

        consumer.process_one()

        assert len(received) == 4
        assert {d.notification_id for d in received} == {'notification-1'}
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }
        assert len({d.delivery_id for d in received}) == 4
        assert _queue_depth(config) == 0

    def test_invalid_payload_nacked(
        self,
        config,
        datasource,
        received
    ):
        _publish(datasource, {'not': 'a notification'}, 'bad-1')

        consumer = NotificationConsumer(
            RabbitmqConnection(config),
            config.queue,
            {NotificationChannel.EMAIL: received.append}
        )

        consumer.process_one()

        assert received == []
        assert _queue_depth(config) == 0
