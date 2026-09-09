# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

"""Helpers for inspecting a real RabbitMQ broker in integration tests."""

import time

import requests


def queue_depth(config, queue):
    """Return the number of messages in the given queue."""
    response = requests.get(
        f'{config.management_url}/api/queues/%2F/{queue}',
        auth=(config.username, config.password),
        timeout=10
    )
    response.raise_for_status()
    return response.json().get('messages', 0)


def wait_for_depth(config, queue, expected, timeout=10):
    """
    Poll until the queue holds exactly 'expected' messages.

    Publishing is asynchronous from the client's perspective, so a
    one-shot depth check immediately after publish races the broker.
    Returns the depth once it equals 'expected; raises TimeoutError
    if that doesn't happen in time.

    We use the same monitoring in system tests.
    """
    deadline = time.monotonic() + timeout
    depth = queue_depth(config, queue)

    while depth != expected:
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f'queue {queue} held {depth} messages, '
                f'expected {expected} messages'
            )
        time.sleep(0.2)
        depth = queue_depth(config, queue)

    return depth


def purge(config, queue):
    """Delete all messages from the given queue."""
    requests.delete(
        f'{config.management_url}/api/queues/%2F/{queue}/contents',
        auth=(config.username, config.password),
        timeout=10
    )


def peek_messages(config, queue, count=10):
    """
    Fetch messages from the queue via the management API.

    ack_requeue_true puts them back afterwards, so this is
    non-destructive (though it marks them redelivered - never
    assert on that flag).
    """
    response = requests.post(
        f'{config.management_url}/api/queues/%2F/{queue}/get',
        json={
            'count': count,
            'ackmode': 'ack_requeue_true',
            'encoding': 'auto'
        },
        auth=(config.username, config.password),
        timeout=10
    )
    response.raise_for_status()
    return response.json()
