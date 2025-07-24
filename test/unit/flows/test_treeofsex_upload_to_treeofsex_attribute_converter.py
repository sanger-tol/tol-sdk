# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    TreeofsexUploadToTreeofsexAttributeConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['attribute']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource, Relational):
    @property
    def supported_types(self):
        return ['attribute', 'source', 'species', 'attribute_key']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_attribute = RelationshipConfig()
        rc_attribute.to_one = {
            'attribute_key': 'attribute_key',
            'source': 'source',
            'species': 'species',
        }
        return {'attribute': rc_attribute}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        pass

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestTreeofsexUploadToTreeofsexAttributeConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TreeofsexUploadToTreeofsexAttributeConverter(
            data_object_factory=destination.data_object_factory
        )

        obj1 = source.data_object_factory(
            id_=1,
            type_='attribute',
            attributes={
                'attribute_key': 'key1',
                'attribute_value': 'value1',
                'attribute_state': 'active',
                'source': 'source1',
                'taxon_id': 'species1'
            }
        )
        obj2 = source.data_object_factory(
            id_=2,
            type_='attribute',
            attributes={
                'attribute_key': 'key2',
                'attribute_value': 'value2',
                'attribute_state': 'active',
                'source': 'source1',
                'taxon_id': 'species2'
            }
        )
        obj3 = source.data_object_factory(
            id_=3,
            type_='attribute',
            attributes={
                'attribute_key': 'key3',
                'attribute_value': 'value3',
                'attribute_state': 'active',
                'source': 'source2',
                'taxon_id': 'species1'
            }
        )

        converteds = converter.convert_iterable([obj1, obj2, obj3])
        ret1 = next(converteds)
        assert ret1.type == 'source'
        assert ret1.id == 'source1'
        assert ret1.attributes == {}

        ret2 = next(converteds)
        assert ret2.type == 'species'
        assert ret2.id == 'species1'
        assert ret2.attributes == {}

        ret3 = next(converteds)
        assert ret3.type == 'attribute'
        assert ret3.id is None
        assert ret3.attributes == {
            'value': 'value1',
            'state': 'active',
        }
        assert ret3.attribute_key.type == 'attribute_key'
        assert ret3.attribute_key.id == 'key1'
        assert ret3.source.type == 'source'
        assert ret3.source.id == 'source1'
        assert ret3.species.type == 'species'
        assert ret3.species.id == 'species1'

        ret4 = next(converteds)
        assert ret4.type == 'species'
        assert ret4.id == 'species2'
        assert ret4.attributes == {}

        ret5 = next(converteds)
        assert ret5.type == 'attribute'
        assert ret5.id is None
        assert ret5.attributes == {
            'value': 'value2',
            'state': 'active',
        }
        assert ret5.attribute_key.type == 'attribute_key'
        assert ret5.attribute_key.id == 'key2'
        assert ret5.source.type == 'source'
        assert ret5.source.id == 'source1'
        assert ret5.species.type == 'species'
        assert ret5.species.id == 'species2'

        ret6 = next(converteds)

        assert ret6.type == 'source'
        assert ret6.id == 'source2'
        assert ret6.attributes == {}

        ret7 = next(converteds)
        assert ret7.type == 'attribute'
        assert ret7.id is None
        assert ret7.attributes == {
            'value': 'value3',
            'state': 'active',
        }
        assert ret7.attribute_key.type == 'attribute_key'
        assert ret7.attribute_key.id == 'key3'
        assert ret7.source.type == 'source'
        assert ret7.source.id == 'source2'
        assert ret7.species.type == 'species'
        assert ret7.species.id == 'species1'

        with self.assertRaises(StopIteration):
            next(converteds)
