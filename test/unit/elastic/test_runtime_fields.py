# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import RuntimeField
from tol.elastic import (
    ElasticRuntimeFields
)


class TestRuntimeFields:
    def test_convert_type_only(self):
        assert ElasticRuntimeFields.convert_to_request(
            RuntimeField(type_='double')
        ) == {'type': 'double'}

    @pytest.mark.parametrize('script', ['emit(1.0);', ''])
    def test_convert_script(self, script):
        assert ElasticRuntimeFields.convert_to_request(
            RuntimeField(type_='double', script=script)
        ) == {'type': 'double', 'script': {'source': script}}

    def test_convert_function(self):
        script, params = ElasticRuntimeFields.coalesce_script(
            _return_type='double',
            fields=['field1', 'field2'],
        )
        assert ElasticRuntimeFields.convert_to_request(
            RuntimeField(
                type_='double',
                function='coalesce',
                function_kwargs={'fields': ['field1', 'field2']},
            )
        ) == {'type': 'double', 'script': {'source': script, 'params': params}}

    def test_convert_to_request_dict(self):
        assert ElasticRuntimeFields.convert_to_request_dict({
            'root': {
                'runtime_column': RuntimeField(type_='boolean', script='emit(true);'),
            },
            'related': {
                'root_int_column_min': RuntimeField(type_='double'),
                'root_int_column_max': RuntimeField(type_='double'),
            },
        }) == {
            'root': {
                'runtime_column': {'type': 'boolean', 'script': {'source': 'emit(true);'}},
            },
            'related': {
                'root_int_column_min': {'type': 'double'},
                'root_int_column_max': {'type': 'double'},
            },
        }

    def test_math(self):
        script, params = ElasticRuntimeFields.math_script(
            first='field1',
            second='field2',
            operation='/'
        )
        assert ''.join(script.split()) == ''.join("""
            if (doc.containsKey('field1') && doc['field1'].size() > 0
                    && doc.containsKey('field2') && doc['field2'].size() > 0) {
                emit(((Number) (doc['field1'].value / doc['field2'].value)).doubleValue());
            }
        """.split())
        assert params == {}

    def test_coalesce(self):
        script, params = ElasticRuntimeFields.coalesce_script(
            fields=['field1', 'field2']
        )
        assert ''.join(script.split()) == ''.join("""
            if (1==1) {
                if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                    for (def value : doc['field1.keyword']) {emit(value);}
                } else if (doc.containsKey('field2.keyword') && doc['field2.keyword'].size() > 0) {
                    for (def value : doc['field2.keyword']) {emit(value);}
                }
            }
        """.split())
        assert params == {}

    def test_coalesce_keyword_null_wins(self):
        script, params = ElasticRuntimeFields.coalesce_script(
            fields=['field1', 'field2'],
            null_wins=True,
        )
        assert ''.join(script.split()) == ''.join("""
            if (1==1) {
                if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                    for (def value : doc['field1.keyword']) {emit(value);} return;
                } else if (doc.containsKey('field2.keyword') && doc['field2.keyword'].size() > 0) {
                    for (def value : doc['field2.keyword']) {emit(value);} return;
                }
            }
        """.split())
        assert params == {}

    @pytest.mark.parametrize('return_type,conversion', [
        ('long', '((Number) value).longValue()'),
        ('double', '((Number) value).doubleValue()'),
        ('date', 'value.toInstant().toEpochMilli()'),
        ('boolean', 'value'),
    ])
    def test_coalesce_multivalue_conversion(self, return_type, conversion):
        script, params = ElasticRuntimeFields.coalesce_script(
            fields=['field1', 'field2'],
            _return_type=return_type
        )
        assert "for (def value : doc['field1'])" in script
        assert "for (def value : doc['field2'])" in script
        assert f'emit({conversion});' in script
        assert '}elseif(' in ''.join(script.split())
        assert params == {}

    def test_latest_date(self):
        script, params = ElasticRuntimeFields.latest_date_script(
            date_fields=['field1', 'field2'],
            allow_missing=False
        )
        assert ''.join(script.split()) == ''.join("""
                if (doc.containsKey('field1') && doc['field1'].size() > 0 &&
                    doc.containsKey('field2') && doc['field2'].size() > 0) {
                    ZonedDateTime latestDate = null;
                    for (int i = 0; i < params.dates.size(); i++) {
                        String dep = params.dates.get(i);
                        if (doc.containsKey(dep) && doc[dep].size() > 0) {
                            ZonedDateTime currentDate = doc[dep].value;
                            if (latestDate == null || currentDate.isAfter(latestDate)) {
                                latestDate = currentDate;
                            }
                        }
                    }
                    if (latestDate != null) {
                        emit(latestDate.toInstant().toEpochMilli());
                    }
                }
        """.split())
        assert params['dates'] == ['field1', 'field2']

    def test_date_interval(self):
        script, params = ElasticRuntimeFields.date_interval_script(
            start_date='field1',
            end_date='field2'
        )
        assert ''.join(script.split()) == ''.join("""
            if (doc.containsKey('field1') && doc['field1'].size() > 0 &&
                    doc.containsKey('field2') && doc['field2'].size() > 0) {
                ZonedDateTime start = doc['field1'].value;
                ZonedDateTime end = doc['field2'].value;
                long differenceInMillis = ChronoUnit.DAYS.between(start, end);
                emit(differenceInMillis);
            }
        """.split())
        assert params == {}

    @pytest.mark.parametrize('function,type_,kwargs', [
        ('math', 'double', {'first': 'a', 'second': 'b'}),
        ('date_interval', 'long', {'start_date': 'start', 'end_date': 'end'}),
        ('latest_date', 'date', {'date_fields': ['a', 'b']}),
        ('substring', 'keyword', {'field': 'name', 'start': 0, 'end': 2}),
    ])
    def test_convert_all_functions(self, function, type_, kwargs):
        expected_script, expected_params = getattr(
            ElasticRuntimeFields, f'{function}_script'
        )(_return_type=type_, **kwargs)
        assert ElasticRuntimeFields.convert_to_request(RuntimeField(
            type_=type_, function=function, function_kwargs=kwargs,
        )) == {
            'type': type_,
            'script': {'source': expected_script, 'params': expected_params},
        }

    def test_shared_nested_field(self):
        child = RuntimeField(
            type_='long', function='math',
            function_kwargs={'first': 'a', 'second': 'b', 'operation': '+'},
        )
        script, params = ElasticRuntimeFields.math_script(
            first=child, second=child, operation='+',
        )
        assert script.count('List _tol_evaluate_0(') == 1
        assert script.count('def _tol_values_0 =') == 1
        assert '_tol_values_0.get(0) + _tol_values_0.get(0)' in script
        assert 'result.add(' in script
        assert script.count('emit(') == 1
        assert params == {}

    def test_nested_date_parameter_scopes(self):
        children = [
            RuntimeField(
                type_='date', function='latest_date',
                function_kwargs={'date_fields': fields},
            )
            for fields in [['start'], ['end']]
        ]
        script, params = ElasticRuntimeFields.latest_date_script(date_fields=children)
        assert list(params.values()) == [['start'], ['end']]
        for key in params:
            assert f'params.{key}.size()' in script
        assert script.count('List _tol_evaluate_') == 2
        assert script.count('toEpochMilli()') == 1
        assert script.count('emit(') == 1

    def test_nested_keyword_has_no_keyword_suffix(self):
        child = RuntimeField(
            type_='keyword', function='substring',
            function_kwargs={'field': 'name', 'start': 0, 'end': 5},
        )
        script, _ = ElasticRuntimeFields.substring_script(field=child, start=1, end=3)
        assert "doc['name.keyword']" in script
        assert '_tol_values_0.get(0).substring(1, 3)' in script
        assert '_tol_values_0.keyword' not in script

    @pytest.mark.parametrize('child', [
        RuntimeField(type_='long', script='emit(1);'),
        RuntimeField(type_='long', script=''),
        RuntimeField(type_='long'),
    ])
    def test_reject_unsupported_nested_definitions(self, child):
        with pytest.raises(ValueError, match='Nested runtime fields must use a built-in'):
            ElasticRuntimeFields.math_script(first=child, second='a')

    def test_reject_nested_type_mismatch(self):
        child = RuntimeField(
            type_='keyword', function='coalesce', function_kwargs={'fields': ['name']},
        )
        with pytest.raises(ValueError, match='Expected nested runtime field type'):
            ElasticRuntimeFields.math_script(first=child, second='a')

    def test_reject_cycle(self):
        kwargs = {'first': 'a', 'second': 'b'}
        child = RuntimeField(type_='long', function='math', function_kwargs=kwargs)
        kwargs['first'] = child
        with pytest.raises(ValueError, match='Cyclic runtime field dependency'):
            ElasticRuntimeFields.convert_to_request(child)

    def test_reject_unknown_function(self):
        with pytest.raises(ValueError, match='Unsupported runtime field function'):
            ElasticRuntimeFields.convert_to_request(RuntimeField(
                type_='long', function='unknown',
            ))

    def test_reject_invalid_field(self):
        with pytest.raises(TypeError, match='Field arguments must be'):
            ElasticRuntimeFields.math_script(first={'function': 'math'}, second='b')

    def test_reject_invalid_operation(self):
        with pytest.raises(ValueError, match='Unsupported runtime field math operation'):
            ElasticRuntimeFields.math_script(first='a', second='b', operation='**')

    def test_reject_invalid_return_type(self):
        with pytest.raises(ValueError, match='Unsupported return type'):
            ElasticRuntimeFields.latest_date_script(date_fields=['a'], _return_type='long')

    def test_does_not_mutate_arguments(self):
        dates = ['a', 'b']
        kwargs = {'date_fields': dates}
        child = RuntimeField(type_='date', function='latest_date', function_kwargs=kwargs)
        first = ElasticRuntimeFields.latest_date_script(date_fields=[child, 'c'])
        second = ElasticRuntimeFields.latest_date_script(date_fields=[child, 'c'])
        assert first == second
        assert child.function_kwargs == {'date_fields': ['a', 'b']}
        assert kwargs['date_fields'] is dates

    def test_substring(self):
        script, params = ElasticRuntimeFields.substring_script(
            field='field1',
            start=0,
            end=5
        )
        assert ''.join(script.split()) == ''.join("""
            if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                emit(doc['field1.keyword'].value.substring(0, 5));
            }
        """.split())
        assert params == {}
