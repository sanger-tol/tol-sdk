# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

class RuntimeField:
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
            if isinstance(dependency, RuntimeField):
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


class RuntimeFields:
    @classmethod
    def date_interval(cls, start_name: str, end_name: str, unit: str = 'days'):
        rf = RuntimeField(
            field_type='long',
            dependencies=[start_name, end_name],
            function_body=f"""
                ZonedDateTime start = doc['{start_name}'].value;
                ZonedDateTime end = doc['{end_name}'].value;
                long differenceInMillis = ChronoUnit.{unit.upper()}.between(start, end);
                emit(differenceInMillis);
            """
        )
        return rf.to_dict()

    @classmethod
    def latest_date(cls, date_fields: list[str], allow_missing: bool = True):
        deps = date_fields if not allow_missing else []
        rf = RuntimeField(
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
        rf = RuntimeField(
            field_type=return_type,
            dependencies=[first, second],
            function_body=f"""
                emit(doc['{first}'].value {operation} doc['{second}'].value)
            """
        )
        return rf.to_dict()

    @classmethod
    def coalesce(cls, fields: list[str], return_type: str = 'keyword'):
        keyword = '.keyword' if return_type == 'keyword' else ''
        rf = RuntimeField(
            field_type=return_type,
            dependencies=[],  # No dependencies as we check in function_body
            function_body='else '.join(
                [
                    f"if (doc.containsKey('{field}{keyword}') "
                    f"&& doc['{field}{keyword}'].size() > 0) {{"
                    f"emit(doc['{field}{keyword}'].value);"
                    f'}}'
                    for field in fields
                ]
            )
        )
        return rf.to_dict()
