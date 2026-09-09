# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from .broker import peek_messages

import requests

QUEUE = 'notification'


def _message(datasource, message_id, num):
    """Create a notification message object."""
    return datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': {'n': num}}
    )


class TestDataSourceAgainstBroker:
    def test_insert_then_get_list(self, config, datasource):
        """
        Insert two notification messages and then fetch them
        via the management API.
        """
        objects = [_message(datasource, f'msg-{i}', i) for i in range(2)]

        results = list(datasource.insert('notification_message', objects))
        assert results == objects

        messages = peek_messages(config, QUEUE)
        ids = [m['properties']['message_id'] for m in messages]
        assert ids == ['msg-0', 'msg-1']
        assert [json.loads(m['payload']) for m in messages] == [
            {'n': 0}, {'n': 1}
        ]

    def test_insert_marks_persistent_and_json(self, config, datasource):
        """Check the AMQP properties set on published messages."""
        objects = [_message(datasource, 'msg-props', 1)]
        list(datasource.insert('notification_message', objects))

        (message, ) = peek_messages(config, QUEUE, count=1)
        properties = message['properties']

        assert properties['delivery_mode'] == 2
        assert properties['content_type'] == 'application/json'

    def test_topology_declared(self, config):
        """Check that the RabbitMQ topology has been declared."""
        response = requests.get(
            f'{config.management_url}/api/queues/%2F/{QUEUE}',
            auth=(config.username, config.password),
            timeout=10
        )

        assert response.status_code == 200
        assert response.json()['durable'] is True
