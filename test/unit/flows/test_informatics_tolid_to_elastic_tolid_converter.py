# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    InformaticsTolidToElasticTolidConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestInformaticsTolidToElasticTolidConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = InformaticsTolidToElasticTolidConverter(
            data_object_factory=destination.data_object_factory,
            config=InformaticsTolidToElasticTolidConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='tolid1',
            type_='tolid',
            attributes={
                'status_summary': '1_submitted',
                'status': '11_done'
            }
        )
        obj2 = CoreDataObject(
            id_='tolid2',
            type_='tolid',
            attributes={
                'status_summary': None,
                'status': '11_done'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(obj1.attributes, ret1.attributes)

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        with self.assertRaises(StopIteration):
            next(converteds)
