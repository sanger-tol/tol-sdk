# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

import requests

from tol.core import core_data_object
from tol.rabbitmq import RabbitmqConfig, create_rabbitmq_datasource
from tol.rabbitmq.connection import RabbitmqConnection


@pytest.fixture(scope='module')
def config():
    """Return a `RabbitmqConfig` instance from environment variables"""
    return RabbitmqConfig.from_env()


@pytest.fixture(scope='module')
def datasource(config):
    """Return a `RabbitmqDataSource` instance"""
    ds = create_rabbitmq_datasource(config)
    core_data_object(ds)
    return ds


@pytest.fixture(autouse=True)
def purge_queue(config):
    """Purge the RabbitMQ queue before each test"""
    requests.delete(
        f'{config.management_url}'
        f'/api/queues/%2F/{config.queue}/contents',
        auth=(config.username, config.password),
        timeout=10
    )

    yield


@pytest.fixture(scope='module', autouse=True)
def declare_topology(config):
    """
    Declare the RabbitMQ topology (exchange, queue, and binding)
    before any tests run.
    """
    with RabbitmqConnection(config):
        pass
