# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

class RuntimeFields:
    @classmethod
    def date_interval(cls, start_name: str, end_name: str, unit: str = 'days'):
        return {
            'type': 'long',
            'script': f"""
                if (doc.containsKey('{start_name}') && doc.containsKey('{end_name}')) {{
                    if (doc['{start_name}'].size() > 0
                        && doc['{end_name}'].size() > 0) {{
                        ZonedDateTime start = doc['{start_name}'].value;
                        ZonedDateTime end = doc['{end_name}'].value;
                        long differenceInMillis = ChronoUnit.{unit.upper()}.between(start, end);
                        emit(differenceInMillis)
                    }}
                }}
            """
        }

    @classmethod
    def math(cls, first: str, second: str, operation: str = '/',
             return_type: str = 'double'):
        return {
            'type': f'{return_type}',
            'script': f"""
                if (doc.containsKey('{first}') && doc.containsKey('{second}')) {{
                if (doc['{first}'].size() > 0
                        && doc['{second}'].size() > 0) {{
                        emit(doc['{first}'].value {operation} doc['{second}'].value)
                    }}
                }}
            """
        }

    @classmethod
    def coalesce(cls, fields: list[str]):
        return {
            'type': 'keyword',
            'script': 'else '.join(
                [
                    f"if (doc.containsKey('{field}.keyword') "
                    f"&& doc['{field}.keyword'].size() > 0) {{"
                    f"emit(doc['{field}.keyword'].value);"
                    f'}}'
                    for field in fields
                ]
            )
        }
