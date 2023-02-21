# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List


class _CustomException(Exception):
    def __init__(self, errors: List[Dict] = None, status_code: int = 500):
        """Each dict element of errors should have:
        - title - the name of the error
        - detail - a short description of what caused the error
        """
        self.errors = errors
        self.status_code = status_code

    def to_dict(self):
        return {
            'errors': self.errors
        }


class IdNotFoundException(_CustomException):
    def __init__(self, type_: str, id_: int):
        errors = [{
            'title': 'Not Found',
            'detail': f'No {type_} with id {id_} was found.'
        }]
        super().__init__(
            errors=errors,
            status_code=404
        )


class EnumNameNotFoundException(_CustomException):
    def __init__(self, type_: str, name: str):
        errors = [{
            'title': 'Not Found',
            'detail': f"No name '{name}' exists on enum {type_}."
        }]
        super().__init__(
            errors=errors,
            status_code=404
        )


class BadParameterException(_CustomException):
    def __init__(self, message: str):
        errors = [{
            'title': 'Bad Request',
            'detail': message
        }]
        super().__init__(
            errors=errors,
            status_code=400
        )


class CandidateKeyNotProvidedExpection(_CustomException):
    def __init__(self):
        errors = [{
            'title': 'Bad Request',
            'detail': 'Candidate key was not provided'
        }]
        super().__init__(errors, 400)


class ExtraFieldsNotPermittedException(_CustomException):
    def __init__(self):
        errors = [{
            'title': 'Bad Request',
            'detail': 'Extra fields are not permitted on this type.'
        }]
        super().__init__(errors, 400)


class BadParameterStringException(_CustomException):
    def __init__(self, message):
        errors = [{
            'title': 'Bad Parameter String',
            'detail': message
        }]
        super().__init__(errors, 400)


class BadTargetServiceException(_CustomException):
    def __init__(self, target_service):
        errors = [{
            'title': 'Bad Target Service',
            'detail': f"No endpoint exists with name '{target_service}'."
        }]
        super().__init__(errors, 400)


class WildcardFilterOnNonStringColumn(_CustomException):
    def __init__(self, filter_column):
        errors = [{
            'title': 'Wildcard filter on non-string column',
            'detail': f'The field {filter_column} is not a string.'
        }]
        super().__init__(errors, 400)
