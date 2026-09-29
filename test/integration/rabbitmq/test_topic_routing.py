# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import DataSourceError
from tol.rabbitmq.connection import QueueSpec, RabbitmqConnection

from .broker import purge, queue_depth, wait_for_depth

APP_A_QUEUE = 'appa.notify'
APP_B_QUEUE = 'appb.notify'


@pytest.fixture(scope='module', autouse=True)
def declare_routing_topology(config):
    """Declare the two app queues with their topic bindings."""

    specs = [
        QueueSpec(name=APP_A_QUEUE, binding_keys=('notify.appa.#',)),
        QueueSpec(name=APP_B_QUEUE, binding_keys=('notify.appb.#',))
    ]

    with RabbitmqConnection(config, specs=specs):
        pass


@pytest.fixture(autouse=True)
def purge_app_queues(config):
    for queue in (APP_A_QUEUE, APP_B_QUEUE):
        purge(config, queue)
        wait_for_depth(config, queue, 0)

    yield


def _publish(datasource, routing_key, message_id):
    """Publish one message with the given routing key."""
    message = datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={
            'body': {'id': message_id, 'type': 'test', 'context': {}},
            'routing_key': routing_key
        }
    )
    datasource.insert_batch('bus_message', [message])


class TestTopicRouting:
    def test_message_routes_only_to_matching_app(
        self,
        config,
        datasource
    ):
        """
        A message published with routing key 'notify.appa.x' lands only on
        appa's queue, not appb's.
        """
        _publish(datasource, 'notify.appa.x', 'route-1')

        assert wait_for_depth(config, APP_A_QUEUE, 1) == 1
        assert queue_depth(config, APP_B_QUEUE) == 0

    def test_wildcard_subtype_matches(self, config, datasource):
        """Any subtype matches the '<category>.<app>.#' binding"""
        _publish(datasource, 'notify.appb.urgent', 'route-2')

        assert wait_for_depth(config, APP_B_QUEUE, 1) == 1
        assert queue_depth(config, APP_A_QUEUE) == 0

    def test_unmatched_key_is_rejected(self, config, datasource):
        """A key matching no binding raises 422 instead of vanishing"""
        with pytest.raises(DataSourceError) as exc_info:
            _publish(datasource, 'notify.nobody.x', 'route-3')

        assert exc_info.value.status_code == 422
        assert queue_depth(config, APP_A_QUEUE) == 0
        assert queue_depth(config, APP_B_QUEUE) == 0

    def test_multi_word_subtype_matches(self, config, datasource):
        """'#' matches subtypes spanning several words"""
        _publish(datasource, 'notify.appa.sample.received', 'route-4')

        assert wait_for_depth(config, APP_A_QUEUE, 1) == 1
        assert queue_depth(config, APP_B_QUEUE) == 0
