# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Type

from flask import make_response

from .auth import AuthInspector
from .misc import (
    AggregationBody,
    AggregationParameters,
    GroupStatsParameters,
    JsonApiRequestBody,
    ListGetParamaters,
    StatsParameters
)
from ..api_client.exception import (
    ObjectNotFoundByIdException,
    RecursiveRelationNotFoundException,
    UninheritedOperationError,
    UnsupportedOpertionError
)
from ..api_client.view import ResponseDict, View
from ..core import DataObject, OperableDataSource
from ..core.datasource_filter import (
    AndFilter,
    DataSourceFilter
)
from ..core.operator import (
    Aggregator,
    Counter,
    Cursor,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    ListGetter,
    Operator,
    OperatorMethod,
    PageGetter,
    Relational,
    ReturnMode,
    Updater,
    Upserter
)
from ..core.operator.updater import DataObjectUpdate
from ..excel import convert_data_objects_to_excel


EmptySuccessResponse = dict[str, bool]


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
    object_method_name: str,
    operator_method: OperatorMethod
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
                object_method_name,
                controller.data_source
            ):
                raise UnsupportedOpertionError(
                    object_type,
                    str(operator_method)
                )
            ext_and = controller.inspect_auth(object_type, operator_method)
            return method(
                controller,
                object_type,
                *args,
                ext_and=ext_and,
                **kwargs,
            )
        return wrapper
    return decorator


