# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    TreeofsexUploadToTreeofsexwhSpeciesConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTreeofsexUploadToTreeofsexwhSpeciesConverter(TestCase):
    def test_convert_iterable(self):

        source = _MockDataSource(config={})
        destination = _MockDataSourceDestination(config={})
        core_data_object(source)
        core_data_object(destination)

        converter = TreeofsexUploadToTreeofsexwhSpeciesConverter(
            data_object_factory=destination.data_object_factory
        )

        obj1 = source.data_object_factory(
            id_=1,
            type_='species',
            attributes={
                'species': 'Species specius',
                'key': 'key1',
                'value': 'value1',
                'reference': 'source1',
            }
        )

        converteds = converter.convert_iterable([obj1])
        ret1 = next(converteds)
        assert ret1.type == 'species'
        assert ret1.id == 'Species specius'
        assert ret1.attributes == {
            'key1': [
                {
                    'value': 'value1',
                    'source': 'source1',
                }
            ]
        }

        with self.assertRaises(StopIteration):
            next(converteds)
