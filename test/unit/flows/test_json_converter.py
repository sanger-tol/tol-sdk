# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import JsonConverter


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

    def test_convert_maps_wrapped_payload_and_derives_relationship_fields(self):
        source = _MockSource(config={})
        destination = _MockDestination(config={})
        core_data_object(source)
        core_data_object(destination)

        input_obj = source.data_object_factory(
            'json_blob',
            'raw-1',
            attributes={
                'data': {
                    'metadata': {
                        'doi': '10.12688/example.1'
                    },
                    'assembly_stats': {
                        'sequence_report': {
                            'assembly_accession': 'GCA_123456789.1'
                        },
                        'species': [
                            {'ncbi_taxonomy_id': '9606'}
                        ],
                        'samples': [
                            {'tolid': 'ilHumTest1'}
                        ]
                    }
                }
            }
        )

        converter = JsonConverter(
            destination.data_object_factory,
            JsonConverter.Config()
        )

        converted = converter.convert(input_obj)
        ret = next(converted)

        self.assertEqual('genome_note', ret.type)
        self.assertEqual('10.12688/example.1', ret.id)
        self.assertEqual('GCA_123456789.1', ret.attributes['assembly_accession'])
        self.assertEqual('9606', ret.attributes['taxid'])
        self.assertEqual('ilHumTest1', ret.attributes['tolid'])
        self.assertIn('assembly_stats', ret.attributes)
        self.assertIn('metadata', ret.attributes)

        with self.assertRaises(StopIteration):
            next(converted)

    def test_convert_raises_when_strict_and_required_fields_missing(self):
        source = _MockSource(config={})
        destination = _MockDestination(config={})
        core_data_object(source)
        core_data_object(destination)

        input_obj = source.data_object_factory(
            'json_blob',
            'raw-2',
            attributes={
                'data': {
                    'metadata': {
                        'doi': '10.12688/example.2'
                    },
                    'assembly_stats': {
                        'sequence_report': {
                            'assembly_accession': 'GCA_987654321.1'
                        },
                        'species': [],
                        'samples': []
                    }
                }
            }
        )

        converter = JsonConverter(
            destination.data_object_factory,
            JsonConverter.Config(strict_missing_relation_fields=True)
        )

        with self.assertRaises(ValueError):
            next(converter.convert(input_obj))
