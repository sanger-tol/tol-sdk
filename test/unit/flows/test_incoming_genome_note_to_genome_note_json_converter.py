# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import IncomingGenomeNoteToGenomeNoteJsonConverter


class _MockSource(DataSource):
    @property
    def supported_types(self):
        return ['json_blob']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDestination(DataSource):
    @property
    def supported_types(self):
        return ['genome_note']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestJsonConverter(TestCase):

    def setUp(self):
        self.source = _MockSource(config={})
        self.destination = _MockDestination(config={})
        core_data_object(self.source)
        core_data_object(self.destination)
        self.converter = IncomingGenomeNoteToGenomeNoteJsonConverter(
            self.destination.data_object_factory,
            IncomingGenomeNoteToGenomeNoteJsonConverter.Config()
        )

    def _build_input(self, object_id, attributes):
        return self.source.data_object_factory(
            'json_blob',
            object_id,
            attributes=attributes
        )

    def _convert_one(self, input_obj):
        converted = self.converter.convert(input_obj)
        ret = next(converted)
        with self.assertRaises(StopIteration):
            next(converted)
        return ret

    def test_convert_maps_wrapped_payload(self):
        input_obj = self._build_input(
            'raw-1',
            {
                'data': {
                    'metadata': {'doi': '10.12688/example.1'},
                    'extra_field': 'should_be_ignored',
                    'reviewer_reports': [
                        {'id': 'report-1', 'recommendation': 'approve'}
                    ],
                    'assembly_stats': {
                        'sequence_report': {
                            'assembly_accession': 'GCA_123456789.1'
                        },
                        'species': [{'ncbi_taxonomy_id': '9606'}],
                        'samples': [{'tolid': 'ilHumTest1'}]
                    }
                }
            }
        )

        ret = self._convert_one(input_obj)

        self.assertEqual('genome_note', ret.type)
        # Now expects taxonomy id as output id
        self.assertEqual('9606', ret.id)
        self.assertIn('assembly_stats', ret.attributes)
        self.assertIn('metadata', ret.attributes)
        self.assertIn('reviewer_reports', ret.attributes)
        self.assertNotIn('extra_field', ret.attributes)
        self.assertEqual('report-1', ret.attributes['reviewer_reports'][0]['id'])

    def test_convert_handles_unwrapped_payload(self):
        input_obj = self._build_input(
            'raw-4',
            {
                'metadata': {'doi': '10.12688/example.1'},
                'assembly_stats': {'accession': 'GCA_123456789.1'}
            }
        )

        with self.assertRaises(ValueError) as context:
            self._convert_one(input_obj)
        self.assertIn('taxonomy id', str(context.exception))

    def test_convert_raises_on_non_dict_payload(self):
        input_obj = self._build_input(
            'raw-5',
            {
                'data': 'not a dict, just a string'
            }
        )

        with self.assertRaises(ValueError) as context:
            list(self.converter.convert(input_obj))

        self.assertIn('JSON object', str(context.exception))
