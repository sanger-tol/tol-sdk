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
        assert 'LIKE' not in str(compiled)
        assert ['Abc'] in compiled.params.values()

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