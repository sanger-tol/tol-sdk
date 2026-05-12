# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.core.data_object import ErrorObject
from tol.flows.converters import (
    BenchlingTissueToStsSampleConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample', 'tissue']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBenchlingTissueToStsSampleConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BenchlingTissueToStsSampleConverter(
            data_object_factory=destination.data_object_factory,
            config=BenchlingTissueToStsSampleConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806

        obj1 = CoreDataObject(
            id_='test1',
            type_='tissue',
            attributes={
                'sts_id': 123,
            }
        )
        obj2 = ErrorObject(
            details='test_detail',
            object_type='test_type',
            object_=obj1,
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('123', ret1.id)
        self.assertEqual('sample', ret1.type)
        self.assertEqual(ret1.eln_id, 'test1')
        assert ret1.eln_updated_at is not None

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual('123', ret2.id)
        self.assertEqual('sample', ret2.type)
        self.assertEqual(ret2.eln_error, {
            'details': 'test_detail',
            'object_type': 'test_type',
        })

        with self.assertRaises(StopIteration):
            next(converteds)
