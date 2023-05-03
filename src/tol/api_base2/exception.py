# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional


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


class UnknownObjectTypeException(BaseRuntimeException):
    def __init__(self, object_type: str) -> None:
        errors = [{
            'title': 'Unknown Object Type',
            'detail': f'The object type "{object_type}" is unknown.'
        }]
        super().__init__(errors, status_code=404)


class ObjectNotFoundByIdException(BaseRuntimeException):
    def __init__(self, object_type: str, id_: str) -> None:
        errors = [{
            'title': 'Object Not Found',
            'detail': f'No "{object_type}" object was found with id "{id_}".'
        }]
        super().__init__(errors, status_code=404)


class UnsupportedOpertionError(BaseRuntimeException):
    def __init__(self, object_type: str, operation: str) -> None:
        errors = [{
            'title': 'Unsupported Operation',
            'detail': f'Cannot perform "{operation}" on type "{object_type}".'
        }]
        super().__init__(errors, status_code=400)


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
            f'The query-string argument with key "{__key}" and value '
            f'{__value} is invalid.'
        )
        if message is None:
            return detail
        return f'{detail}\n\n{message}'
