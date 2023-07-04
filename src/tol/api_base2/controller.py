# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable, Type

from .exception import (
    ObjectNotFoundByIdException,
    UninheritedOperationError,
    UnsupportedOpertionError
)
from .misc import (
    AggregationBody,
    AggregationParameters,
    ListGetParamaters
)
from .view import ResponseDict, View
from ..core import DataObject, OperableDataSource
from ..core.operator import Aggregator, DetailGetter, Operator, PageGetter


def __is_supported(
    operator_class: Type[Operator],
    operator_method: str,
    data_source: OperableDataSource,
) -> bool:
    """
    Returns `True` if the given `DataSource` instance implements
    the specified `Operator` class.

    If it doesn't, it first checks if the operator method is
    defined on the `DataSource` instance, as this implies an
    inheritance error, and raises an `UninheritedOperationError`
    if so.

    Finally, otherwise, returns `False`
    """
    if isinstance(data_source, operator_class):
        return True
    if hasattr(data_source, operator_method):
        raise UninheritedOperationError(
            data_source,
            operator_class,
            operator_method
        )
    return False


def validate(
    operator_class: Type[Operator],
    operator_method: str,
    api_full_name: str
) -> Callable:
    """
    Validates:
    - a Controller method's corresponding operation is supported by its DataSource:
        - an UninheritedOperationError is raised if the method is implemented
          but the mixin ABC is not inherited from.
        - otherwise an UnsupportedOpertionError is raised.
    """
    def decorator(method: Callable) -> Callable:
        def wrapper(controller: Controller, object_type: str, *args, **kwargs) -> Any:
            if not __is_supported(
                operator_class,
                operator_method,
                controller.data_source
            ):
                raise UnsupportedOpertionError(object_type, api_full_name)
            return method(controller, object_type, *args, **kwargs)
        return wrapper
    return decorator


class Controller:
    """
    An MVC-esque Controller class, that fulfills requests.
    """

    def __init__(self, data_source: OperableDataSource, view: View) -> None:
        self.__data_source = data_source
        self.__view = view

    @property
    def data_source(self) -> OperableDataSource:
        return self.__data_source

    @validate(DetailGetter, 'get_by_id', 'detail GET')
    def get_detail(self, object_type: str, object_id: str) -> ResponseDict:
        """
        Gets an individual object of specified type and id
        """
        data_object = self.__get_detail_object(object_type, object_id)
        return self.__view.dump(data_object)

    @validate(PageGetter, 'get_list_page', 'list GET')
    def get_list(
        self,
        object_type: str,
        query_args: ListGetParamaters
    ) -> ResponseDict:
        """
        Gets a page of list results of specified type.
        """
        page_number = self.__get_page_number_or_1(query_args)
        data_objects, total = self.__data_source.get_list_page(
            object_type,
            page_number,
            page_size=query_args.page_size,
            object_filters=query_args.filter,
            sort_by=query_args.sort_by
        )
        document_meta = {
            'total': total,
            'types': self.__data_source.get_attribute_types(object_type)
        }
        return self.__view.dump_bulk(data_objects, document_meta=document_meta)

    @validate(Aggregator, 'get_aggregations', 'aggregations POST')
    def post_aggregations(
        self,
        object_type: str,
        query_args: AggregationParameters,
        body: AggregationBody
    ) -> ResponseDict:
        """
        Gets an aggregation on the specified object_type.
        """
        aggregation_results = self.__data_source.get_aggregations(
            object_type,
            object_filters=query_args.filter,
            aggregations=body.aggs
        )
        document_meta = {
            'aggregations': aggregation_results,
            'types': self.__data_source.get_attribute_types(object_type)
        }
        return self.__view.dump_bulk([], document_meta=document_meta)

    def __get_detail_object(self, object_type: str, object_id: str) -> DataObject:
        data_objects = list(self.__data_source.get_by_id(object_type, [object_id]))
        if len(data_objects) == 0 or data_objects[0] is None:
            raise ObjectNotFoundByIdException(object_type, object_id)
        return data_objects[0]

    def __get_page_number_or_1(self, query_args: ListGetParamaters) -> int:
        page_number = query_args.page
        if page_number is None:
            return 1
        return page_number
