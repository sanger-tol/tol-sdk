# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BoldBinToElasticSampleUpdateConverter
)


class _MockDataSourceBold(DataSource):

    @property
    def supported_types(self):
        return ['bin']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceElastic(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBoldSampleToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceBold(config={})
        destination = _MockDataSourceElastic(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BoldBinToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=BoldBinToElasticSampleUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='BOLD1',
            type_='bin',
            attributes={
                'taxonomy': {'kingdom': {'kingdom1': 10}}
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'bold_bin_uri': 'BOLD1',
            'bold_taxonomy': {'kingdom': {'kingdom1': 10}}
        }))
