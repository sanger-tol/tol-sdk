# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.rabbitmq.connection import QueueSpec, RabbitmqConnection

from .broker import purge, queue_depth, wait_for_depth

APP_A_QUEUE = 'appa.notify'
APP_B_QUEUE = 'appb.notify'


@pytest.fixture(scope='module', autouse=True)
def declare_routing_topology(config):
    """Declare the two app queues with their topic bindings."""

    specs = [
        QueueSpec(name=APP_A_QUEUE, binding_keys=('notify.appa.*',)),
        QueueSpec(name=APP_B_QUEUE, binding_keys=('notify.appb.*',))
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
        'notification_message',
        id_=message_id,
        attributes={
            'body': {'n': 1},
            'routing_key': routing_key
        }
    )
    list(datasource.insert_batch('notification_message', [message]))


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
        """Any single-word subtype matches the '<category>.<app>.*' binding"""
        _publish(datasource, 'notify.appb.urgent', 'route-2')

        assert wait_for_depth(config, APP_B_QUEUE, 1) == 1
        assert queue_depth(config, APP_A_QUEUE) == 0

    def test_unmatched_key_is_dropped(self, config, datasource):
        """A key matching no binding reaches neither queue"""
        _publish(datasource, 'notify.nobody.x', 'route-3')

        assert queue_depth(config, APP_A_QUEUE) == 0
        assert queue_depth(config, APP_B_QUEUE) == 0
