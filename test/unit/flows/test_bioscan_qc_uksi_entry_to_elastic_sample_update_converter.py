# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BioscanQcUksiEntryToElasticSampleUpdateConverter,
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['uksi_entry', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioscanQcUksiEntryToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BioscanQcUksiEntryToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Genus species',
            type_='uksi_entry',
            attributes={
                'uksi_name_status': '1',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'bold_species': 'Genus species',
            'uksi_name_status': '1'
        }))
