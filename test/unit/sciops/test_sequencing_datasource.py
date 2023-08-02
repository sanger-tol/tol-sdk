# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# from typing import Dict, Iterable
import datetime
import uuid
from unittest import TestCase, mock


from lab_share_lib.constants import RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
from lab_share_lib.rabbit.avro_encoder import AvroEncoderBinary
from lab_share_lib.rabbit.basic_publisher import BasicPublisher


from tol.core import DataSourceError, core_data_object
from tol.sciops import SequencingDataSource
from tol.sciops.messages import CreateLabwareMessage


class MockSequencingDataSource(SequencingDataSource):
    pass


def mock_sequencing_data_source() -> SequencingDataSource:
    sds = MockSequencingDataSource(
        {
            'redpanda_url': 'https://redpanda.uat.tol.psd.sanger.ac.uk',
            'redpanda_api_key': 'redpanda-tol',
            'rabbitmq_host': 'rabbitmq.uat.tol.psd.sanger.ac.uk',
            'rabbitmq_port': '5671',
            'rabbitmq_username': 'tol',
            'rabbitmq_password': 'password',
            'rabbitmq_vhost': 'tol',
            'rabbitmq_exchange': 'tol-team.tol',
            'rabbitmq_routing_key': 'crud.1',
            'rabbitmq_use_ssl': 'True',
            'rabbitmq_publish_retry_delay': '5',
            'rabbitmq_publish_retries': '36',
            'tol_feedback_queue': 'tol.feedback'
        }
    )
    core_data_object_mock = core_data_object(sds)
    return core_data_object_mock, sds