class Controller:
    """
    An MVC-esque Controller class, that fulfills requests.
    """

    def __init__(
        self,
        data_source: OperableDataSource,
        view: View,
        auth_inspector: Optional[AuthInspector] = None
    ) -> None:

        self.__data_source = data_source
        self.__view = view
        self.__inspector = auth_inspector

    @property
    def data_source(self) -> OperableDataSource:
        return self.__data_source

    def inspect_auth(
        self,
        object_type: str,
        operation: OperatorMethod
    ) -> Optional[AndFilter]:

        if self.__inspector is not None:
            return self.__inspector(object_type, operation)

    @validate(DetailGetter, 'get_by_id', OperatorMethod.DETAIL)
    def get_detail(self, object_type: str, object_id: str, **kwargs) -> ResponseDict:
        """
        Gets an individual object of specified type and id
        """
        data_object = self.__get_detail_object(object_type, object_id)
        return self.__view.dump(data_object)

    @validate(PageGetter, 'get_list_page', OperatorMethod.PAGE)
    def get_list(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        ext_and: Optional[AndFilter] = None
    ) -> ResponseDict:
        """
        Gets a page of list results of specified type.
        """
        page_number = self.__get_page_number_or_1(query_args)
        data_objects, total = self.__data_source.get_list_page(
            object_type,
            page_number,
            page_size=query_args.page_size,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
            sort_by=query_args.sort_by,
            requested_fields=query_args.requested_fields
        )
        document_meta = {
            'total': total,
            'types': self.__data_source.get_attribute_types(object_type)
        }
        return self.__view.dump_bulk(data_objects, document_meta=document_meta)

    @validate(ListGetter, 'post_list_export', OperatorMethod.EXPORT)
    def post_list_export(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        body: JsonApiRequestBody,
        ext_and: Optional[AndFilter],
    ) -> ResponseDict:
        """
        Gets all the list results of the specified type.
        """

        page_number = self.__get_page_number_or_1(query_args)
        data_objects, _ = self.__data_source.get_list_page(
            object_type,
            page_number,
            page_size=query_args.page_size,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
            sort_by=query_args.sort_by
        )

        output_stream = convert_data_objects_to_excel(
            self.data_source,
            object_type,
            data_objects,
            body.data,
            'Sheet1'
        )
        response = make_response(output_stream.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=download_table.xlsx'
        response.headers['Content-type'] = 'application/vnd.ms-excel'
        return response

    @validate(Counter, 'get_count', OperatorMethod.COUNT)
    def get_count(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        ext_and: Optional[AndFilter],
    ) -> ResponseDict:
        """
        Gets a count of specified object type, respecting filters.
        """
        total = self.__data_source.get_count(
            object_type,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
        )
        document_meta = {
            'total': total
        }
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(Counter, 'get_stats', OperatorMethod.STATS)
    def get_stats(
        self,
        object_type: str,
        query_args: StatsParameters,
        ext_and: Optional[AndFilter],
    ) -> ResponseDict:
        """
        Gets stats of specified object type, respecting filters.
        """
        stats = self.__data_source.get_stats(
            object_type,
            stats=query_args.stats,
            stats_fields=query_args.stats_fields,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
        )
        document_meta = {**stats, 'type': object_type}
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(GroupStatter, 'get_group_stats', OperatorMethod.GROUP_STATS)
    def get_group_stats(
        self,
        object_type: str,
        query_args: GroupStatsParameters,
        ext_and: Optional[AndFilter],
    ) -> ResponseDict:
        """
        Gets stats of specified object type, respecting filters.
        """
        stats = self.__data_source.get_group_stats(
            object_type,
            query_args.group_by,
            stats=query_args.stats,
            stats_fields=query_args.stats_fields,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
        )
        document_meta = {
            'stats': list(stats),
            'type': object_type
        }
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(Deleter, 'delete', OperatorMethod.DELETE)
    def delete_detail(
        self,
        object_type: str,
        object_id: str,
        **kwargs
    ) -> EmptySuccessResponse:
        """Deletes the `DataObject` of specified type and id"""

        self.data_source.delete(object_type, [object_id])
        return {'success': True}

    @validate(Updater, 'update', OperatorMethod.UPDATE)
    def patch_list(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate],
        **kwargs
    ) -> EmptySuccessResponse:
        """
        Updates the objects (all of same type) using the given
        `Iterable` of ID:update-dict pairs
        """

        self.data_source.update(object_type, updates)
        return {'success': True}

    @validate(Inserter, 'insert', OperatorMethod.INSERT)
    def post_inserts(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        **kwargs
    ) -> EmptySuccessResponse:
        """Inserts the given objects of specified type"""

        returned = self.data_source.insert(object_type, objects)
        if self.data_source.return_mode[object_type] == ReturnMode.POPULATED:
            return self.__view.dump_bulk(returned)
        else:
            return {'success': True}

    @validate(Upserter, 'post_upserts', OperatorMethod.UPSERT)
    def post_upserts(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        **kwargs
    ) -> EmptySuccessResponse:
        """Upserts the given objects of specified type"""

        returned = self.data_source.upsert(object_type, objects)
        if self.data_source.return_mode[object_type] == ReturnMode.POPULATED:
            return self.__view.dump_bulk(returned)
        else:
            return {'success': True}

    @validate(Aggregator, 'get_aggregations', OperatorMethod.AGGREGATE)
    def post_aggregations(
        self,
        object_type: str,
        query_args: AggregationParameters,
        body: AggregationBody,
        ext_and: Optional[AndFilter],
    ) -> ResponseDict:
        """
        Gets an aggregation on the specified object_type.
        """
        aggregation_results = self.__data_source.get_aggregations(
            object_type,
            object_filters=self.__combine_filters(
                query_args.filter,
                ext_and
            ),
            aggregations=body.aggs
        )
        document_meta = {
            'aggregations': aggregation_results,
            'types': self.__data_source.get_attribute_types(object_type)
        }
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(
        Cursor,
        'get_cursor_page',
        OperatorMethod.CURSOR
    )
    def get_cursor_page(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        search_after: list[str] | None,
        ext_and: Optional[AndFilter]
    ) -> ResponseDict:

        data_objects, new_search_after = self.data_source.get_cursor_page(
            object_type,
            query_args.page_size,
            self.__combine_filters(
                query_args.filter,
                ext_and
            ),
            search_after
        )
        meta = {'search_after': new_search_after}

        return self.__view.dump_bulk(
            data_objects,
            document_meta=meta
        )

    @validate(
        Relational,
        'get_recursive_relation',
        OperatorMethod.TO_ONE
    )
    def get_recursive_relation(
        self,
        data_object: DataObject,
        relationship_hops: list[str],
        **kwargs
    ) -> ResponseDict:
        """
        Gets a nested to-one relation by recursive hops
        """

        related_object = self.__get_to_one_relation(
            data_object,
            relationship_hops
        )
        if related_object is None:
            raise RecursiveRelationNotFoundException()
        return self.__view.dump(related_object)

    @validate(
        Relational,
        'get_to_many_relations_page',
        OperatorMethod.TO_MANY
    )
    def get_many_relations_page(
        self,
        data_object: DataObject,
        relationship_name: str,
        query_args: ListGetParamaters,
        **kwargs
    ) -> ResponseDict:
        """Gets a page of to-many relation results"""

        page = self.data_source.get_to_many_relations_page(
            data_object,
            relationship_name,
            query_args.page,
            query_args.page_size
        )
        return self.__view.dump_bulk(page)

    def __combine_filters(
        self,
        object_filters: Optional[DataSourceFilter],
        ext_and: Optional[AndFilter]
    ) -> Optional[DataSourceFilter]:

        if ext_and is None:
            return object_filters
        else:
            if object_filters is None:
                return DataSourceFilter(
                    and_=ext_and
                )
            elif object_filters.and_ is None:
                object_filters.and_ = ext_and
            else:
                object_filters.and_ |= ext_and

            return object_filters

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

    def __get_to_one_relation(
        self,
        source: DataObject,
        relationship_hops: list[str]
    ) -> Optional[DataObject]:

        self.__data_source.validate_to_one_recurse(
            source.type,
            relationship_hops
        )
        return self.__data_source.get_recursive_relation(
            source,
            relationship_hops
        )
