# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import multiprocessing
import os
import time

import pytest

from tol.rabbitmq.connection import RabbitmqConnection

from . import fakes
from .broker import (
    publish_raw, purge,
    queue_depth,
    queue_info,
    wait_for_depth
)
from .constants import QUEUE, ROUTING_KEY


DEAD_QUEUE = f'{QUEUE}.dead'


@pytest.fixture(autouse=True)
def purge_dead_queue(config):
    """Purge the dead-letter queue before each test."""
    purge(config, DEAD_QUEUE)
    wait_for_depth(config, DEAD_QUEUE, 0)

    yield


def _get_then_crash(config):
    """Child process: take the message unacked, then die without closing."""
    connection = RabbitmqConnection(config)
    connection.connect()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        method, _, _ = connection.channel.basic_get(QUEUE, auto_ack=False)
        if method is not None:
            os._exit(0)
        time.sleep(0.2)
    os._exit(1)


def _crashed_delivery(config):
    """
    Returns True if a consumer received the message and then crashed;
    False once the broker stops serving it.
    """
    process = multiprocessing.Process(target=_get_then_crash, args=(config,))
    process.start()
    process.join(timeout=15)
    return process.exitcode == 0


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
            attributes={'message_type': 'poison'}
        )
        datasource.insert_batch('bus_message', [message])

        datasource.consume(
            {'poison': fakes.spec('RaisingHandler')},
            time_limit=5
        )

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1

    def test_invalid_envelope_dead_letters(self, config, datasource):
        """
        A message that fails envelope validation is also dead-lettered.
        """
        publish_raw(config, ROUTING_KEY, {'not': 'an envelope'})

        datasource.consume({}, time_limit=5)

        assert queue_depth(config, QUEUE) == 0
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1

    def test_queue_arguments(self, config):
        """App and dead queues are quorum with the expected limits."""
        main = queue_info(config, QUEUE)
        dead = queue_info(config, DEAD_QUEUE)

        assert main['type'] == 'quorum'
        assert main['arguments']['x-delivery-limit'] == 5
        assert main['arguments']['x-dead-letter-strategy'] == 'at-least-once'
        assert dead['type'] == 'quorum'
        assert dead['arguments']['x-max-length'] == 10_000

    def test_redelivery_after_crash_is_bounded(self, config):
        """
        A message whose consumer keeps dying before the ack is
        dead-lettered after the delivery limit, not redelivered forever.
        """
        publish_raw(config, ROUTING_KEY, {'not': 'acked'})

        deliveries = 0
        for _ in range(10):
            if not _crashed_delivery(config):
                break
            deliveries += 1

        assert deliveries == 6
        assert wait_for_depth(config, DEAD_QUEUE, 1) == 1
