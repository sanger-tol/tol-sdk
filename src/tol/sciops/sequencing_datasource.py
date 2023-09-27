# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import logging
import sys
import uuid
from collections.abc import Mapping
from functools import cache
from typing import Dict, Iterable, Iterator

from lab_share_lib.constants import RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
from lab_share_lib.rabbit.avro_encoder import AvroEncoderBinary
from lab_share_lib.rabbit.basic_publisher import BasicPublisher
from lab_share_lib.rabbit.schema_registry import SchemaRegistry
from lab_share_lib.types import RabbitServerDetails

from tol.sciops.message_builder import MessageBuilder
from tol.sciops.messages import CreateLabwareMessage, LabwareMessage, Sample

from ..core import (
    DataObject,
    DataSource,
    DataSourceError
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Change the next line to also output pika mq logging
logging.getLogger('pika').propagate = False
LOGGER = logging.getLogger(__name__)


class SequencingDataSource(DataSource):
    @property
    def registry(self):
        return self.__registry

    @property
    def rabbitmq_details(self):
        return self.__rabbitmq_details

    def __init__(self, config: Dict):
        super().__init__(config, expected=['redpanda_url', 'redpanda_api_key', 'rabbitmq_host',
                                           'rabbitmq_port', 'rabbitmq_username',
                                           'rabbitmq_password', 'rabbitmq_vhost',
                                           'rabbitmq_exchange', 'rabbitmq_routing_key',
                                           'rabbitmq_use_ssl', 'rabbitmq_publish_retry_delay',
                                           'rabbitmq_publish_retries', 'tol_feedback_queue'])
        self._initialise_rabbitmq()

    def _initialise_rabbitmq(self):
        LOGGER.info('Initialising SciOps publisher')
        self.__registry = SchemaRegistry(self.redpanda_url, self.redpanda_api_key)
        self.__rabbitmq_details = RabbitServerDetails(
            uses_ssl=self.rabbitmq_use_ssl,
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            username=self.rabbitmq_username,
            password=self.rabbitmq_password,
            vhost=self.rabbitmq_vhost,
        )

    def _create_publisher(self) -> BasicPublisher:
        """ Create a new publisher instance for sending messages """
        return BasicPublisher(
            self.__rabbitmq_details,
            self.rabbitmq_publish_retry_delay,
            self.rabbitmq_publish_retries
        )

    def _create_encoder(self, subject) -> AvroEncoderBinary:
        """ Create a message encoder """
        encoder = AvroEncoderBinary(self.__registry, subject)
        encoder.set_compression_codec('snappy')
        return encoder

    def _send_message(self, msg_to_send: LabwareMessage):
        """ Send the given message """
        subject = msg_to_send.SUBJECT
        version = msg_to_send.VERSION
        built_msg = MessageBuilder.build_labware_message(msg_to_send)

        encoder = self._create_encoder(subject)
        encoded_message = encoder.encode([built_msg], version=version)

        try:
            publisher = self._create_publisher()
            LOGGER.info(f'Sending message {built_msg}')

            publisher.publish_message(
                self.rabbitmq_exchange,
                self.rabbitmq_routing_key,
                encoded_message.body,
                subject,
                encoded_message.version,
                RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY,
            )
        except Exception:
            raise DataSourceError('Unable to publish message')

    def split_objects_into_plates(self, objects):
        """ Separates the samples based on their barcode """
        separated_data = {}
        for obj in objects:
            barcode = obj.barcode
            if barcode not in separated_data:
                separated_data[barcode] = []
            separated_data[barcode].append(obj)
        return separated_data

    def _send_plate_to_sciops(
            self,
            samples: Iterable[DataObject],
            barcode: str,
            labware_type: str,
            labware_uuid: str
    ) -> None:
        """ Creates and sends the message in LabwareMessage format """
        create_msg = CreateLabwareMessage(
            message_uuid=str(uuid.uuid4()),
            message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
            barcode=barcode,
            labware_type=labware_type,
            labware_uuid=labware_uuid,
            samples=[
                Sample(
                    **{k: v for k, v in sample.attributes.items()
                       if k != 'barcode'}
                )
                for sample in samples
            ]
        )

        publisher = self
        publisher._send_message(create_msg)

    def add_plate(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        barcode: str,
        labware_type: str,
        labware_uuid: str
    ) -> None:
        """ Checks whether all samples belong to the same plate and sends message """
        first_barcode = objects[0].barcode
        for obj in objects:
            if obj.barcode != first_barcode:
                raise ValueError('Samples should have the same barcode')

        self._send_plate_to_sciops(samples=objects, barcode=barcode,
                                   labware_type=labware_type, labware_uuid=labware_uuid)
        return True

    @property
    def supported_types(self):
        return ['sequencing_sample']

    @property
    @cache
    def attribute_types(self) -> Dict:

        class AttributeTypesDict(Mapping[str, dict[str, str]]):
            def __getitem__(self, __k: str) -> dict[str, str]:
                if __k != 'sequencing_sample':
                    raise DataSourceError(
                        f'{__k} objects are not supported'
                    )
                return {
                    'barcode': 'str',
                    'sample_uuid': 'str',
                    'study_uuid': 'str',
                    'sanger_sample_id': 'str',
                    'location': 'str',
                    'supplier_sample_name': 'str',
                    'volume': 'str',
                    'concentration': 'str',
                    'public_name': 'str',
                    'taxon_id': 'str',
                    'common_name': 'str',
                    'donor_id': 'str',
                    'library_type': 'str',
                    'country_of_origin': 'str',
                    'sample_collection_date_utc': 'datetime',
                    'cost_code': 'str',
                    'genome_size': 'str',
                    'accession_number': 'str',
                    'sheared_femto_fragment_size': 'str',
                    'post_spri_concentration': 'str',
                    'post_spri_volume': 'str',
                    'final_nano_drop_280': 'str',
                    'final_nano_drop_230': 'str',
                    'final_nano_drop': 'str',
                    'shearing_and_qc_comments': 'str',
                    'date_submitted_utc': 'datetime',
                    'priority_level': 'str',
                    'date_required_by': 'str',
                    'reason_for_priority': 'str'
                }

            def __len__(self) -> int:
                return 1

            def __iter__(self) -> Iterator[str]:
                return iter(['sequencing_sample'])

        return AttributeTypesDict()
