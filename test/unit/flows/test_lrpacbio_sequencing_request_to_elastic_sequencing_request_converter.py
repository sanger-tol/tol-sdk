# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    LrpacbioSequencingRequestToElasticSequencingRequestConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sequencing_request']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestLrpacbioSequencingRequestToElasticSequencingRequestConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = LrpacbioSequencingRequestToElasticSequencingRequestConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sequencing_request_id1',
            type_='sequencing_request',
            attributes={'library_remaining': 'No Library Type Matched',
                        'library_remaining_oplc': 'Check Library Type'}
        )

        obj2 = CoreDataObject(
            id_='sequencing_request_id2',
            type_='sequencing_request',
            attributes={'library_remaining': '-2',
                        'library_remaining_oplc': '-24'}
        )

        obj3 = CoreDataObject(
            id_='sequencing_request_id3',
            type_='sequencing_request',
            attributes={'library_remaining': '4',
                        'library_remaining_oplc': '6'}
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1.attributes, {
            'library_remaining': None,
            'library_remaining_oplc': None
        })

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2.attributes, {
            'library_remaining': 0.0,
            'library_remaining_oplc': 0.0
        })

        converteds = converter.convert(obj3)
        ret3 = next(converteds)
        self.assertEqual(ret3.attributes, {
            'library_remaining': 4.0,
            'library_remaining_oplc': 6.0
        })
