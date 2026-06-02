# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import DataSource, ErrorObject, core_data_object
from tol.flows.converters import ErrorObjectConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


@pytest.fixture
def source():
    ds = _MockDataSource(config={})
    core_data_object(ds)
    return ds


@pytest.fixture
def destination():
    ds = _MockDataSource(config={})
    core_data_object(ds)
    return ds


@pytest.fixture
def data_object(source):
    return source.data_object_factory('sample', id_='obj-1', attributes={})


@pytest.fixture
def error_object():
    return ErrorObject(details={'message': 'something went wrong'}, object_type='sample')


class TestErrorObjectConverterIncludeTrue:
    """include=True (default): yield ErrorObjects, discard DataObjects."""

    @pytest.fixture
    def converter(self, destination):
        return ErrorObjectConverter(
            destination.data_object_factory,
            config=ErrorObjectConverter.Config(include=True),
        )

    def test_yields_error_object(self, converter, error_object):
        result = list(converter.convert(error_object))
        assert result == [error_object]

    def test_discards_data_object(self, converter, data_object):
        result = list(converter.convert(data_object))
        assert result == []

    def test_default_config_is_include_true(self, destination):
        converter = ErrorObjectConverter(
            destination.data_object_factory,
            config=ErrorObjectConverter.Config(),
        )
        error = ErrorObject(details={}, object_type='sample')
        assert list(converter.convert(error)) == [error]


class TestErrorObjectConverterIncludeFalse:
    """include=False: yield DataObjects, discard ErrorObjects."""

    @pytest.fixture
    def converter(self, destination):
        return ErrorObjectConverter(
            destination.data_object_factory,
            config=ErrorObjectConverter.Config(include=False),
        )

    def test_yields_data_object(self, converter, data_object):
        result = list(converter.convert(data_object))
        assert len(result) == 1
        assert result[0] is data_object

    def test_discards_error_object(self, converter, error_object):
        result = list(converter.convert(error_object))
        assert result == []
