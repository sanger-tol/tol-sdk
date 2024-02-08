# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
from abc import ABCMeta, abstractmethod

from lab_share_lib.exceptions import TransientRabbitError
from lab_share_lib.processing.rabbit_message import RabbitMessage
from lab_share_lib.processing.rabbit_message_processor import ENCODERS
from lab_share_lib.rabbit.schema_registry import SchemaRegistry

import tol.sciops.configuration as config

LOGGER = logging.getLogger(__name__)


class MessageProcessor(object, metaclass=ABCMeta):
    """ Base class for response message processors """

    @property
    def registry(self):
        return self.__registry

    def __init__(self):
        self.__registry = SchemaRegistry(config.REDPANDA_URL, config.REDPANDA_API_KEY)

    def build_avro_encoder(self, encoder_type, subject):
        if encoder_type not in ENCODERS.keys():
            raise Exception(f'Encoder type {encoder_type} not recognised')

        return ENCODERS[encoder_type](self.__registry, subject)

    @abstractmethod
    def process_message(self, headers, body):
        pass

    def _unpack(self, headers, body) -> RabbitMessage:
        """ Helper method to decode a received feedback message """
        message = RabbitMessage(headers, body)
        message.decode(self.build_avro_encoder(message.encoder_type, message.subject))
        return message


class FeedbackProcessor(MessageProcessor):
    """ Handle incoming feedback messages """

    def process_message(self, headers, body):
        """
        This method should return true to ack the message and False to move it to dead letter
        """
        try:
            message = self._unpack(headers, body)
        except TransientRabbitError as ex:
            # Cause the consumer to restart and try this message again.
            # Ideally we will delay the consumer.
            LOGGER.error(f'Transient error while processing message: {ex.message}')
            raise
        except Exception as ex:
            LOGGER.error(
                f'Unrecoverable error while decoding RabbitMQ message: {type(ex)} {str(ex)}')
            return False  # Send the message to dead letters.

        if not message.contains_single_message:
            LOGGER.error('RabbitMQ message received containing multiple AVRO encoded messages.')
            return False  # Send the message to dead letters.

        LOGGER.info(f'Received queue feedback message: {str(message.message)}')
        return True


class NoOpProcessor(MessageProcessor):
    """ No operation dummy feedback processor for testing """

    def process_message(self, headers, body):
        return True
