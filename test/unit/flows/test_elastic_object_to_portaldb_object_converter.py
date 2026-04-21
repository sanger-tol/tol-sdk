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
        return ['tissue_prep', 'tissue_prep_event', 'tolid', 'tolid_event']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    def get_one(self, type_, id_):
        return self.data_object_factory(
            id_=id_,
            type_=type_,
            attributes={'tol_tum_action_count': None}
        )


class TestElasticObjectToPortaldbObjectConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticObjectToPortaldbObjectConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticObjectToPortaldbObjectConverter.Config(),
            destination_object_type='tissue_prep_event',
            fields={'test_field_1': 'test1'},
            id_field='different_id'
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='tissue_prep_id1',
            type_='tissue_prep',
            attributes={
                'different_id': 'different_id1',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual('different_id1', ret1.id)
        self.assertEqual('tissue_prep_event', ret1.type)
        self.assertEqual(ret1.attributes, {'test_field_1': 'test1'})

        # Test incremental conversion for tolid_event
        converter2 = ElasticObjectToPortaldbObjectConverter(
            data_object_factory=destination.data_object_factory,
            config=ElasticObjectToPortaldbObjectConverter.Config(),
            destination_object_type='tolid_event',
            fields={'test_field_2': 'test2'},
            id_field='different_id',
            incremental=True
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj2 = CoreDataObject(
            id_='tolid_id1',
            type_='tolid',
            attributes={
                'different_id': 'different_id2',
            }
        )

        converteds2 = converter2.convert(obj2)
        ret1 = next(converteds2)
        self.assertEqual('different_id2', ret1.id)
        self.assertEqual('tolid_event', ret1.type)
        self.assertEqual(ret1.attributes, {'test_field_2': 'test2', 'tol_tum_action_count': 1})
