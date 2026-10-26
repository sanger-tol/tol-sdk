# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from ..core import RuntimeField, RuntimeFields


class ElasticRuntimeFields(RuntimeFields):
    NULL_SENTINEL = '__TOL_PROVENANCE_NULL__'

    @classmethod
    def convert_to_request(cls, runtime_field: RuntimeField):
        if runtime_field.function is not None:
            function_script_generator = getattr(cls, f'{runtime_field.function}_script')
            script, params = function_script_generator(
                _return_type=runtime_field.type,
                **runtime_field.function_kwargs or {}
            )

            return {
                'type': runtime_field.type,
                'script': {
                    'source': script,
                    'params': params
                }
            }
        else:  # is a script runtime field
            return {
                'type': runtime_field.type,
                'script': {'source': runtime_field.script}
            }

    @classmethod
    def __generate_dependencies_exist_guard(cls, dependencies: list[str]):
        if dependencies:
            # Return the two checks that need to be made for each dependency, for every dependency
            # (separated by && operators)
            return ' && '.join([
                f"doc.containsKey('{dep}') && "
                f"doc['{dep}'].size() > 0" for dep in dependencies
            ])
        else:
            # If this runtime field has no dependencies, there doesn't need to be a guard,
            # so return a condition that always passes
            return '1==1'

    @classmethod
    def generate_function_script(
        cls,
        *,
        dependencies: list[str],
        function_body: str,
        function_default: str = '',  # An empty string is instead of `| None`
    ) -> str:
        """
        The main part of the script comes from `function_body`, but this method should be wrapped
        around it to add an if guard for dependencies that may not exist.
        If there's a `function_default`, it will be used in the script instead of `function_body`
        if the if guard for the dependencies fails.
        """
        dependencies_guard_condition = cls.__generate_dependencies_exist_guard(dependencies)

        return f"""
            if ({dependencies_guard_condition}) {{
                {function_body}
            }} else {{
                {function_default}
            }}
        """

    @classmethod
    def date_interval_script(
        cls,
        *,
        start_date: str,
        end_date: str,
        unit: str = 'days'
    ) -> tuple[str, dict[str, Any]]:
        script = cls.generate_function_script(
            dependencies=[start_date, end_date],
            function_body=f"""
                ZonedDateTime start = doc['{start_date}'].value;
                ZonedDateTime end = doc['{end_date}'].value;
                long differenceInMilis = ChronoUnit.{unit.upper()}.between(start, end);
                emit(differenceInMilis);
            """
        )
        return script, {}

    @classmethod
    def latest_date_script(
        cls,
        *,
        date_fields: list[str],
        allow_missing: bool = True
    ) -> tuple[str, dict[str, Any]]:
        deps = date_fields if not allow_missing else []
        script = cls.generate_function_script(
            dependencies=deps,
            function_body="""
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
            """
        )
        return script, {'dates': date_fields}

    @classmethod
    def math_script(
        cls,
        *,
        first: str,
        second: str,
        operation: str = '/'
    ) -> tuple[str, dict[str, Any]]:
        script = cls.generate_function_script(
            dependencies=[first, second],
            function_body=f"""
                emit(doc['{first}'].value {operation} doc['{second}'].value)
            """
        )
        return script, {}

    @classmethod
    def coalesce_script(
        cls,
        *,
        _return_type: str = 'keyword',
        fields: list[str],
        null_wins: bool = False,
    ) -> tuple[str, dict[str, Any]]:
        keyword = '.keyword' if _return_type == 'keyword' else ''
        if _return_type == 'date':
            emit_value = 'value.toInstant().toEpochMilli()'
        elif _return_type == 'long':
            emit_value = '((Number) value).longValue()'
        elif _return_type == 'double':
            emit_value = '((Number) value).doubleValue()'
        else:
            emit_value = 'value'
        if null_wins and _return_type == 'keyword':
            # sentinel is a real indexed keyword value written at upsert time;
            # standard size > 0 check is sufficient to find it.
            function_body = 'else '.join(
                [
                    f"if (doc.containsKey('{field}{keyword}') "
                    f"&& doc['{field}{keyword}'].size() > 0) {{"
                    f"for (def value : doc['{field}{keyword}']) {{emit({emit_value});}}"
                    f'return;'
                    f'}}'
                    for field in fields
                ]
            )
        else:
            function_body = 'else '.join(
                [
                    f"if (doc.containsKey('{field}{keyword}') "
                    f"&& doc['{field}{keyword}'].size() > 0) {{"
                    f"for (def value : doc['{field}{keyword}']) {{emit({emit_value});}}"
                    f'}}'
                    for field in fields
                ]
            )

        script = cls.generate_function_script(
            dependencies=[],  # No dependencies as we check in function_body
            function_body=function_body
        )
        return script, {}

    @classmethod
    def substring_script(
        cls,
        *,
        _return_type = 'keyword',
        field: str,
        start: int,
        end: int,
    ) -> tuple[str, dict[str, Any]]:
        keyword = '.keyword' if _return_type == 'keyword' else ''

        script = cls.generate_function_script(
            dependencies=[f'{field}{keyword}'],
            function_body=f"emit(doc['{field}{keyword}'].value.substring({start}, {end}));"
        )
        return script, {}


