# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    StsProjectToElasticSampleUpdateConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['project']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestLabwhereLocationToElasticSampleConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsProjectToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=StsProjectToElasticSampleUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='proj1',
            type_='project',
            attributes={
                'target_coverage': 25
            }
        )

        obj2 = CoreDataObject(
            id_='proj2',
            type_='project',
            attributes={
                'target_coverage': 50
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'project': 'proj1',
            'target_coverage': 25
        }))

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'project': 'proj2',
            'target_coverage': 50
        }))
