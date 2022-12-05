# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import uuid
from unittest import TestCase, mock

from lab_share_lib.constants import RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
from lab_share_lib.rabbit.avro_encoder import AvroEncoderBinary
from lab_share_lib.rabbit.basic_publisher import BasicPublisher

import tol.sciops.configuration as config
from tol.sciops.messages import CreateLabwareMessage
from tol.sciops.publisher import SciOpsPublisher


class TestSciOpsPublisher(TestCase):
    """ Unit tests for the SciOpsPublisher class """
    LOCALHOST = '127.0.0.1'

    @mock.patch('tol.sciops.publisher.SchemaRegistry')
    def test_init(self, mock_schema_registry):
        """ Test SciOpsPublisher construction """
        publisher = SciOpsPublisher()
        self.assertIsNotNone(publisher.registry)
        self.assertIsNotNone(publisher.rabbitmq_details)
        self.assertEqual(publisher.rabbitmq_details.uses_ssl, False)
        self.assertEqual(publisher.rabbitmq_details.host, self.LOCALHOST)
        self.assertEqual(publisher.rabbitmq_details.port, '5671')
        self.assertEqual(publisher.rabbitmq_details.username, 'psd')
        self.assertEqual(publisher.rabbitmq_details.password, 'psd')
        self.assertEqual(publisher.rabbitmq_details.vhost, 'tol')

    def test_create_publisher(self):
        publisher = SciOpsPublisher()
        result = publisher._create_publisher()
        self.assertIsInstance(result, BasicPublisher)

    def test_create_encoder(self):
        publisher = SciOpsPublisher()
        result = publisher._create_encoder('a-subject')
        self.assertIsInstance(result, AvroEncoderBinary)

    @mock.patch('tol.sciops.publisher.SciOpsPublisher._create_encoder')
    @mock.patch('tol.sciops.publisher.SciOpsPublisher._create_publisher')
    @mock.patch('tol.sciops.publisher.SchemaRegistry')
    def test_send_message(self, mock_schema_registry, mock_create_publisher, mock_create_encoder):
        """ Test sending a message """
        mock_basic_publisher = mock.Mock()
        mock_create_publisher.return_value = mock_basic_publisher
        create_msg = CreateLabwareMessage(
            message_uuid=str(uuid.uuid4()),
            message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
            labware_type='Plate12x8',
            labware_uuid=str(uuid.uuid4()),
            barcode='1',
            samples=[]
        )
        publisher = SciOpsPublisher()
        publisher.send_message(create_msg)
        mock_basic_publisher.publish_message.assert_called_once_with(
            config.RABBITMQ_EXCHANGE,
            config.RABBITMQ_ROUTING_KEY,
            mock.ANY,
            config.REDPANDA_CREATE_LABWARE_SUBJECT,
            mock.ANY,
            RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
        )
