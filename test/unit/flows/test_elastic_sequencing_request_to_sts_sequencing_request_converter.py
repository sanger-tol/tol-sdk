# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    ElasticSequencingRequestToStsSequencingRequestConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sequencing_request']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestElasticSequencingRequestToStsSequencingRequestConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSequencingRequestToStsSequencingRequestConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticSequencingRequestToStsSequencingRequestConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        # if data_object relations data = data else data.attributes
        obj1 = CoreDataObject(
            id_='test1',
            type_='sequencing_request',
            attributes={
                'fluidx_id': 'value1',
                'sequencing_platform': 'pacbio',
                'completion_date': datetime.fromtimestamp(1234)
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='sequencing_request',
            attributes={
                'fluidx_id': 'value2',
                'sequencing_platform': 'hic'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'fluidx_id': 'value1',
            'platform': 'PACBIO',
            'submission_date': datetime.fromtimestamp(1234)
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'fluidx_id': 'value2',
            'platform': 'HIC',
            'submission_date': datetime.fromtimestamp(0)
        })

        with self.assertRaises(StopIteration):
            next(converteds)
