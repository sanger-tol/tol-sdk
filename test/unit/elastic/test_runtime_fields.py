# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.elastic import (
    RuntimeFields
)


class TestRuntimeFields:
    def test_math(self):
        rf = RuntimeFields.math(
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
        rf = RuntimeFields.coalesce(
            ['field1', 'field2']
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (1==1) {
                if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                    emit(doc['field1.keyword'].value);
                } else if (doc.containsKey('field2.keyword') && doc['field2.keyword'].size() > 0) {
                    emit(doc['field2.keyword'].value);
                }
            }
        """.split())

    def test_latest_date(self):
        rf = RuntimeFields.latest_date(
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
        rf = RuntimeFields.date_interval(
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
        rf = RuntimeFields.substring(
            'field1',
            start=0,
            end=5
        )
        assert ''.join(rf['script']['source'].split()) == ''.join("""
            if (doc.containsKey('field1.keyword') && doc['field1.keyword'].size() > 0) {
                emit(doc['field1.keyword'].value.substring(0, 5));
            }
        """.split())
