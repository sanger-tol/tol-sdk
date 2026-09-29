# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

import requests

from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer

from .broker import (
    MANAGEMENT_URL,
    publish_raw, purge,
    queue_depth,
    wait_for_depth
)
from .constants import CREATED_AT, QUEUE, ROUTING_KEY, SOURCE


DEAD_QUEUE = f'{QUEUE}.dead'


@pytest.fixture(autouse=True)
def purge_dead_queue(config):
    """Purge the dead-letter queue before each test."""
    purge(config, DEAD_QUEUE)
    wait_for_depth(config, DEAD_QUEUE, 0)

    yield


class TestDeadLetterQueue:
    def test_failing_handler_dead_letter_message(
        self,
        config,
        datasource
    ):
        """
        A message whose handler raises is nacked with requeue=False
        and lands on the dead-letter queue.
        """
        message = datasource.data_object_factory(
            'bus_message',
            id_='poison-1',
            attributes={
                'body': {
                    'id': 'poison-1',
                    'type': 'poison',
                    'source': SOURCE,
                    'created_at': CREATED_AT,
                    'context': {}},
                'routing_key': ROUTING_KEY
            }
        )
        datasource.insert_batch('bus_message', [message])

        def exploding_handler(envelope):
            raise RuntimeError('handler blew up')

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {'poison': exploding_handler}
        )
        assert consumer.process_one()

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1

    def test_invalid_envelope_dead_letters(self, config, datasource):
        """
        A message that fails envelope validation is also dead-lettered.
        """
        publish_raw(config, ROUTING_KEY, {'not': 'an envelope'})

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {}
        )
        assert consumer.process_one()

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1

    def test_dead_queue_is_bounded(self, config):
        """The dead-letter queue is declared with a max length."""
        response = requests.get(
            f'{MANAGEMENT_URL}/api/queues/%2F/{DEAD_QUEUE}',
            auth=(config.username, config.password),
            timeout=10
        )
        response.raise_for_status()

        assert response.json()['arguments']['x-max-length'] == 10_000
