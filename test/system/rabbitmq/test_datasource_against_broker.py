# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import requests

from .broker import MANAGEMENT_URL, peek_messages
from .constants import QUEUE


def _message(datasource, message_id, num):
    """Create a `bus_message` for this app."""
    return datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={'message_type': 'test', 'context': {'n': num}}
    )


class TestDataSourceAgainstBroker:
    def test_insert_then_peek(self, config, datasource):
        """
        Insert two messages and then fetch them via the management API.
        """
        objects = [_message(datasource, f'msg-{i}', i) for i in range(2)]

        results = list(datasource.insert('bus_message', objects))
        assert results == objects

        messages = peek_messages(config, QUEUE)
        ids = [m['properties']['message_id'] for m in messages]
        assert ids == ['msg-0', 'msg-1']
        assert [json.loads(m['payload'])['context'] for m in messages] == [
            {'n': 0}, {'n': 1}
        ]

    def test_insert_sets_amqp_properties(self, config, datasource):
        """Check the AMQP properties set on published messages."""
        list(datasource.insert(
            'bus_message', [_message(datasource, 'msg-props', 1)]
        ))

        (message, ) = peek_messages(config, QUEUE, count=1)

        properties = message['properties']

        assert properties['delivery_mode'] == 2
        assert properties['content_type'] == 'application/json'
        assert properties['type'] == 'test'
        assert properties['app_id'] == config.app_name
        assert json.loads(message['payload'])['source'] == config.app_name

    def test_topology_declared(self, config):
        """Check that the RabbitMQ topology has been declared."""
        response = requests.get(
            f'{MANAGEMENT_URL}/api/queues/%2F/{QUEUE}',
            auth=(config.username, config.password),
            timeout=10
        )

        assert response.status_code == 200
        assert response.json()['durable'] is True
