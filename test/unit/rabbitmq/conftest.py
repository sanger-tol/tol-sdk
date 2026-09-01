# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from pika.adapters.blocking_connection import BlockingChannel

import pytest

from tol.rabbitmq.config import RabbitmqConfig


@pytest.fixture
def config():
    """Fixture to provide a RabbitmqConfig for testing."""
    return RabbitmqConfig(
        host='rabbitmq-host',
        port=5672,
        username='test-user',
        password='test-password',
        vhost='test-vhost',
        exchange='notification',
        queue='notification',
        routing_key='notification',
        management_url='http://rabbitmq-mgmt:15672',
    )


@pytest.fixture
def mock_channel():
    """Create a mock BlockingChannel for testing."""
    return create_autospec(BlockingChannel, spec_set=True)
