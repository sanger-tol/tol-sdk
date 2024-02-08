# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional, Type

from ..core import DataSource


class BaseRuntimeException(Exception):
    def __init__(
        self,
        errors: List[Dict[str, Any]],
        status_code: int = 500
    ) -> None:
        self.__errors = errors
        self.__status_code = status_code

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """
        The list of errors, containing a title and detail each
        """
        return self.__errors

    @property
    def status_code(self) -> int:
        """
        The status code for the error response in Flask
        """
        return self.__status_code


class ObjectNotFoundByIdException(BaseRuntimeException):
    def __init__(self, object_type: str, id_: str) -> None:
        errors = [{
            'title': 'Object Not Found',
            'detail': f'No "{object_type}" object was found with id "{id_}".'
        }]
        super().__init__(errors, status_code=404)


class RecursiveRelationNotFoundException(BaseRuntimeException):
    def __init__(self) -> None:
        errors = [{
            'title': 'Relation Not Found',
            'detail': (
                'The specified to-one relation object was not found'
            )
        }]
        super().__init__(errors, status_code=404)


class UnsupportedOpertionError(BaseRuntimeException):
    def __init__(self, object_type: str, operation: str) -> None:
        errors = [{
            'title': 'Unsupported Operation',
            'detail': f'Cannot perform "{operation}" on type "{object_type}".'
        }]
        super().__init__(errors, status_code=400)


class UninheritedOperationError(BaseRuntimeException):
    def __init__(
        self,
        data_source: DataSource,
        operator_class: Type,
        method: str
    ) -> None:

        self.__detail = (
            f'The DataSource {type(data_source).__name__} must '
            f'inherit from {operator_class.__name__} to implement '
            f'the {method} method.'
        )
        errors = [{
            'title': 'Misconfigured DataSource',
            'detail': self.__detail
        }]
        super().__init__(errors, status_code=500)

    def __str__(self) -> str:
        return self.__detail


class BadQueryArgError(BaseRuntimeException):
    def __init__(
        self,
        __key: str,
        __value: str,
        message: Optional[str] = None
    ) -> None:
        errors = [{
            'title': 'Bad Query-String Argument',
            'detail': self.__get_detail(__key, __value, message)
        }]
        super().__init__(errors, status_code=400)

    def __get_detail(
        self,
        __key: str,
        __value: str,
        message: Optional[str]
    ) -> str:
        detail = (
            f'The query-string argument with key "{__key}" '
            f'is invalid.'
        )
        if message is None:
            return detail
        return f'{detail}\n\n{message}'


class BadPostJsonError(BaseRuntimeException):
    def __init__(
        self,
        __key: str,
        message: Optional[str] = None
    ) -> None:
        errors = [{
            'title': 'Bad POST JSON',
            'detail': self.__get_detail(__key, message)
        }]
        super().__init__(errors, status_code=400)

    def __get_detail(
        self,
        __key: str,
        message: Optional[str]
    ) -> str:
        detail = (
            f'The POSTed JSON must have a key "{__key}"'
        )
        if message is None:
            return detail
        return f'{detail}\n\n{message}'


class UnauthenticatedError(BaseRuntimeException):
    """
    Raise on any error condition that warrants a
    401: Unauthorized HTTP status code.
    """

    def __init__(self, detail: str) -> None:
        errors = [{
            'title': 'Unauthorized',
            'detail': detail
        }]
        super().__init__(errors, status_code=401)
