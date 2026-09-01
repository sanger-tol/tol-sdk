# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.rabbitmq.connection import QueueSpec, declare_topology


class TestDeclareTopology:
    def test_queue_with_dlq(self, mock_channel):
        specs = [
            QueueSpec(
                name='portal.notify',
                binding_keys=('notify.portal.*',)
            )
        ]

        declare_topology(
            mock_channel,
            'tol',
            specs,
            dlx='tol.dlx'
        )

        mock_channel.exchange_declare.assert_any_call(
            exchange='tol',
            exchange_type='topic',
            durable=True
        )
        mock_channel.exchange_declare.assert_any_call(
            exchange='tol.dlx',
            exchange_type='topic',
            durable=True
        )
        mock_channel.queue_declare.assert_any_call(
            queue='portal.notify',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'tol.dlx',
                'x-dead-letter-routing-key': 'dead.portal.notify'
            }
        )
        mock_channel.queue_bind.assert_any_call(
            queue='portal.notify',
            exchange='tol',
            routing_key='notify.portal.*'
        )
        mock_channel.queue_declare.assert_any_call(
            queue='portal.notify.dead',
            durable=True
        )
        mock_channel.queue_bind.assert_any_call(
            queue='portal.notify.dead',
            exchange='tol.dlx',
            routing_key='dead.portal.notify'
        )

    def test_no_dlq_when_disabled(self, mock_channel):
        specs = [
            QueueSpec(
                name='q',
                binding_keys=('k',),
                dead_letter=False
            )
        ]

        declare_topology(
            mock_channel,
            'tol',
            specs,
            dlx='tol.dlx'
        )

        mock_channel.queue_declare.assert_called_once_with(
            queue='q',
            durable=True,
            arguments=None
        )
