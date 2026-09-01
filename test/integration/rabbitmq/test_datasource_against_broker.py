# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import requests


def _message(datasource, message_id, num):
    """Create a notification message object."""
    return datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': {'n': num}}
    )


class TestDataSourceAgainstBroker:
    def test_insert_then_get_list(self, datasource):
        """
        Insert two notification messages and then fetch them with `get_list`
        """
        objects = [_message(datasource, f'msg-{i}', i) for i in range(2)]

        results = list(datasource.insert('notification_message', objects))
        assert results == objects

        fetched = list(datasource.get_list('notification_message'))
        assert [obj.id for obj in fetched] == ['msg-0', 'msg-1']
        assert [obj.body for obj in fetched] == [{'n': 0}, {'n': 1}]

    def test_get_by_id(self, datasource):
        """Fetch a notification message by its ID."""
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
        """Check that the RabbitMQ topology has been declared."""
        response = requests.get(
            f'{config.management_url}/api/queues/%2F/{config.queue}',
            auth=(config.username, config.password),
            timeout=10
        )

        assert response.status_code == 200
        assert response.json()['durable'] is True
