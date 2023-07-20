# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import uuid
from unittest import TestCase

from tol.sciops.message_builder import MessageBuilder
from tol.sciops.messages import CreateLabwareMessage, Sample, Update, UpdateLabwareMessage


class TestMessageBuilder(TestCase):
    """ Unit tests for the message_builder class """

    def test_build_create_labware_message(self):
        """ Test the _build_create_labware_message method"""
        message_uuid = str(uuid.uuid4())
        sample_uuid = str(uuid.uuid4())
        study_uuid = str(uuid.uuid4())
        labware_uuid = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)
        msg = CreateLabwareMessage(
            message_uuid=message_uuid,
            message_create_date_utc=now,
            labware_type='Plate12x8',
            labware_uuid=labware_uuid,
            barcode='1',
            samples=[
                Sample(
                    sample_uuid=sample_uuid,
                    study_uuid=study_uuid,
                    sanger_sample_id='TestSample1',
                    location='A1',
                    supplier_sample_name='TestSample1SupplierName',
                    volume='2.5',
                    concentration='5',
                    public_name='TestSample1PublicName',
                    taxon_id='10090',
                    common_name='Mus Musculus',
                    donor_id='TestSample1',
                    library_type='Library1',
                    country_of_origin='United Kingdom',
                    sample_collection_date_utc=now,
                    cost_code='costCode',
                    genome_size='3',
                    accession_number='A1234',
                    sheared_femto_fragment_size='5',
                    post_spri_concentration='10',
                    post_spri_volume='20',
                    final_nano_drop_280='5',
                    final_nano_drop_230='6',
                    final_nano_drop='7',
                    shearing_and_qc_comments='Comments',
                    date_submitted_utc=now,
                    priority_level='Medium',
                    date_required_by='Long Read',
                    reason_for_priority='Reason for priority'
                )
            ]
        )
        result = MessageBuilder._build_create_labware_message(msg)
        self.assertEqual(result['messageUuid'].decode(), message_uuid)
        self.assertIsNotNone(result['messageCreateDateUtc'])
        labware = result['labware']
        self.assertIsNotNone(labware)
        self.assertEqual(labware['labwareType'], 'Plate12x8')
        self.assertEqual(labware['labwareUuid'].decode(), labware_uuid)
        self.assertEqual(labware['barcode'], '1')
        samples = result['labware']['samples']
        self.assertEqual(samples[0]['sampleUuid'].decode(), sample_uuid)
        self.assertEqual(samples[0]['studyUuid'].decode(), study_uuid)
        self.assertEqual(samples[0]['sangerSampleId'], 'TestSample1')
        self.assertEqual(samples[0]['location'], 'A1')
        self.assertEqual(samples[0]['supplierSampleName'], 'TestSample1SupplierName')
        self.assertEqual(samples[0]['volume'], '2.5')
        self.assertEqual(samples[0]['concentration'], '5')
        self.assertEqual(samples[0]['publicName'], 'TestSample1PublicName')
        self.assertEqual(samples[0]['taxonId'], '10090')
        self.assertEqual(samples[0]['commonName'], 'Mus Musculus')
        self.assertEqual(samples[0]['donorId'], 'TestSample1')
        self.assertEqual(samples[0]['libraryType'], 'Library1')
        self.assertEqual(samples[0]['countryOfOrigin'], 'United Kingdom')
        self.assertIsNotNone(samples[0]['sampleCollectionDateUtc'])
        self.assertEqual(samples[0]['costCode'], 'costCode')
        self.assertEqual(samples[0]['genomeSize'], '3')
        self.assertEqual(samples[0]['accessionNumber'], 'A1234')
        self.assertEqual(samples[0]['shearedFemtoFragmentSize'], '5')
        self.assertEqual(samples[0]['postSPRIConcentration'], '10')
        self.assertEqual(samples[0]['postSPRIVolume'], '20')
        self.assertEqual(samples[0]['finalNanoDrop280'], '5')
        self.assertEqual(samples[0]['finalNanoDrop230'], '6')
        self.assertEqual(samples[0]['finalNanoDrop'], '7')
        self.assertEqual(samples[0]['shearingAndQCComments'], 'Comments')
        self.assertIsNotNone(samples[0]['dateSubmittedUTC'])
        self.assertEqual(samples[0]['priorityLevel'], 'Medium')
        self.assertEqual(samples[0]['dateRequiredBy'], 'Long Read')
        self.assertEqual(samples[0]['reasonForPriority'], 'Reason for priority')

    def test_build_create_labware_message__sparse(self):
        """ Test the _build_create_labware_message method  with empty fields """
        message_uuid = str(uuid.uuid4())
        sample_uuid = str(uuid.uuid4())
        study_uuid = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)
        msg = CreateLabwareMessage(
            message_uuid=message_uuid,
            message_create_date_utc=now,
            barcode='1',
            samples=[
                Sample(
                    sample_uuid=sample_uuid,
                    study_uuid=study_uuid,
                    sanger_sample_id='TestSample1',
                    sample_collection_date_utc=now
                )
            ]
        )
        result = MessageBuilder._build_create_labware_message(msg)
        self.assertEqual(result['messageUuid'].decode(), message_uuid)
        self.assertIsNotNone(result['messageCreateDateUtc'])
        labware = result['labware']
        self.assertIsNotNone(labware)
        self.assertEqual(labware['barcode'], '1')
        samples = result['labware']['samples']
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]['sampleUuid'].decode(), sample_uuid)
        self.assertEqual(samples[0]['studyUuid'].decode(), study_uuid)
        self.assertEqual(samples[0]['sangerSampleId'], 'TestSample1')
        self.assertIsNone(samples[0].get('taxonId'))
        self.assertIsNotNone(samples[0]['sampleCollectionDateUtc'])

    def test_build_update_labware_message(self):
        """ Test the _build_update_labware_message method"""
        message_uuid = str(uuid.uuid4())
        sample_uuid = str(uuid.uuid4())
        labware_uuid = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)
        msg = UpdateLabwareMessage(
            message_uuid=message_uuid,
            message_create_date_utc=now,
            labware_updates=[
                Update(
                    uuid=labware_uuid,
                    name='barcode',
                    value='2'
                )
            ],
            sample_updates=[
                Update(
                    uuid=sample_uuid,
                    name='volume',
                    value='6'
                )
            ]
        )
        result = MessageBuilder._build_update_labware_message(msg)
        self.assertEqual(result['messageUuid'].decode(), message_uuid)
        self.assertIsNotNone(result['messageCreateDateUtc'])
        labware_updates = result['labwareUpdates']
        sample_updates = result['sampleUpdates']
        self.assertEqual(len(labware_updates), 1)
        self.assertEqual(len(sample_updates), 1)
        self.assertEqual(labware_updates[0]['labwareUuid'].decode(), labware_uuid)
        self.assertEqual(labware_updates[0]['name'], 'barcode')
        self.assertEqual(labware_updates[0]['value'], '2')
        self.assertEqual(sample_updates[0]['sampleUuid'].decode(), sample_uuid)
        self.assertEqual(sample_updates[0]['name'], 'volume')
        self.assertEqual(sample_updates[0]['value'], '6')
