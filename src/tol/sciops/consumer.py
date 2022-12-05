# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import signal
import sys

from lab_share_lib.rabbit.background_consumer import BackgroundConsumer
from lab_share_lib.types import RabbitServerDetails

import tol.sciops.configuration as config
from tol.sciops.response_processors import FeedbackProcessor, MessageProcessor

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Change the next line to also output pika mq logging
logging.getLogger('pika').propagate = False
LOGGER = logging.getLogger(__name__)


class SciOpsConsumer:
    """ Class that handles async consuming of response messages from Sci Ops """
    @property
    def rabbitmq_details(self):
        return self.__rabbitmq_details

    @property
    def is_healthy(self):
        return self._background_consumer.is_healthy if self._background_consumer else False

    def __init__(self, processor: MessageProcessor):
        """ Constructor """
        LOGGER.info('Initialising SciOps consumer')
        self.__rabbitmq_details = RabbitServerDetails(
            uses_ssl=config.RABBITMQ_USE_SSL,
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            username=config.RABBITMQ_USERNAME,
            password=config.RABBITMQ_PASSWORD,
            vhost=config.RABBITMQ_VHOST,
        )
        self.__processor = processor
        self.__background_consumer = None

    def start(self):
        LOGGER.info('Starting SciOps consumer')
        signal.signal(signal.SIGINT, self._signal_handler)
        self.__background_consumer = BackgroundConsumer(
            self.__rabbitmq_details, config.TOL_FEEDBACK_QUEUE, self.__processor.process_message
        )
        # Start and wait for messages
        self.__background_consumer.start()
        self.__background_consumer.join()

    def _signal_handler(self):
        LOGGER.info('Shutting down SciOps consumer')
        if self.__background_consumer:
            self.__background_consumer.stop()


if __name__ == '__main__':
    # TESTING ONLY...
    consumer = SciOpsConsumer(FeedbackProcessor())
    consumer.start()
