# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
from unittest import TestCase, mock
import lab_share_lib.rabbit.background_consumer as bconsumer
from tol.sciops.consumer import SciOpsConsumer
from tol.sciops.response_processors import NoOpProcessor


class TestSciOpsConsumer(TestCase):
    """ Unit tests for the SciOpsConsumer class """
    LOCALHOST = "127.0.0.1"

    def test_init(self):
        """ Test SciOpsConsumer construction """
        consumer = SciOpsConsumer(NoOpProcessor())
        self.assertIsNotNone(consumer.rabbitmq_details)
        self.assertEqual(consumer.rabbitmq_details.uses_ssl, False)
        self.assertEqual(consumer.rabbitmq_details.host, self.LOCALHOST)
        self.assertEqual(consumer.rabbitmq_details.port, "5671")
        self.assertEqual(consumer.rabbitmq_details.username, "psd")
        self.assertEqual(consumer.rabbitmq_details.password, "psd")
        self.assertEqual(consumer.rabbitmq_details.vhost, "tol")

    @mock.patch.object(bconsumer.BackgroundConsumer, "join")
    @mock.patch.object(bconsumer.BackgroundConsumer, "start")
    def test_start(self, mock_bconsumer_start, mock_bconsumer_join):
        consumer = SciOpsConsumer(NoOpProcessor())
        consumer.start()
        mock_bconsumer_start.assert_called_once()
        mock_bconsumer_join.assert_called_once()
