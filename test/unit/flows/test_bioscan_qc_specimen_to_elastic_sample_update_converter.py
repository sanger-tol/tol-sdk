# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BioscanQcSpecimenToElasticSampleUpdateConverter,
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species', 'specimen']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioscanQcSpecimenToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BioscanQcSpecimenToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=BioscanQcSpecimenToElasticSampleUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='SPECIMEN1',
            type_='specimen',
            attributes={
                'sanger_qc_result': '1',
                'sanger_qc_description': '2',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'specimen.id': 'SPECIMEN1',
            'sanger_qc_result': '1',
            'sanger_qc_description': '2'
        }))
