# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    ElasticObjectToPortaldbObjectConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['tissue_prep', 'tissue_prep_event']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestElasticObjectToPortaldbObjectConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticObjectToPortaldbObjectConverter(
            data_object_factory=destination.data_object_factory,
            destination_object_type='tissue_prep_event',
            fields={'test_field_1': 'test1'}
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='tissue_prep_id1',
            type_='tissue_prep',
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('tissue_prep_event', ret1.type)
        self.assertEqual(ret1.attributes, {'test_field_1': 'test1'})
