# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.elastic import (
    ElasticRuntimeFields
)


class TestRuntimeFields:
    def test_math(self):
        rf = ElasticRuntimeFields.math(
            'field1',
            'field2',
            operation='/'
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (doc.containsKey('field1') && doc['field1'].size() > 0
                    && doc.containsKey('field2') && doc['field2'].size() > 0) {
                emit(doc['field1'].value / doc['field2'].value)
            }
        """.split())

    def test_coalesce(self):
        rf = ElasticRuntimeFields.coalesce(
            ['field1', 'field2']
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (1==1) {
                if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                    for (def value : doc['field1.keyword']) {emit(value);}
                } else if (doc.containsKey('field2.keyword') && doc['field2.keyword'].size() > 0) {
                    for (def value : doc['field2.keyword']) {emit(value);}
                }
            }
        """.split())

    def test_coalesce_keyword_null_wins(self):
        rf = ElasticRuntimeFields.coalesce(
            ['field1', 'field2'],
            null_wins=True,
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (1==1) {
                if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                    for (def value : doc['field1.keyword']) {emit(value);} return;
                } else if (doc.containsKey('field2.keyword') && doc['field2.keyword'].size() > 0) {
                    for (def value : doc['field2.keyword']) {emit(value);} return;
                }
            }
        """.split())
        assert rf['script']['params'] == {}

    @pytest.mark.parametrize('return_type,conversion', [
        ('long', '((Number) value).longValue()'),
        ('double', '((Number) value).doubleValue()'),
        ('date', 'value.toInstant().toEpochMilli()'),
        ('boolean', 'value'),
    ])
    def test_coalesce_multivalue_conversion(self, return_type, conversion):
        runtime_field = ElasticRuntimeFields.coalesce(['field1', 'field2'], return_type=return_type)
        script = runtime_field['script']['source']

        assert "for (def value : doc['field1'])" in script
        assert "for (def value : doc['field2'])" in script
        assert f'emit({conversion});' in script
        assert '}else if ' in script

    def test_latest_date(self):
        rf = ElasticRuntimeFields.latest_date(
            ['field1', 'field2'],
            allow_missing=False
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
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
        assert rf['script']['params']['dates'] == ['field1', 'field2']

    def test_date_interval(self):
        rf = ElasticRuntimeFields.date_interval(
            start_date='field1',
            end_date='field2'
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (doc.containsKey('field1') && doc['field1'].size() > 0 &&
                    doc.containsKey('field2') && doc['field2'].size() > 0) {
                ZonedDateTime start = doc['field1'].value;
                ZonedDateTime end = doc['field2'].value;
                long differenceInMillis = ChronoUnit.DAYS.between(start, end);
                emit(differenceInMillis);
            }
        """.split())

    def test_substring(self):
        rf = ElasticRuntimeFields.substring(
            'field1',
            start=0,
            end=5
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                emit(doc['field1.keyword'].value.substring(0, 5));
            }
        """.split())
