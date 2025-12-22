# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import AutoDetectManifestTypeConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['upload']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource):
    @property
    def supported_types(self):
        return ['upload']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestAutoDetectManifestTypeConverter(TestCase):

    def test_convert(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'upload',
            'ABC123',
            attributes={
                'RACK_OR_TUBE_ID': 'B20'
            }
        )
        config = AutoDetectManifestTypeConverter.Config(
            rack_or_plate='RACK_OR_TUBE_ID',
        )
        converter = AutoDetectManifestTypeConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        res = next(result)
        attrs = res.attributes
        assert attrs['manifest_type'] == 'PLATE_WELL'