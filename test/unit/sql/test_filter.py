import pytest

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from tol.core import DataSourceFilter
from tol.sql import model_base
from tol.sql.filter import DefaultDatabaseFilter


BaseModel = model_base()


class FilterExample(BaseModel):
    __tablename__ = 'filter_example'

    id = Column(String, primary_key=True)
    text_column = Column(String)
    int_column = Column(Integer)
    bool_column = Column(Boolean)
    list_column = Column(JSONB)


def compile_filter(field, operator, constraint, literal_binds=True):
    converter = DefaultDatabaseFilter(DataSourceFilter(and_={field: {operator: constraint}}))
    query = converter.filter(converter.get_query(FilterExample))
    compiled = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={'literal_binds': literal_binds}
    )
    return str(compiled) if literal_binds else compiled


class TestSqlFilterOptions:
    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('match_anywhere', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_contains_options(self, case_insensitive, match_anywhere, negate):
        constraint = {'value': 'Abc', 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        if match_anywhere is not None:
            constraint['match_anywhere'] = match_anywhere
        observed = compile_filter('text_column', 'contains', constraint)
        comparison = 'ILIKE' if case_insensitive is not False else 'LIKE'
        if negate:
            comparison = f'NOT {comparison}'
        pattern = '%%Abc%%' if match_anywhere is not False else 'Abc%%'
        assert f"{comparison} '{pattern}'" in observed
        assert 'ESCAPE' in observed
        assert ('IS NULL' in observed) == negate

    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_eq_options(self, case_insensitive, negate):
        constraint = {'value': 'Abc', 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        observed = compile_filter('text_column', 'eq', constraint)
        if case_insensitive:
            comparison = 'NOT ILIKE' if negate else 'ILIKE'
            assert f"{comparison} 'Abc'" in observed
            assert 'ESCAPE' in observed
        else:
            comparison = '!=' if negate else '='
            assert f"{comparison} 'Abc'" in observed
            assert 'ILIKE' not in observed
        assert ('IS NULL' in observed) == negate

    @pytest.mark.parametrize('case_insensitive', [None, False, True])
    @pytest.mark.parametrize('match_anywhere', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_in_list_options(self, case_insensitive, match_anywhere, negate):
        constraint = {'value': ['Abc', 'Def'], 'negate': negate}
        if case_insensitive is not None:
            constraint['case_insensitive'] = case_insensitive
        if match_anywhere is not None:
            constraint['match_anywhere'] = match_anywhere
        observed = compile_filter('text_column', 'in_list', constraint)
        if case_insensitive or match_anywhere:
            comparison = 'ILIKE' if case_insensitive else 'LIKE'
            for value in ('Abc', 'Def'):
                pattern = f'%%{value}%%' if match_anywhere else value
                assert f"{comparison} '{pattern}'" in observed
            assert ' OR ' in observed
            assert 'ESCAPE' in observed
        else:
            assert "IN ('Abc', 'Def')" in observed
        assert ('IS NULL' in observed) == negate

    @pytest.mark.parametrize('operator', ['contains', 'eq', 'in_list'])
    def test_literal_sql_wildcards(self, operator):
        value = r'a%b_c\d'
        constraint = {'value': [value] if operator == 'in_list' else value,
                      'case_insensitive': True}
        compiled = compile_filter('text_column', operator, constraint, literal_binds=False)
        expected = r'a\%b\_c\\d'
        if operator == 'contains':
            expected = f'%{expected}%'
        assert expected in compiled.params.values()
        assert 'ESCAPE' in str(compiled)

    @pytest.mark.parametrize('operator', ['eq', 'in_list'])
    @pytest.mark.parametrize('field,value', [('int_column', 5), ('bool_column', True)])
    def test_non_string_options(self, operator, field, value):
        constraint = {'value': [value] if operator == 'in_list' else value,
                      'case_insensitive': True, 'match_anywhere': True}
        observed = compile_filter(field, operator, constraint)
        assert 'LIKE' not in observed
        if operator == 'in_list':
            assert ' IN ' in observed
        else:
            assert ' = ' in observed

    def test_array_contains_options_preserve_containment(self):
        compiled = compile_filter('list_column', 'contains', {
            'value': 'Abc', 'case_insensitive': True, 'match_anywhere': True
        }, literal_binds=False)
        assert '@>' in str(compiled)
        assert 'CASE WHEN' in str(compiled)
        assert ['Abc'] in compiled.params.values()

    @pytest.mark.parametrize('operator', ['contains', 'eq', 'in_list'])
    @pytest.mark.parametrize('search_values', [None, False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_json_dictionary_values(self, operator, search_values, negate):
        constraint = {'value': ['Abc'] if operator == 'in_list' else 'Abc',
                      'negate': negate}
        if search_values is not None:
            constraint['search_values'] = search_values
        compiled = compile_filter('list_column', operator, constraint, literal_binds=False)
        observed = str(compiled)
        assert ('jsonb_each' in observed) == (search_values is not False)
        if search_values is not False:
            assert 'EXISTS' in observed
            assert 'CASE WHEN' in observed
            assert 'filter_example.id' not in observed.split('EXISTS', 1)[1]
        assert ('IS NULL' in observed) == negate

    @pytest.mark.parametrize('operator', ['contains', 'eq', 'in_list'])
    @pytest.mark.parametrize('value', [42, True, None, '42'])
    def test_json_value_types(self, operator, value):
        compiled = compile_filter('list_column', operator, {
            'value': [value] if operator == 'in_list' else value
        }, literal_binds=False)
        assert 'jsonb_each' in str(compiled)
        if operator != 'contains' or not isinstance(value, str):
            assert any(
                type(parameter) is type(value) and parameter == value
                for parameter in compiled.params.values()
            )

    @pytest.mark.parametrize('operator', ['contains', 'eq', 'in_list'])
    @pytest.mark.parametrize('case_insensitive', [False, True])
    @pytest.mark.parametrize('match_anywhere', [False, True])
    def test_json_string_options(self, operator, case_insensitive, match_anywhere):
        compiled = compile_filter('list_column', operator, {
            'value': ['Abc'] if operator == 'in_list' else 'Abc',
            'case_insensitive': case_insensitive, 'match_anywhere': match_anywhere
        }, literal_binds=False)
        observed = str(compiled)
        uses_pattern = operator == 'contains' or case_insensitive \
            or (operator == 'in_list' and match_anywhere)
        assert ('LIKE' in observed) == bool(uses_pattern)
        if uses_pattern:
            assert ('ILIKE' in observed) == case_insensitive
            pattern = 'Abc'
            if match_anywhere and operator != 'eq':
                pattern = '%Abc%'
            elif operator == 'contains':
                pattern = 'Abc%'
            assert pattern in compiled.params.values()

    def test_json_empty_list(self):
        compiled = compile_filter('list_column', 'in_list', {'value': []}, literal_binds=False)
        assert 'WHERE false' in str(compiled)

    @pytest.mark.parametrize('case_insensitive', [False, True])
    @pytest.mark.parametrize('match_anywhere', [False, True])
    @pytest.mark.parametrize('negate', [False, True])
    def test_empty_list(self, case_insensitive, match_anywhere, negate):
        observed = compile_filter('text_column', 'in_list', {
            'value': [], 'case_insensitive': case_insensitive,
            'match_anywhere': match_anywhere, 'negate': negate,
        })
        assert 'LIKE' not in observed
        if case_insensitive or match_anywhere:
            assert f"WHERE {'true' if negate else 'false'}" in observed
        else:
            assert 'IN (NULL)' in observed
            assert ('IS NULL' in observed) == negate