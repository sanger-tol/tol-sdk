# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from tol.core.datasource_filter import DataSourceFilter
from tol.core.filter_strategy import (
    AttributeMetadataProvider,
    CompositeFilterStrategy,
    DateNormalisingPreprocessor,
    FilterPreprocessor,
    FilterStrategy,
)


class TestFilterStrategy:
    def test_convert_receives_filter_and_returns_target_type(self):
        class StubStrategy(FilterStrategy[dict]):
            def convert(self, object_type, object_filters=None):
                return {'converted': True}

        strategy = StubStrategy()
        result = strategy.convert('sample', DataSourceFilter(exact={'name': 'x'}))
        assert result == {'converted': True}

    def test_convert_with_none_filter(self):
        class StubStrategy(FilterStrategy[str]):
            def convert(self, object_type, object_filters=None):
                return None if object_filters is None else 'has_filter'

        strategy = StubStrategy()
        assert strategy.convert('sample', None) is None
        assert strategy.convert('sample', DataSourceFilter()) == 'has_filter'


class TestFilterPreprocessor:
    def test_preprocess_modifies_filter(self):
        class AddOwnerPreprocessor(FilterPreprocessor):
            def preprocess(self, object_type, object_filters):
                if object_filters.and_ is None:
                    object_filters.and_ = {}
                object_filters.and_['owner'] = {'eq': {'value': 'user1'}}
                return object_filters

        preprocessor = AddOwnerPreprocessor()
        f = DataSourceFilter(and_={'name': {'eq': {'value': 'test'}}})
        result = preprocessor.preprocess('sample', f)
        assert 'owner' in result.and_
        assert result.and_['name'] == {'eq': {'value': 'test'}}


class TestDateNormalisingPreprocessor:
    def test_converts_relative_date_string_to_datetime(self):
        metadata_provider = MagicMock(spec=AttributeMetadataProvider)
        metadata_provider.get_attribute_metadata_by_name.return_value = {
            'python_type': 'datetime'
        }
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'created_at': {'gt': {'value': '2 days ago'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert isinstance(result.and_['created_at']['gt']['value'], datetime)

    def test_leaves_non_datetime_fields_unchanged(self):
        metadata_provider = MagicMock(spec=AttributeMetadataProvider)
        metadata_provider.get_attribute_metadata_by_name.return_value = {
            'python_type': 'str'
        }
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'name': {'eq': {'value': 'test_value'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert result.and_['name']['eq']['value'] == 'test_value'

    def test_handles_none_metadata_gracefully(self):
        metadata_provider = MagicMock(spec=AttributeMetadataProvider)
        metadata_provider.get_attribute_metadata_by_name.return_value = None
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(and_={
            'unknown_field': {'eq': {'value': 'x'}}
        })

        result = preprocessor.preprocess('sample', f)

        assert result.and_['unknown_field']['eq']['value'] == 'x'

    def test_skips_when_and_is_none(self):
        metadata_provider = MagicMock(spec=AttributeMetadataProvider)
        preprocessor = DateNormalisingPreprocessor(metadata_provider)
        f = DataSourceFilter(exact={'name': 'x'})

        result = preprocessor.preprocess('sample', f)

        metadata_provider.get_attribute_metadata_by_name.assert_not_called()
        assert result.exact == {'name': 'x'}


class TestCompositeFilterStrategy:
    def test_applies_preprocessors_before_conversion(self):
        call_order = []

        class TrackingPreprocessor(FilterPreprocessor):
            def __init__(self, label):
                self.label = label

            def preprocess(self, object_type, object_filters):
                call_order.append(f'preprocess_{self.label}')
                return object_filters

        class TrackingStrategy(FilterStrategy[str]):
            def convert(self, object_type, object_filters=None):
                call_order.append('convert')
                return 'result'

        composite = CompositeFilterStrategy(
            delegate=TrackingStrategy(),
            preprocessors=[TrackingPreprocessor('a'), TrackingPreprocessor('b')],
        )
        composite.convert('sample', DataSourceFilter())

        assert call_order == ['preprocess_a', 'preprocess_b', 'convert']

    def test_skips_preprocessing_when_filter_is_none(self):
        preprocessor = MagicMock(spec=FilterPreprocessor)
        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = {'empty': True}

        composite = CompositeFilterStrategy(delegate, preprocessors=[preprocessor])
        result = composite.convert('sample', None)

        preprocessor.preprocess.assert_not_called()
        delegate.convert.assert_called_once_with('sample', None)
        assert result == {'empty': True}

    def test_passes_preprocessed_filter_to_delegate(self):
        class UpperCasePreprocessor(FilterPreprocessor):
            def preprocess(self, object_type, object_filters):
                if object_filters.exact:
                    object_filters.exact = {
                        k: v.upper() if isinstance(v, str) else v
                        for k, v in object_filters.exact.items()
                    }
                return object_filters

        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = 'ok'

        composite = CompositeFilterStrategy(
            delegate, preprocessors=[UpperCasePreprocessor()]
        )
        f = DataSourceFilter(exact={'name': 'hello'})
        composite.convert('sample', f)

        called_filter = delegate.convert.call_args[0][1]
        assert called_filter.exact['name'] == 'HELLO'

    def test_no_preprocessors_delegates_directly(self):
        delegate = MagicMock(spec=FilterStrategy)
        delegate.convert.return_value = 'direct'

        composite = CompositeFilterStrategy(delegate)
        f = DataSourceFilter(exact={'x': 1})
        result = composite.convert('sample', f)

        assert result == 'direct'
        delegate.convert.assert_called_once_with('sample', f)
