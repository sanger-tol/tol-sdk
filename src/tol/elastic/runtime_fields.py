# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ..core import FieldNameOrRuntimeField, RuntimeField, RuntimeFields


@dataclass(frozen=True)
class _FieldValue:
    setup: str
    exists: str
    first: str
    values: str


class _ScriptCompiler:
    """Compile children into list-returning functions, never rewriting user scripts."""

    def __init__(self) -> None:
        self.params: dict[str, Any] = {}
        self.functions: list[str] = []
        self.children: dict[int, str] = {}
        self.active: set[int] = set()

    def compile(self, field: RuntimeField) -> tuple[str, dict[str, Any]]:
        body = self._body(field, 'emit')
        return '\n'.join([*self.functions, body]), self.params

    def _body(self, field: RuntimeField, output: str) -> str:
        if id(field) in self.active:
            raise ValueError('Cyclic runtime field dependency')
        generators = {
            'date_interval': self._date_interval,
            'latest_date': self._latest_date,
            'math': self._math,
            'coalesce': self._coalesce,
            'substring': self._substring,
        }
        if field.function not in generators:
            raise ValueError(f'Unsupported runtime field function: {field.function!r}')
        return_types = {
            'date_interval': ('long', 'double'),
            'latest_date': ('date',),
            'math': ('long', 'double'),
            'substring': ('keyword',),
        }
        if field.function in return_types and field.type_ not in return_types[field.function]:
            raise ValueError(
                f'Unsupported return type {field.type_!r} for {field.function!r}'
            )
        self.active.add(id(field))
        try:
            return generators[field.function](
                output=output,
                return_type=field.type_,
                **(field.function_kwargs or {}),
            )
        finally:
            self.active.remove(id(field))

    def _resolve(
        self,
        field: FieldNameOrRuntimeField,
        *,
        keyword: bool = False,
        expected_types: tuple[str, ...] = (),
    ) -> _FieldValue:
        if isinstance(field, str):
            name = field + ('.keyword' if keyword else '')
            name = name.replace('\\', '\\\\').replace("'", "\\'")
            values = f"doc['{name}']"
            return _FieldValue(
                setup='',
                exists=f"doc.containsKey('{name}') && {values}.size() > 0",
                first=f'{values}.value',
                values=values,
            )
        if not isinstance(field, RuntimeField):
            raise TypeError('Field arguments must be attribute names or RuntimeField instances')
        if field.script is not None or field.function is None:
            raise ValueError(
                'Nested runtime fields must use a built-in function, not a raw script '
                'or a type-only definition'
            )
        if expected_types and field.type_ not in expected_types:
            raise ValueError(
                f'Expected nested runtime field type in {expected_types}, got {field.type_!r}'
            )
        if id(field) in self.active:
            raise ValueError('Cyclic runtime field dependency')
        if id(field) not in self.children:
            name = f'_tol_evaluate_{len(self.children)}'
            self.children[id(field)] = name
            body = self._body(field, 'result.add')
            self.functions.append(f"""
                List {name}(def doc, def params) {{
                    List result = new ArrayList();
                    {body}
                    return result;
                }}
            """)
        name = self.children[id(field)]
        values = name.replace('_evaluate_', '_values_')
        return _FieldValue(
            setup=f'def {values} = {name}(doc, params);',
            exists=f'{values}.size() > 0',
            first=f'{values}.get(0)',
            values=values,
        )

    @staticmethod
    def _guard(fields: Sequence[_FieldValue], body: str) -> str:
        setup = '\n'.join(dict.fromkeys(field.setup for field in fields))
        condition = ' && '.join(field.exists for field in fields) or '1==1'
        return f'{setup}\nif ({condition}) {{ {body} }}'

    @staticmethod
    def _output(value: str, return_type: str, output: str) -> str:
        if return_type == 'date' and output == 'emit':
            value = f'{value}.toInstant().toEpochMilli()'
        elif return_type == 'long':
            value = f'((Number) {value}).longValue()'
        elif return_type == 'double':
            value = f'((Number) {value}).doubleValue()'
        return f'{output}({value});'

    def _date_interval(
        self, *, start_date: FieldNameOrRuntimeField, end_date: FieldNameOrRuntimeField,
        unit: str = 'days', output: str, return_type: str,
    ) -> str:
        start = self._resolve(start_date, expected_types=('date',))
        end = self._resolve(end_date, expected_types=('date',))
        value = '(double) differenceInMillis' if return_type == 'double' else 'differenceInMillis'
        return self._guard([start, end], f"""
            ZonedDateTime start = {start.first};
            ZonedDateTime end = {end.first};
            long differenceInMillis = ChronoUnit.{unit.upper()}.between(start, end);
            {output}({value});
        """)

    def _latest_date(
        self, *, date_fields: list[FieldNameOrRuntimeField], allow_missing: bool = True,
        output: str, return_type: str,
    ) -> str:
        fields = [self._resolve(field, expected_types=('date',)) for field in date_fields]
        # Keep names in params for ordinary inputs; nested inputs are local lists, not names.
        if all(isinstance(field, str) for field in date_fields):
            key = 'dates' if 'dates' not in self.params else f'dates_{len(self.params)}'
            self.params[key] = date_fields
            body = f"""
                for (int i = 0; i < params.{key}.size(); i++) {{
                    String dep = params.{key}.get(i);
                    if (doc.containsKey(dep) && doc[dep].size() > 0) {{
                        ZonedDateTime currentDate = doc[dep].value;
                        if (latestDate == null || currentDate.isAfter(latestDate)) {{
                            latestDate = currentDate;
                        }}
                    }}
                }}
            """
        else:
            body = '\n'.join(f"""
                if ({field.exists}) {{
                    ZonedDateTime currentDate = {field.first};
                    if (latestDate == null || currentDate.isAfter(latestDate)) {{
                        latestDate = currentDate;
                    }}
                }}
            """ for field in fields)
        result = f"""
            ZonedDateTime latestDate = null;
            {body}
            if (latestDate != null) {{
                {self._output('latestDate', return_type, output)}
            }}
        """
        if allow_missing:
            setup = '\n'.join(dict.fromkeys(field.setup for field in fields))
            return self._guard([], setup + result)
        return self._guard(fields, result)

    def _math(
        self, *, first: FieldNameOrRuntimeField, second: FieldNameOrRuntimeField,
        operation: str = '/', output: str, return_type: str,
    ) -> str:
        if operation not in ('+', '-', '*', '/', '%'):
            raise ValueError(f'Unsupported runtime field math operation: {operation!r}')
        first_value = self._resolve(first, expected_types=('long', 'double'))
        second_value = self._resolve(second, expected_types=('long', 'double'))
        value = f'({first_value.first} {operation} {second_value.first})'
        return self._guard(
            [first_value, second_value], self._output(value, return_type, output),
        )

    def _coalesce(
        self, *, fields: list[FieldNameOrRuntimeField], null_wins: bool = False,
        output: str, return_type: str,
    ) -> str:
        if not fields:
            return 'return;' if output == 'emit' else ''
        branches = ''
        fallback_needs_scope = False
        for field in reversed(fields):
            expected_types = ('long', 'double') if return_type in ('long', 'double') \
                else (return_type,)
            value = self._resolve(
                field, keyword=return_type == 'keyword', expected_types=expected_types,
            )
            # Child evaluation must stay inside its fallback branch.
            fallback = (
                f'else {{ {branches} }}' if fallback_needs_scope else f'else {branches}'
            ) if branches else ''
            stop = 'return;' if null_wins and return_type == 'keyword' and output == 'emit' else ''
            branches = f"""
                {value.setup}
                if ({value.exists}) {{
                    for (def value : {value.values}) {{
                        {self._output('value', return_type, output)}
                    }}
                    {stop}
                }}
            """ + fallback
            fallback_needs_scope = bool(value.setup)
        return self._guard([], branches)

    def _substring(
        self, *, field: FieldNameOrRuntimeField, start: int, end: int,
        output: str, return_type: str,
    ) -> str:
        value = self._resolve(field, keyword=return_type == 'keyword', expected_types=('keyword',))
        return self._guard(
            [value],
            self._output(f'{value.first}.substring({start}, {end})', return_type, output),
        )


