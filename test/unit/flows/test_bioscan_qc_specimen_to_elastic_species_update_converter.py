# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BioscanQcSpecimenToElasticSpeciesUpdateConverter,
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioscanQcSpecimenToElasticSpeciesUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BioscanQcSpecimenToElasticSpeciesUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Genus species',
            type_='specimen',
            attributes={
                'sanger_qc_result': '1',
                'sanger_qc_description': '2',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'goat_scientific_name': 'Genus species',
            'sanger_qc_result': '1',
            'sanger_qc_description': '2'
        }))
