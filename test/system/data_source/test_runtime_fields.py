# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from uuid import uuid4

import pytest

import requests

from tol.core import RuntimeField
from tol.elastic import ElasticRuntimeFields


def runtime(type_, function, **kwargs):
    return RuntimeField(type_=type_, function=function, function_kwargs=kwargs)


@pytest.fixture(scope='module')
def runtime_index():
    session = requests.Session()
    session.auth = (os.environ['ELASTIC_USER'], os.environ['ELASTIC_PASSWORD'])
    url = os.environ['ELASTIC_URI'].rstrip('/')
    index = f'test-runtime-fields-{uuid4().hex}'
    properties = {
        **{name: {'type': 'long'} for name in ['a', 'b', 'c', 'zero', 'missing_number']},
        **{name: {'type': 'date'} for name in ['created', 'updated', 'missing_date']},
        **{
            name: {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}}
            for name in ['title', 'tags', 'fallback', 'missing_keyword', 'sentinel']
        },
        'flag': {'type': 'boolean'},
    }
    response = session.put(
        f'{url}/{index}', json={'mappings': {'properties': properties}}, timeout=10,
    )
    response.raise_for_status()
    try:
        yield session, url, index
    finally:
        response = session.delete(f'{url}/{index}', timeout=10)
        response.raise_for_status()
        session.close()


@pytest.mark.parametrize('field,expected', [
    pytest.param(
        runtime('double', 'math',
                first=runtime('long', 'math', first='a', second='b', operation='+'),
                second='b'),
        [5.0], id='nested-math',
    ),
    pytest.param(
        runtime('long', 'math',
                first=runtime('long', 'math',
                              first=runtime('long', 'coalesce', fields=['missing_number', 'a']),
                              second='b', operation='+'),
                second='c', operation='*'),
        [30], id='three-level-math',
    ),
    pytest.param(
        runtime('double', 'math',
                first=runtime('double', 'date_interval',
                              start_date='created', end_date='updated'),
                second='c'),
        [2 / 3], id='double-date-interval-child',
    ),
    pytest.param(
        runtime('long', 'math', operation='-',
                first=runtime('long', 'math', first='a', second='b', operation='+'),
                second=runtime('long', 'math', first='b', second='c', operation='*')),
        [4], id='sibling-math-local-scopes',
    ),
    pytest.param(
        runtime('keyword', 'substring',
                field=runtime('keyword', 'substring', field='title', start=1, end=5),
                start=1, end=3),
        ['cd'], id='nested-substring',
    ),
    pytest.param(
        runtime('keyword', 'coalesce',
                fields=[runtime('keyword', 'coalesce', fields=['missing_keyword', 'tags']),
                        'fallback']),
        ['alpha', 'beta'], id='nested-multivalue-coalesce',
    ),
    pytest.param(
        runtime('keyword', 'coalesce',
                fields=[runtime('keyword', 'coalesce', fields=['missing_keyword']),
                        'fallback']),
        ['fallback'], id='missing-child-fallback',
    ),
    pytest.param(
        runtime('keyword', 'substring',
                field=runtime('keyword', 'coalesce', fields=['tags']),
                start=0, end=2),
        ['al'], id='first-value-of-multivalue-child',
    ),
    pytest.param(
        runtime('double', 'coalesce',
                fields=['a', runtime('long', 'math', first='a', second='zero')]),
        [8.0], id='lazy-coalesce-does-not-divide-by-zero',
    ),
    pytest.param(
        runtime('long', 'date_interval',
                start_date=runtime('date', 'coalesce', fields=['missing_date', 'created']),
                end_date=runtime('date', 'latest_date', date_fields=['created', 'updated'])),
        [2], id='nested-date-interval',
    ),
    pytest.param(
        runtime('date', 'latest_date',
                date_fields=[runtime('date', 'latest_date', date_fields=['created']),
                             runtime('date', 'latest_date', date_fields=['updated'])]),
        ['2026-01-03T00:00:00.000Z'], id='nested-date-parameters',
    ),
    pytest.param(
        runtime('date', 'latest_date',
                date_fields=[runtime('date', 'latest_date', date_fields=['missing_date']),
                             'updated']),
        ['2026-01-03T00:00:00.000Z'], id='latest-date-allows-missing-child',
    ),
    pytest.param(
        runtime('date', 'latest_date', allow_missing=False,
                date_fields=[runtime('date', 'latest_date', date_fields=['missing_date']),
                             'updated']),
        [], id='latest-date-requires-child',
    ),
    pytest.param(
        runtime('date', 'latest_date', allow_missing=False,
                date_fields=[runtime('date', 'latest_date', date_fields=['created']),
                             'updated']),
        ['2026-01-03T00:00:00.000Z'], id='latest-date-all-children-present',
    ),
    pytest.param(
        runtime('double', 'math',
                first=runtime('long', 'coalesce', fields=['missing_number']), second='b'),
        [], id='missing-child-in-required-operand',
    ),
    pytest.param(
        runtime('boolean', 'coalesce',
                fields=[runtime('boolean', 'coalesce', fields=['flag'])]),
        [False], id='false-is-not-missing',
    ),
    pytest.param(
        runtime('long', 'coalesce',
                fields=[runtime('long', 'math', first='zero', second='b')]),
        [0], id='zero-is-not-missing',
    ),
    pytest.param(
        runtime('keyword', 'coalesce', null_wins=True,
                fields=[runtime('keyword', 'coalesce', null_wins=True, fields=['title']),
                        'fallback']),
        ['abcdef'], id='nested-null-wins-does-not-return-from-parent',
    ),
    pytest.param(
        runtime('keyword', 'substring',
                field=runtime('keyword', 'coalesce', null_wins=True, fields=['title']),
                start=1, end=3),
        ['bc'], id='nested-null-wins-continues-parent',
    ),
    pytest.param(
        runtime('keyword', 'coalesce',
                fields=[runtime('keyword', 'coalesce', fields=['sentinel']), 'fallback']),
        [ElasticRuntimeFields.NULL_SENTINEL], id='nested-null-sentinel-is-present',
    ),
    pytest.param(
        runtime('date', 'coalesce',
                fields=[runtime('date', 'latest_date', date_fields=['created', 'updated'])]),
        ['2026-01-03T00:00:00.000Z'], id='date-coalesce-emits-epoch-milliseconds',
    ),
    pytest.param(
        runtime('date', 'latest_date', date_fields=[]),
        [], id='empty-latest-date',
    ),
    pytest.param(
        runtime('keyword', 'coalesce', fields=[]),
        [], id='empty-coalesce',
    ),
    pytest.param(
        runtime('keyword', 'coalesce',
                fields=[runtime('keyword', 'coalesce', fields=[]), 'fallback']),
        ['fallback'], id='empty-child-coalesce',
    ),
    pytest.param(
        runtime('keyword', 'coalesce',
                fields=[runtime('keyword', 'substring', field='title', start=0, end=0),
                        'fallback']),
        [''], id='empty-string-is-not-missing',
    ),
    pytest.param(
        runtime('long', 'math', first='a', second='b'),
        [4], id='plain-math',
    ),
    pytest.param(
        runtime('long', 'date_interval', start_date='created', end_date='updated'),
        [2], id='plain-date-interval',
    ),
    pytest.param(
        runtime('date', 'latest_date', date_fields=['created', 'updated']),
        ['2026-01-03T00:00:00.000Z'], id='plain-latest-date',
    ),
    pytest.param(
        runtime('keyword', 'substring', field='title', start=1, end=3),
        ['bc'], id='plain-substring',
    ),
])
def test_runtime_script_execution(runtime_index, field, expected):
    session, url, index = runtime_index
    definition = ElasticRuntimeFields.convert_to_request(field)
    response = session.post(
        f'{url}/_scripts/painless/_execute',
        json={
            'script': definition['script'],
            'context': f'{field.type_}_field',
            'context_setup': {
                'index': index,
                'document': {
                    'a': 8, 'b': 2, 'c': 3, 'zero': 0,
                    'created': '2026-01-01', 'updated': '2026-01-03',
                    'title': 'abcdef', 'tags': ['beta', 'alpha'],
                    'fallback': 'fallback', 'flag': False,
                    'sentinel': ElasticRuntimeFields.NULL_SENTINEL,
                },
            },
        }, timeout=10,
    )
    assert response.status_code == 200, response.text
    assert response.json()['result'] == expected


