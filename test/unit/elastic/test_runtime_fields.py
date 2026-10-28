# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.elastic import (
    ElasticRuntimeFields
)


class TestRuntimeFields:
    def test_math(self):
        script, params = ElasticRuntimeFields.math_script(
            first='field1',
            second='field2',
            operation='/'
        )
        assert ''.join(script.split()) == ''.join("""
            if (doc.containsKey('field1') && doc['field1'].size() > 0
                    && doc.containsKey('field2') && doc['field2'].size() > 0) {
                emit(doc['field1'].value / doc['field2'].value)
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
        assert '}else if ' in script
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
