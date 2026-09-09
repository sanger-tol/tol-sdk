# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer

from .broker import purge, queue_depth, wait_for_depth


QUEUE = 'notification'
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
            'notification_message',
            id_='poison-1',
            attributes={
                'body': {
                    'id': 'poison-1',
                    'type': 'notification',
                    'context': {'irrelevant': 'payload'}
                }
            }
        )
        list(datasource.insert_batch('notification_message', [message]))

        def exploding_handler(envelope):
            raise RuntimeError('handler blew up')

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {'notification': exploding_handler}
        )
        consumer.process_one()

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1

    def test_invalid_envelope_dead_letters(self, config, datasource):
        """
        A message that fails envelope validation is also dead-lettered.
        """
        message = datasource.data_object_factory(
            'notification_message',
            id_='poison-2',
            attributes={'body': {'not': 'an envelope'}}
        )
        list(datasource.insert_batch('notification_message', [message]))

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {}
        )
        consumer.process_one()

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1