class ElasticRuntimeFields(RuntimeFields):
    NULL_SENTINEL = '__TOL_PROVENANCE_NULL__'

    @classmethod
    def convert_to_request(cls, runtime_field: RuntimeField):
        if runtime_field.function is not None:
            generator = getattr(cls, f'{runtime_field.function}_script', None)
            if generator is None:
                raise ValueError(
                    f'Unsupported runtime field function: {runtime_field.function!r}'
                )
            script, params = generator(
                _return_type=runtime_field.type_,
                **(runtime_field.function_kwargs or {}),
            )
            return {
                'type': runtime_field.type_,
                'script': {'source': script, 'params': params},
            }
        elif runtime_field.script is not None:
            return {
                'type': runtime_field.type_,
                'script': {'source': runtime_field.script},
            }
        else:
            return {'type': runtime_field.type_}

    @classmethod
    def generate_function_script(
        cls, *, dependencies: list[str], function_body: str, function_default: str = '',
    ) -> str:
        """Wrap a low-level script body with guards for indexed field names."""
        compiler = _ScriptCompiler()
        fields = [compiler._resolve(field) for field in dependencies]
        script = _ScriptCompiler._guard(fields, function_body)
        return script + (f' else {{ {function_default} }}' if function_default else '')

    @classmethod
    def _function_script(
        cls, function: str, return_type: str, **kwargs: Any,
    ) -> tuple[str, dict[str, Any]]:
        return _ScriptCompiler().compile(RuntimeField(
            type_=return_type, function=function, function_kwargs=kwargs,
        ))

    @classmethod
    def date_interval_script(
        cls, *, start_date: FieldNameOrRuntimeField, end_date: FieldNameOrRuntimeField,
        unit: str = 'days', _return_type: str = 'long',
    ) -> tuple[str, dict[str, Any]]:
        return cls._function_script(
            'date_interval', _return_type, start_date=start_date, end_date=end_date, unit=unit,
        )

    @classmethod
    def latest_date_script(
        cls, *, date_fields: list[FieldNameOrRuntimeField], allow_missing: bool = True,
        _return_type: str = 'date',
    ) -> tuple[str, dict[str, Any]]:
        return cls._function_script(
            'latest_date', _return_type, date_fields=date_fields, allow_missing=allow_missing,
        )

    @classmethod
    def math_script(
        cls, *, first: FieldNameOrRuntimeField, second: FieldNameOrRuntimeField,
        operation: str = '/', _return_type: str = 'double',
    ) -> tuple[str, dict[str, Any]]:
        return cls._function_script(
            'math', _return_type, first=first, second=second, operation=operation,
        )

    @classmethod
    def coalesce_script(
        cls, *, fields: list[FieldNameOrRuntimeField], _return_type: str = 'keyword',
        null_wins: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        return cls._function_script(
            'coalesce', _return_type, fields=fields, null_wins=null_wins,
        )

    @classmethod
    def substring_script(
        cls, *, field: FieldNameOrRuntimeField, start: int, end: int,
        _return_type: str = 'keyword',
    ) -> tuple[str, dict[str, Any]]:
        return cls._function_script(
            'substring', _return_type, field=field, start=start, end=end,
        )
