# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    LabwhereLocationToElasticSampleUpdateConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['location']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestElasticSequencingRequestLrpacbioConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = LabwhereLocationToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='lw-location-1234',
            type_='location',
            attributes={
                'parentage': 'Site1 / Building1 / Freezer1 / Shelf1',
                'name': 'Tray1'
            }
        )

        obj2 = CoreDataObject(
            id_='lw-location-5678',
            type_='location',
            attributes={
                'parentage': 'Site2 / Building2 / Freezer2 / Shelf2',
                'name': 'Tray2'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'sts_location': 'lw-location-1234',
            'parentage': 'Site1 / Building1 / Freezer1 / Shelf1',
            'name': 'Tray1'
        }))

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'sts_location': 'lw-location-5678',
            'parentage': 'Site2 / Building2 / Freezer2 / Shelf2',
            'name': 'Tray2'
        }))