class TestSequencingDataSource(TestCase):
    @mock.patch('tol.sciops.sequencing_datasource.SchemaRegistry')
    def test_init(self, mock_schema_registry):
        """ Test SciOpsPublisher construction """
        _, sds = mock_sequencing_data_source()
        self.assertIsNotNone(sds.registry)
        self.assertIsNotNone(sds.rabbitmq_details)
        self.assertEqual(sds.rabbitmq_details.uses_ssl, 'True')
        self.assertEqual(sds.rabbitmq_details.host, 'rabbitmq.uat.tol.psd.sanger.ac.uk')
        self.assertEqual(sds.rabbitmq_details.port, '5671')
        self.assertEqual(sds.rabbitmq_details.username, 'tol')
        self.assertEqual(sds.rabbitmq_details.password, 'password')
        self.assertEqual(sds.rabbitmq_details.vhost, 'tol')

    def test_create_publisher(self):
        _, sds = mock_sequencing_data_source()
        result = sds._create_publisher()
        self.assertIsInstance(result, BasicPublisher)

    def test_create_encoder(self):
        _, sds = mock_sequencing_data_source()
        result = sds._create_encoder('a-subject')
        self.assertIsInstance(result, AvroEncoderBinary)

    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_encoder')
    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_publisher')
    @mock.patch('tol.sciops.sequencing_datasource.SchemaRegistry')
    def test_send_message_ok(self, mock_schema_registry, mock_create_publisher,
                             mock_create_encoder):
        _, sds = mock_sequencing_data_source()

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

        sds._send_message(create_msg)
        mock_create_publisher.return_value.publish_message.assert_called_once_with(
            sds.rabbitmq_exchange,
            sds.rabbitmq_routing_key,
            mock.ANY,
            'create-labware',
            mock.ANY,
            RABBITMQ_HEADER_VALUE_ENCODER_TYPE_BINARY
        )

    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_encoder')
    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_publisher')
    @mock.patch('tol.sciops.sequencing_datasource.SchemaRegistry')
    def test_send_message_fail(self, mock_schema_registry, mock_create_publisher,
                               mock_create_encoder):
        _, sds = mock_sequencing_data_source()

        mock_create_publisher.side_effect = Exception()

        create_msg = CreateLabwareMessage(
            message_uuid=str(uuid.uuid4()),
            message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
            labware_type='Plate12x8',
            labware_uuid=str(uuid.uuid4()),
            barcode='1',
            samples=[]
        )

        with self.assertRaises(DataSourceError):
            sds._send_message(create_msg)

    def test_split_objects_into_plates(self):
        core_data_object, sds = mock_sequencing_data_source()

        samples = [
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '1',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample1',
                    'location': 'A1',
                }
            ),
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '1',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample2',
                    'location': 'B1',
                }
            ),
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '2',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample3',
                    'location': 'C1',
                }
            )
        ]

        split_samples = sds.split_objects_into_plates(samples)
        # resulting dict has barcode as keys
        self.assertEqual(set(split_samples.keys()), {'1', '2'})

        self.assertEqual(split_samples['1'], [samples[0], samples[1]])
        self.assertEqual(split_samples['2'], [samples[2]])

    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_encoder')
    @mock.patch('tol.sciops.sequencing_datasource.SequencingDataSource._create_publisher')
    @mock.patch('tol.sciops.sequencing_datasource.SchemaRegistry')
    def test_add_plate_ok(self, mock_schema_registry, mock_create_publisher,
                          mock_create_encoder):
        core_data_object, sds = mock_sequencing_data_source()

        labware_type = 'Plate12x8'
        labware_uuid = str(uuid.uuid4())

        samples = [
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '1',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample1',
                    'location': 'A1',
                    'supplier_sample_name': 'TestSample1SupplierName',
                    'volume': '5',
                    'concentration': '5',
                    'public_name': 'TestSample1PublicName',
                    'taxon_id': '10090',
                    'common_name': 'Mus Musculus',
                    'donor_id': 'TestSample1',
                    'library_type': 'Library1',
                    'country_of_origin': 'United Kingdom',
                    'sample_collection_date_utc': datetime.datetime.now(datetime.timezone.utc),
                    'cost_code': str(uuid.uuid4()),
                    'genome_size': '3',
                    'accession_number': 'A1234',
                    'sheared_femto_fragment_size': '5',
                    'post_spri_concentration': '10',
                    'post_spri_volume': '20',
                    'final_nano_drop_280': '5',
                    'final_nano_drop_230': '6',
                    'final_nano_drop': '7',
                    'shearing_and_qc_comments': 'Comments1',
                    'date_submitted_utc': datetime.datetime.now(datetime.timezone.utc),
                    'priority_level': 'Medium',
                    'date_required_by': 'Long Read',
                    'reason_for_priority': 'Reason for priority'
                }
            ),
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '1',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample3',
                    'location': 'A1',
                    'supplier_sample_name': 'TestSample3SupplierName',
                    'volume': '5',
                    'concentration': '5',
                    'public_name': 'TestSample1PublicName',
                    'taxon_id': '10090',
                    'common_name': 'Mus Musculus',
                    'donor_id': 'TestSample1',
                    'library_type': 'Library1',
                    'country_of_origin': 'United Kingdom',
                    'sample_collection_date_utc': datetime.datetime.now(datetime.timezone.utc),
                    'cost_code': str(uuid.uuid4()),
                    'genome_size': '5',
                    'accession_number': 'A1290',
                    'sheared_femto_fragment_size': '5',
                    'post_spri_concentration': '10',
                    'post_spri_volume': '20',
                    'final_nano_drop_280': '5',
                    'final_nano_drop_230': '6',
                    'final_nano_drop': '7',
                    'shearing_and_qc_comments': 'Comments3',
                    'date_submitted_utc': datetime.datetime.now(datetime.timezone.utc),
                    'priority_level': 'High',
                    'date_required_by': 'Long Read',
                    'reason_for_priority': 'Reason for high priority'
                }
            )
        ]

        result = sds.add_plate('sequencing_sample', objects=samples, barcode='1',
                               labware_type=labware_type, labware_uuid=labware_uuid)
        self.assertTrue(result)

    def test_add_plate_fail(self):
        core_data_object, sds = mock_sequencing_data_source()

        labware_type = 'Plate12x8'
        labware_uuid = str(uuid.uuid4())

        samples = [
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '1',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample1',
                    'location': 'A1',
                }
            ),
            core_data_object(
                'sequencing_sample',
                data={
                    'barcode': '2',
                    'sample_uuid': str(uuid.uuid4()),
                    'study_uuid': str(uuid.uuid4()),
                    'sanger_sample_id': 'TestSample3',
                    'location': 'A1'
                }
            )
        ]

        with self.assertRaises(ValueError):
            sds.add_plate('sequencing_sample', objects=samples, barcode='1',
                          labware_type=labware_type, labware_uuid=labware_uuid)
