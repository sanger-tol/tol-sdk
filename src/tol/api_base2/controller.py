# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable

from .exception import (
    ObjectNotFoundByIdException,
    UnsupportedOpertionError
)
from .misc import ListGetParamaters
from .view import ResponseDict, View
from ..core import DataObject, DataSource


def validate(operation_name: str, api_full_name: str) -> Callable:
    """
    Validates a Controller method's corresponding operation
    is supported by its DataSource
    """
    def decorator(method: Callable) -> Callable:
        def wrapper(controller: Controller, object_type: str, *args, **kwargs) -> Any:
            if not controller.operation_is_supported(operation_name):
                raise UnsupportedOpertionError(object_type, api_full_name)
            return method(controller, object_type, *args, **kwargs)
        return wrapper
    return decorator


class Controller:
    """
    An MVC-esque Controller class, that fulfills requests.
    """

    def __init__(self, data_source: DataSource, view: View) -> None:
        self.__data_source = data_source
        self.__view = view

    def operation_is_supported(self, operation: str) -> bool:
        return operation in self.__data_source.supported_operations

    @validate('get_by_id', 'detail GET')
    def get_detail(self, object_type: str, object_id: str) -> ResponseDict:
        """
        Gets an individual object of specified type and id
        """
        data_object = self.__get_detail_object(object_type, object_id)
        return self.__view.dump(data_object)

    @validate('get_list_page', 'list GET')
    def get_list(
        self,
        object_type: str,
        query_args: ListGetParamaters
    ) -> ResponseDict:
        """
        Gets a page of list results of specified type.
        """
        page_number = self.__get_page_number_or_1(query_args)
        # TODO don't throw away the total DataObject count
        data_objects, _ = self.__data_source.get_list_page(
            object_type,
            page_number,
            page_size=query_args.page_size
        )
        return self.__view.dump_bulk(data_objects)

    def __get_detail_object(self, object_type: str, object_id: str) -> DataObject:
        data_objects = self.__data_source.get_by_id(object_type, [object_id])
        if len(data_objects) == 0 or data_objects[0] is None:
            raise ObjectNotFoundByIdException(object_type, object_id)
        return data_objects[0]

    def __get_page_number_or_1(self, query_args: ListGetParamaters) -> int:
        page_number = query_args.page_number
        if page_number is None:
            return 1
        return page_number
