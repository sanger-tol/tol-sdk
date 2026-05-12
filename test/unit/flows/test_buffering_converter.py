# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import BufferingConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBufferingConverter(TestCase):

    def test_buffering(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)

        mock_object1 = source.data_object_factory(
            'sample',
            'ABC1',
            attributes={
                'attribute1': 'value1',
            }
        )
        mock_object2 = source.data_object_factory(
            'sample',
            'ABC2',
            attributes={
                'attribute1': 'value1',
                'attribute3': ['value3']
            }
        )
        mock_object3 = source.data_object_factory(
            'sample',
            'ABC2',
            attributes={
                'attribute2': 'value2',
                'attribute3': ['value4']
            }
        )
        mock_object4 = source.data_object_factory(
            'sample',
            'ABC3',
            attributes={
                'attribute1': 'value1',
            }
        )

        config = BufferingConverter.Config(
        )
        converter = BufferingConverter(
            destination.data_object_factory,
            config
        )

        result = list(converter.convert_iterable(
            [mock_object1, mock_object2, mock_object3, mock_object4]
        ))
        assert len(result) == 3
        assert result[0].id == 'ABC1'
        assert result[0].attributes == {
            'attribute1': 'value1',
        }
        assert result[1].id == 'ABC2'
        assert result[1].attributes == {
            'attribute1': 'value1',
            'attribute2': 'value2',
            'attribute3': ['value3', 'value4']
        }
        assert result[2].id == 'ABC3'
        assert result[2].attributes == {
            'attribute1': 'value1',
        }
