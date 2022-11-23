# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
import sys
import logging
import uuid
import datetime
import tol.sciops.configuration as config
from lab_share_lib.rabbit.schema_registry import SchemaRegistry
from lab_share_lib.rabbit.basic_publisher import BasicPublisher
from lab_share_lib.rabbit.avro_encoder import AvroEncoderBinary
from lab_share_lib.types import RabbitServerDetails
from lab_share_lib.constants import RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
from tol.sciops.messages import LabwareMessage, CreateLabwareMessage, UpdateLabwareMessage, \
     Sample, Update
from tol.sciops.message_builder import MessageBuilder

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Change the next line to also output pika mq logging
logging.getLogger("pika").propagate = False
LOGGER = logging.getLogger(__name__)


class SciOpsPublisher:
    """ Class that handles sending of messages to Sci Ops """

    @property
    def registry(self):
        return self.__registry

    @property
    def rabbitmq_details(self):
        return self.__rabbitmq_details

    def __init__(self):
        """ Constructor """
        LOGGER.info("Initialising SciOps publisher")
        self.__registry = SchemaRegistry(config.REDPANDA_URL, config.REDPANDA_API_KEY)
        self.__rabbitmq_details = RabbitServerDetails(
            uses_ssl=config.RABBITMQ_USE_SSL,
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            username=config.RABBITMQ_USERNAME,
            password=config.RABBITMQ_PASSWORD,
            vhost=config.RABBITMQ_VHOST,
        )

    def _create_publisher(self) -> BasicPublisher:
        """ Create a new publisher instance for sending messages """
        return BasicPublisher(
            self.__rabbitmq_details,
            config.RABBITMQ_PUBLISH_RETRY_DELAY,
            config.RABBITMQ_PUBLISH_RETRIES
        )

    def _create_encoder(self, subject) -> AvroEncoderBinary:
        """ Create a message encoder """
        encoder = AvroEncoderBinary(self.__registry, subject)
        encoder.set_compression_codec("snappy")
        return encoder

    def send_message(self, msg_to_send: LabwareMessage):
        """ Send the given message """
        subject = msg_to_send.SUBJECT
        version = msg_to_send.VERSION
        built_msg = MessageBuilder.build_labware_message(msg_to_send)

        encoder = self._create_encoder(subject)
        encoded_message = encoder.encode([built_msg], version=version)

        publisher = self._create_publisher()
        LOGGER.info(f"Sending message {built_msg}")

        publisher.publish_message(
            config.RABBITMQ_EXCHANGE,
            config.RABBITMQ_ROUTING_KEY,
            encoded_message.body,
            subject,
            encoded_message.version,
            RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY,
        )


if __name__ == "__main__":
    # TESTING ONLY....
    LOGGER.info("About to publish messages")

    sample_uuid = str(uuid.uuid4())
    study_uuid = str(uuid.uuid4())
    labware_uuid = str(uuid.uuid4())

    create_msg = CreateLabwareMessage(
        message_uuid=str(uuid.uuid4()),
        message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
        labware_type="Plate12x8",
        labware_uuid=labware_uuid,
        barcode="1",
        samples=[
            Sample(
                sample_uuid=sample_uuid,
                study_uuid=study_uuid,
                sanger_sample_id="TestSample1",
                location="A1",
                supplier_sample_name="TestSample1SupplierName",
                volume="5",
                concentration="5",
                public_name="TestSample1PublicName",
                taxon_id="10090",
                common_name="Mus Musculus",
                donor_id="TestSample1",
                library_type="Library1",
                country_of_origin="United Kingdom",
                sample_collection_date_utc=datetime.datetime.now(datetime.timezone.utc)
            )
        ]
    )

    update_msg = UpdateLabwareMessage(
        message_uuid=str(uuid.uuid4()),
        message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
        labware_updates=[
            Update(
                uuid=labware_uuid,
                name="barcode",
                value="2"
            )
        ],
        sample_updates=[
            Update(
                uuid=sample_uuid,
                name="volume",
                value="6"
            )
        ]
    )

    publisher = SciOpsPublisher()
    publisher.send_message(create_msg)
    publisher.send_message(update_msg)

    LOGGER.info("Finished publishing messages")
