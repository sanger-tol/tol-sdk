from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_elastic, elastic


class TestElasticContains:
    @against(elastic, api_elastic)
    def test_in_list_options(self, data_source: OperableDataSource, ds_sleep):
        values = {
            'lower': 'sapiens',
            'mixed': 'SAPIENS',
            'other': 'musculus',
            'mixed-other': 'MUSCULUS',
            'prefix': 'sapiens alpha',
            'middle': 'Homo sapiens alpha',
            'end': 'Homo sapiens',
            'mixed-middle': 'Homo SAPIENS alpha',
            'other-end': 'Mus musculus',
            'similar': 'sapienz',
            'literal': r'Homo a*b?c\d',
            'wildcard-decoy': r'Homo axbyc\d',
        }
        data_source.upsert('root', [
            data_source.data_object_factory(
                'root', object_id,
                attributes={
                    'str_column': value,
                    'int_column': position,
                    'bool_column': position % 2 == 0,
                },
            )
            for position, (object_id, value) in enumerate(values.items())
        ], provenance='source1')
        ds_sleep(7)

        for case_insensitive in (None, False, True):
            for match_anywhere in (None, False, True):
                expected = {'lower', 'other'}
                if case_insensitive:
                    expected.update({'mixed', 'mixed-other'})
                if match_anywhere:
                    expected.update({'prefix', 'middle', 'end', 'other-end'})
                    if case_insensitive:
                        expected.add('mixed-middle')
                options = {}
                if case_insensitive is not None:
                    options['case_insensitive'] = case_insensitive
                if match_anywhere is not None:
                    options['match_anywhere'] = match_anywhere
                for negate in (False, True):
                    for candidates in ([], ['sapiens', 'musculus']):
                        filters = DataSourceFilter(and_={
                            'id': {'in_list': {'value': list(values)}},
                            'str_column': {'in_list': {
                                'value': candidates, 'negate': negate, **options
                            }},
                        })
                        observed = {
                            obj.id for obj in data_source.get_list('root', object_filters=filters)
                        }
                        matches = expected if candidates else set()
                        expected_ids = set(values) - matches if negate else matches
                        assert observed == expected_ids, (
                            case_insensitive, match_anywhere, negate, candidates, observed
                        )

                for field, candidates, expected_ids in (
                    ('int_column', [0, 2], {'lower', 'other'}),
                    ('bool_column', [True], set(list(values)[::2])),
                ):
                    filters = DataSourceFilter(and_={
                        'id': {'in_list': {'value': list(values)}},
                        field: {'in_list': {'value': candidates, **options}},
                    })
                    assert {
                        obj.id for obj in data_source.get_list('root', object_filters=filters)
                    } == expected_ids

        literal_filter = DataSourceFilter(and_={'str_column': {'in_list': {
            'value': [r'a*b?c\d'], 'match_anywhere': True
        }}})
        assert {
            obj.id for obj in data_source.get_list('root', object_filters=literal_filter)
        } == {'literal'}

    @against(elastic, api_elastic)
    def test_eq_case_insensitive(self, data_source: OperableDataSource, ds_sleep):
        values = {
            'lower': 'homo sapiens',
            'mixed': 'Homo SAPIENS',
            'prefix': 'homo sapiens alpha',
            'substring': 'alpha homo sapiens',
            'similar': 'homo sapienz',
            'literal': 'Homo *sapiens?',
            'wildcard-decoy': 'Homo xsapiensx',
        }
        data_source.upsert('root', [
            data_source.data_object_factory(
                'root', object_id, attributes={'str_column': value}
            )
            for object_id, value in values.items()
        ], provenance='source1')
        ds_sleep(7)

        for case_insensitive in (None, False, True):
            expected = {'lower', 'mixed'} if case_insensitive else {'lower'}
            for negate in (False, True):
                constraint = {'value': 'homo sapiens', 'negate': negate}
                if case_insensitive is not None:
                    constraint['case_insensitive'] = case_insensitive
                filters = DataSourceFilter(and_={
                    'id': {'in_list': {'value': list(values)}},
                    'str_column': {'eq': constraint},
                })
                observed = {
                    obj.id for obj in data_source.get_list('root', object_filters=filters)
                }
                expected_ids = set(values) - expected if negate else expected
                assert observed == expected_ids, (case_insensitive, negate, observed)

        literal_filter = DataSourceFilter(and_={
            'str_column': {'eq': {
                'value': 'homo *sapiens?', 'case_insensitive': True
            }},
        })
        assert {
            obj.id for obj in data_source.get_list('root', object_filters=literal_filter)
        } == {'literal'}

    @against(elastic, api_elastic)
    def test_contains_options(self, data_source: OperableDataSource, ds_sleep):
        values = {
            'lower-prefix': 'sapiens alpha',
            'mixed-prefix': 'Sapiens alpha',
            'middle': 'Homo sapiens alpha',
            'mixed-middle': 'Homo SAPIENS alpha',
            'end': 'Homo sapiens',
            'similar': 'Homo sapienz',
            'literal': r'Homo a*b?c\d',
            'wildcard-decoy': r'Homo axbyc\d',
        }
        objects = [
            data_source.data_object_factory(
                'root', object_id, attributes={'str_column': value}
            )
            for object_id, value in values.items()
        ]
        data_source.upsert('root', objects, provenance='source1')
        ds_sleep(7)

        for case_insensitive in (None, False, True):
            for match_anywhere in (None, False, True):
                expected = {'lower-prefix'}
                if case_insensitive is not False:
                    expected.add('mixed-prefix')
                if match_anywhere:
                    expected.update({'middle', 'end'})
                    if case_insensitive is not False:
                        expected.add('mixed-middle')
                for negate in (False, True):
                    options = {}
                    if case_insensitive is not None:
                        options['case_insensitive'] = case_insensitive
                    if match_anywhere is not None:
                        options['match_anywhere'] = match_anywhere
                    filters = DataSourceFilter(
                        and_={
                            'id': {'in_list': {'value': list(values)}},
                            'str_column': {
                                'contains': {
                                    'value': 'sapiens', 'negate': negate, **options
                                }
                            },
                        },
                    )
                    observed = {
                        obj.id for obj in data_source.get_list('root', object_filters=filters)
                    }
                    expected_ids = set(values) - expected if negate else expected
                    assert observed == expected_ids, (
                        case_insensitive, match_anywhere, negate, observed
                    )

        literal_filter = DataSourceFilter(
            and_={'str_column': {'contains': {
                'value': r'a*b?c\d', 'match_anywhere': True
            }}},
        )
        assert {
            obj.id for obj in data_source.get_list('root', object_filters=literal_filter)
        } == {'literal'}