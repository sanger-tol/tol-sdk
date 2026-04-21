# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    LabwhereLocationToStsTrayConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['location', 'freezer_tray']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestLabwhereLocationToStsTrayConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = LabwhereLocationToStsTrayConverter(
            data_object_factory=destination.data_object_factory,
            config=LabwhereLocationToStsTrayConverter.Config()
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
        self.assertEqual('lw-location-1234', ret1.id)
        self.assertEqual({
            'parentage': 'Site1 / Building1 / Freezer1 / Shelf1',
            'name': 'Tray1'
        }, ret1.attributes)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual('lw-location-5678', ret2.id)
        self.assertEqual({
            'parentage': 'Site2 / Building2 / Freezer2 / Shelf2',
            'name': 'Tray2'
        }, ret2.attributes)