def test_nested_runtime_mapping_search(runtime_index):
    session, url, index = runtime_index
    response = session.put(
        f'{url}/{index}/_doc/composed?refresh=true',
        json={'created': '2026-01-01', 'updated': '2026-01-03'}, timeout=10,
    )
    response.raise_for_status()
    field = runtime(
        'long', 'date_interval', start_date='created',
        end_date=runtime('date', 'latest_date', date_fields=['created', 'updated']),
    )
    response = session.post(
        f'{url}/{index}/_search',
        json={
            'runtime_mappings': {'elapsed': ElasticRuntimeFields.convert_to_request(field)},
            '_source': False,
            'fields': ['elapsed'],
            'query': {'range': {'elapsed': {'gte': 1, 'lte': 3}}},
            'sort': [{'elapsed': 'desc'}],
            'aggs': {'total_elapsed': {'sum': {'field': 'elapsed'}}},
        }, timeout=10,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert [hit['fields'] for hit in result['hits']['hits']] == [{'elapsed': [2]}]
    assert result['aggregations']['total_elapsed']['value'] == 2


@pytest.mark.parametrize('function', ['math', 'latest_date'])
def test_shared_child_execution(runtime_index, function):
    session, url, index = runtime_index
    if function == 'math':
        child = runtime('long', 'math', first='a', second='b', operation='+')
        field = runtime('long', 'math', first=child, second=child, operation='+')
        expected = [20]
    else:
        child = runtime('date', 'latest_date', date_fields=['created'])
        field = runtime('date', 'latest_date', date_fields=[child, child])
        expected = ['2026-01-01T00:00:00.000Z']
    definition = ElasticRuntimeFields.convert_to_request(field)
    response = session.post(
        f'{url}/_scripts/painless/_execute',
        json={
            'script': definition['script'],
            'context': f'{field.type_}_field',
            'context_setup': {
                'index': index, 'document': {'a': 8, 'b': 2, 'created': '2026-01-01'},
            },
        }, timeout=10,
    )
    assert response.status_code == 200, response.text
    assert response.json()['result'] == expected