# TODO How does it know what `field_type` is currently when it's a function runtime field?
class ElasticRuntimeField:
    def __init__(
            self,
            field_type: str,
            dependencies: list[str],
            function_body: str,
            function_default: str = '',
            params: dict = {},
            **kwargs
    ):
        self.field_type = field_type
        self.dependencies = self.__unpack_dependencies(dependencies)
        self.function_body = function_body
        self.function_default = function_default
        self.params = params
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __unpack_dependencies(self, dependencies):
        ret = []
        for dependency in dependencies:
            if isinstance(dependency, ElasticRuntimeField):
                ret.extend(dependency.dependencies)
            else:
                ret.append(dependency)
        return ret

    def __if_dependencies_exist(self):
        conditions = [
            f"doc.containsKey('{dep}') && "
            f"doc['{dep}'].size() > 0" for dep in self.dependencies
        ]
        if self.dependencies:
            return (
                f"if ({' && '.join(conditions)})"
            )
        return 'if (1==1)'

    def to_function(self):
        main_body = f"""
            {self.__if_dependencies_exist()} {{
                {self.function_body}
            }}
        """
        if self.function_default:
            main_body += f"""
                else {{
                    {self.function_default}
                }}
            """
        return f'{main_body}'

    def to_dict(self):
        return {
            'type': self.field_type,
            'script': {
                'source': self.to_function(),
                'params': self.params
            }
        }


class LEGACYElasticRuntimeFields:
    NULL_SENTINEL = '__TOL_PROVENANCE_NULL__'

    @classmethod
    def date_interval(cls, start_date: str, end_date: str, unit: str = 'days'):
        rf = ElasticRuntimeField(
            field_type='long',
            dependencies=[start_date, end_date],
            function_body=f"""
                ZonedDateTime start = doc['{start_date}'].value;
                ZonedDateTime end = doc['{end_date}'].value;
                long differenceInMillis = ChronoUnit.{unit.upper()}.between(start, end);
                emit(differenceInMillis);
            """
        )
        return rf.to_dict()

    @classmethod
    def latest_date(cls, date_fields: list[str], allow_missing: bool = True):
        deps = date_fields if not allow_missing else []
        rf = ElasticRuntimeField(
            field_type='date',
            dependencies=deps,
            params={'dates': date_fields},
            function_body="""
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
            """
        )
        return rf.to_dict()

    @classmethod
    def math(cls, first: str, second: str, operation: str = '/',
             return_type: str = 'double'):
        rf = ElasticRuntimeField(
            field_type=return_type,
            dependencies=[first, second],
            function_body=f"""
                emit(doc['{first}'].value {operation} doc['{second}'].value)
            """
        )
        return rf.to_dict()

    @classmethod
    def coalesce(
            cls,
            fields: list[str],
            return_type: str = 'keyword',
            null_wins: bool = False
    ):
        keyword = '.keyword' if return_type == 'keyword' else ''
        if return_type == 'date':
            emit_value = 'value.toInstant().toEpochMilli()'
        elif return_type == 'long':
            emit_value = '((Number) value).longValue()'
        elif return_type == 'double':
            emit_value = '((Number) value).doubleValue()'
        else:
            emit_value = 'value'
        if null_wins and return_type == 'keyword':
            # sentinel is a real indexed keyword value written at upsert time;
            # standard size > 0 check is sufficient to find it.
            function_body = 'else '.join(
                [
                    f"if (doc.containsKey('{field}{keyword}') "
                    f"&& doc['{field}{keyword}'].size() > 0) {{"
                    f"for (def value : doc['{field}{keyword}']) {{emit({emit_value});}}"
                    f'return;'
                    f'}}'
                    for field in fields
                ]
            )
            params = {}
        else:
            function_body = 'else '.join(
                [
                    f"if (doc.containsKey('{field}{keyword}') "
                    f"&& doc['{field}{keyword}'].size() > 0) {{"
                    f"for (def value : doc['{field}{keyword}']) {{emit({emit_value});}}"
                    f'}}'
                    for field in fields
                ]
            )
            params = {}
        rf = ElasticRuntimeField(
            field_type=return_type,
            dependencies=[],  # No dependencies as we check in function_body
            function_body=function_body,
            params=params,
        )
        return rf.to_dict()

    @classmethod
    def substring(cls, field: str, start: int, end: int, return_type: str = 'keyword'):
        keyword = '.keyword' if return_type == 'keyword' else ''
        rf = ElasticRuntimeField(
            field_type=return_type,
            dependencies=[f'{field}{keyword}'],
            function_body=f"emit(doc['{field}{keyword}'].value.substring({start}, {end}));"
        )
        return rf.to_dict()
