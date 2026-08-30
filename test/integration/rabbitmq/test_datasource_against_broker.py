# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import pytest
import requests

from tol.core import core_data_object
from tol.rabbitmq import (
    RabbitmqConfig,
    create_rabbitmq_datasource
)
from tol.rabbitmq.connection import RabbitmqConnection


@pytest.fixture(scope='module')
def config():
    return RabbitmqConfig.from_env()


@pytest.fixture(scope='module')
def datasource(config):
    ds = create_rabbitmq_datasource(config)
    core_data_object(ds)
    return ds


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


def _message(datasource, message_id, num):
    return datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': {'n': num}}
    )


class TestDataSourceAgainstBroker:
    def test_insert_then_get_list(self, datasource):
        objects = [_message(datasource, f'msg-{i}', i) for i in range(2)]

        results = list(datasource.insert('notification_message', objects))
        assert results == objects

        fetched = list(datasource.get_list('notification_message'))
        assert [obj.id for obj in fetched] == ['msg-0', 'msg-1']
        assert [obj.body for obj in fetched] == [{'n': 0}, {'n': 1}]

    def test_get_by_id(self, datasource):
        objects = [_message(datasource, f'msg-{i}', i) for i in range(2)]
        list(datasource.insert('notification_message', objects))

        fetched, missing = list(
            datasource.get_by_id(
                'notification_message',
                ['msg-1', 'unknown-id']
            )
        )

        assert fetched.id == 'msg-1'
        assert fetched.body == {'n': 1}
        assert missing is None

    def test_topology_declared(self, config):
        response = requests.get(
            f'{config.management_url}/api/queues/%2F/{config.queue}',
            auth=(config.username, config.password),
            timeout=10
        )

        assert response.status_code == 200
        assert response.json()['durable'] is True
