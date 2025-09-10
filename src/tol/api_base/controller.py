# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

"""
Controller module for MVC-style request handling.

This module provides the Controller class which serves as an intermediary between
data sources and views, handling various operations such as CRUD operations,
aggregations, and relationship management with proper validation and authorisation.
"""

from __future__ import annotations

import inspect
from inspect import BoundArguments
from typing import Any, Callable, Iterable, Optional, Type

from .auth import AuthInspector
from .misc import (
    AggregationBody,
    AggregationParameters,
    GroupStatsParameters,
    ListGetParamaters,
    StatsParameters,
)
from ..api_client.exception import (
    ObjectNotFoundByIdException,
    RecursiveRelationNotFoundException,
    UninheritedOperationError,
    UnsupportedOperationError,
)
from ..api_client.view import ResponseDict, View
from ..core import DataObject, OperableDataSource
from ..core.datasource_filter import AndFilter, DataSourceFilter
from ..core.operator import (
    Aggregator,
    Counter,
    Cursor,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    Operator,
    OperatorMethod,
    PageGetter,
    Relational,
    ReturnMode,
    Updater,
    Upserter,
)
from ..core.operator.updater import DataObjectUpdate


EmptySuccessResponse = dict[str, bool]


def __is_supported(
    operator_class: Type[Operator],
    operator_method: str,
    data_source: OperableDataSource,
) -> bool:
    """
    Check if a given DataSource instance supports the specified Operator class.

    This function determines whether the data source implements the required operator
    by checking instance relationships and method availability. It handles inheritance
    validation to ensure proper operator implementation.

    Args:
        operator_class: The Operator class type to check for support.
        operator_method: The name of the operator method to validate.
        data_source: The OperableDataSource instance to examine.

    Returns:
        True if the data source supports the operator class, False otherwise.

    Raises:
        UninheritedOperationError: If the operator method exists on the data source
            but the required operator class is not properly inherited.
    """
    if isinstance(data_source, operator_class):
        return True
    if hasattr(data_source, operator_method):
        raise UninheritedOperationError(data_source, operator_class, operator_method)
    return False


def validate(
    operator_class: Type[Operator],
    object_method_name: str,
    operator_method: OperatorMethod,
) -> Callable:
    """
    Decorator factory for validating Controller method operations.

    This decorator ensures that a Controller method's corresponding operation is
    supported by its DataSource. It performs comprehensive validation including
    inheritance checking and authorisation inspection.

    Args:
        operator_class: The Operator class that must be supported by the data source.
        object_method_name: The name of the method on the data source object.
        operator_method: The OperatorMethod enum value for this operation.

    Returns:
        A decorator function that validates the operation before execution.

    Raises:
        UninheritedOperationError: If the method is implemented but the mixin ABC
            is not inherited from.
        UnsupportedOperationError: If the operation is not supported by the data source.
    """

    def decorator(method: Callable) -> Callable:
        sig = inspect.signature(method)

        def wrapper(controller: Controller, object_type: str, *args, **kwargs) -> Any:
            bound_args = sig.bind(controller, object_type, *args, **kwargs)
            bound_args.apply_defaults()

            if not __is_supported(
                operator_class, object_method_name, controller.data_source
            ):
                raise UnsupportedOperationError(object_type, str(operator_method))

            ext_and = controller.inspect_auth(object_type, operator_method, bound_args)
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
    MVC-style Controller class for handling API requests and coordinating data operations.

    The Controller serves as an intermediary between the data source layer and the view
    layer, providing a consistent interface for various operations including CRUD operations,
    aggregations, statistics, and relationship management. It handles validation,
    authorisation, and error management for all supported operations.

    The controller supports a wide range of operations:
    - Detail retrieval and listing with pagination
    - Counting and statistics generation
    - Create, Read, Update, Delete (CRUD) operations
    - Aggregation queries
    - Cursor-based pagination
    - Relationship traversal (to-one and to-many)
    """

    def __init__(
        self,
        data_source: OperableDataSource,
        view: View,
        auth_inspector: Optional[AuthInspector] = None,
    ) -> None:
        """
        Initialise the Controller with required dependencies.

        Args:
            data_source: The OperableDataSource instance for data operations.
            view: The View instance for response formatting.
            auth_inspector: Optional AuthInspector for authorisation validation.
                If None, no authorisation checks will be performed.
        """
        self.__data_source = data_source
        self.__view = view
        self.__inspector = auth_inspector

    @property
    def data_source(self) -> OperableDataSource:
        """
        Get the configured data source instance.

        Returns:
            The OperableDataSource instance used by this controller.
        """
        return self.__data_source

    def inspect_auth(
        self, object_type: str, operation: OperatorMethod, bound_args: BoundArguments
    ) -> Optional[AndFilter]:
        """
        Perform authorisation inspection for the given operation.

        This method delegates to the configured AuthInspector to determine if the
        current context has permission to perform the specified operation on the
        given object type.

        Args:
            object_type: The type of object being operated on.
            operation: The OperatorMethod being performed.
            bound_args: The bound arguments from the calling method.

        Returns:
            An optional AndFilter containing authorisation constraints, or None
            if no inspector is configured or no constraints are required.
        """
        if self.__inspector is not None:
            return self.__inspector(object_type, operation, bound_args)

    @validate(DetailGetter, 'get_by_id', OperatorMethod.DETAIL)
    def get_detail(self, object_type: str, object_id: str, **kwargs) -> ResponseDict:
        """
        Retrieve an individual object of the specified type and identifier.

        This method fetches a single data object by its unique identifier and
        returns it in a format suitable for API responses.

        Args:
            object_type: The type of object to retrieve.
            object_id: The unique identifier of the object.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            A ResponseDict containing the serialised object data.

        Raises:
            ObjectNotFoundByIdException: If no object with the given ID exists.
            UnsupportedOperationError: If the data source doesn't support detail retrieval.
        """
        data_object = self.__get_detail_object(object_type, object_id)
        return self.__view.dump(data_object)

    @validate(PageGetter, 'get_list_page', OperatorMethod.PAGE)
    def get_list(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Retrieve a paginated list of objects of the specified type.

        This method fetches a page of objects based on the provided query parameters,
        including filters, sorting, and field selection. It returns both the data
        and metadata about the total count and available types.

        Args:
            object_type: The type of objects to retrieve.
            query_args: Parameters controlling pagination, filtering, and sorting.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing the paginated objects and metadata including
            total count and attribute type information.

        Raises:
            UnsupportedOperationError: If the data source doesn't support page retrieval.
        """
        page_number = self.__get_page_number_or_1(query_args)
        data_objects, total = self.__data_source.get_list_page(
            object_type,
            page_number,
            page_size=query_args.page_size,
            object_filters=self.__combine_filters(query_args.filter, ext_and),
            sort_by=query_args.sort_by,
            requested_fields=query_args.requested_fields,
        )
        document_meta = {
            'total': total,
            'types': self.__data_source.get_attribute_types(object_type),
        }
        return self.__view.dump_bulk(data_objects, document_meta=document_meta)

    @validate(Counter, 'get_count', OperatorMethod.COUNT)
    def get_count(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Get the count of objects of the specified type matching the given filters.

        This method returns only the total count of objects without retrieving
        the actual data, which is more efficient for counting operations.

        Args:
            object_type: The type of objects to count.
            query_args: Parameters containing filter conditions.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing metadata with the total count.

        Raises:
            UnsupportedOperationError: If the data source doesn't support counting.
        """
        total = self.__data_source.get_count(
            object_type,
            object_filters=self.__combine_filters(query_args.filter, ext_and),
        )
        document_meta = {'total': total}
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(Counter, 'get_stats', OperatorMethod.STATS)
    def get_stats(
        self,
        object_type: str,
        query_args: StatsParameters,
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Generate statistical information for objects of the specified type.

        This method calculates various statistics (such as min, max, average, sum)
        for specified fields on objects matching the given filters.

        Args:
            object_type: The type of objects to analyse.
            query_args: Parameters specifying which statistics to calculate and on which fields.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing metadata with the calculated statistics.

        Raises:
            UnsupportedOperationError: If the data source doesn't support statistics.
        """
        stats = self.__data_source.get_stats(
            object_type,
            stats=query_args.stats,
            stats_fields=query_args.stats_fields,
            object_filters=self.__combine_filters(query_args.filter, ext_and),
        )
        document_meta = {**stats, 'type': object_type}
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(GroupStatter, 'get_group_stats', OperatorMethod.GROUP_STATS)
    def get_group_stats(
        self,
        object_type: str,
        query_args: GroupStatsParameters,
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Generate grouped statistical information for objects of the specified type.

        This method calculates statistics grouped by one or more fields, allowing
        for analysis of data distribution across different categories.

        Args:
            object_type: The type of objects to analyse.
            query_args: Parameters specifying grouping fields, statistics, and target fields.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing metadata with the grouped statistics.

        Raises:
            UnsupportedOperationError: If the data source doesn't support group statistics.
        """
        stats = self.__data_source.get_group_stats(
            object_type,
            query_args.group_by,
            stats=query_args.stats,
            stats_fields=query_args.stats_fields,
            object_filters=self.__combine_filters(query_args.filter, ext_and),
        )
        document_meta = {'stats': list(stats), 'type': object_type}
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(Deleter, 'delete', OperatorMethod.DELETE)
    def delete_detail(
        self, object_type: str, object_id: str, **kwargs
    ) -> EmptySuccessResponse:
        """
        Delete the DataObject of the specified type and identifier.

        This method removes a single object from the data source. The operation
        is permanent and cannot be undone.

        Args:
            object_type: The type of object to delete.
            object_id: The unique identifier of the object to delete.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            An EmptySuccessResponse indicating successful deletion.

        Raises:
            UnsupportedOperationError: If the data source doesn't support deletion.
        """
        self.data_source.delete(object_type, [object_id])
        return {'success': True}

    @validate(Updater, 'update', OperatorMethod.UPDATE)
    def patch_list(
        self, object_type: str, updates: Iterable[DataObjectUpdate], **kwargs
    ) -> EmptySuccessResponse:
        """
        Update multiple objects of the same type using the provided update specifications.

        This method applies updates to existing objects based on their identifiers
        and the update data provided. All objects must be of the same type.

        Args:
            object_type: The type of objects to update.
            updates: An iterable of DataObjectUpdate instances containing
                ID and update data pairs.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            An EmptySuccessResponse indicating a successful update.

        Raises:
            UnsupportedOperationError: If the data source doesn't support updates.
        """
        self.data_source.update(object_type, updates)
        return {'success': True}

    @validate(Inserter, 'insert', OperatorMethod.INSERT)
    def post_inserts(
        self, object_type: str, objects: Iterable[DataObject], **kwargs
    ) -> EmptySuccessResponse:
        """
        Insert new objects of the specified type into the data source.

        This method creates new objects in the data source. The return value
        depends on the data source's return mode configuration.

        Args:
            object_type: The type of objects to insert.
            objects: An iterable of DataObject instances to insert.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            Either an EmptySuccessResponse or a ResponseDict containing the inserted
            objects, depending on the data source's return mode.

        Raises:
            UnsupportedOperationError: If the data source doesn't support insertion.
        """
        returned = self.data_source.insert(object_type, objects)
        if self.data_source.return_mode[object_type] == ReturnMode.POPULATED:
            return self.__view.dump_bulk(returned)
        else:
            return {'success': True}

    @validate(Upserter, 'post_upserts', OperatorMethod.UPSERT)
    def post_upserts(
        self, object_type: str, objects: Iterable[DataObject], **kwargs
    ) -> EmptySuccessResponse:
        """
        Upsert (insert or update) objects of the specified type.

        This method performs an upsert operation, which will insert new objects
        or update existing ones based on their identifiers. The return value
        depends on the data source's return mode configuration.

        Args:
            object_type: The type of objects to upsert.
            objects: An iterable of DataObject instances to upsert.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            Either an EmptySuccessResponse or a ResponseDict containing the upserted
            objects, depending on the data source's return mode.

        Raises:
            UnsupportedOperationError: If the data source doesn't support upsertion.
        """
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
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Perform aggregation operations on objects of the specified type.

        This method executes complex aggregation queries such as grouping,
        bucketing, and statistical calculations on the data set.

        Args:
            object_type: The type of objects to aggregate.
            query_args: Parameters containing filter conditions.
            body: The aggregation specification defining the operations to perform.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing the aggregation results and type information.

        Raises:
            UnsupportedOperationError: If the data source doesn't support aggregation.
        """
        aggregation_results = self.__data_source.get_aggregations(
            object_type,
            object_filters=self.__combine_filters(query_args.filter, ext_and),
            aggregations=body.aggs,
        )
        document_meta = {
            'aggregations': aggregation_results,
            'types': self.__data_source.get_attribute_types(object_type),
        }
        return self.__view.dump_bulk([], document_meta=document_meta)

    @validate(Cursor, 'get_cursor_page', OperatorMethod.CURSOR)
    def get_cursor_page(
        self,
        object_type: str,
        query_args: ListGetParamaters,
        search_after: list[str] | None,
        ext_and: Optional[AndFilter] = None,
    ) -> ResponseDict:
        """
        Retrieve a page of objects using cursor-based pagination.

        This method provides an alternative pagination mechanism using cursors,
        which is more efficient for large datasets and provides consistent
        results even when the underlying data changes.

        Args:
            object_type: The type of objects to retrieve.
            query_args: Parameters containing filter conditions and page size.
            search_after: The cursor position to start from, or None for the first page.
            ext_and: Optional additional filter constraints from authorisation.

        Returns:
            A ResponseDict containing the objects and metadata, including the
            new cursor position for the next page.

        Raises:
            UnsupportedOperationError: If the data source doesn't support cursor pagination.
        """
        data_objects, new_search_after = self.data_source.get_cursor_page(
            object_type,
            query_args.page_size,
            self.__combine_filters(query_args.filter, ext_and),
            search_after,
        )
        meta = {'search_after': new_search_after}

        return self.__view.dump_bulk(data_objects, document_meta=meta)

    @validate(Relational, 'get_recursive_relation', OperatorMethod.TO_ONE)
    def get_recursive_relation(
        self, data_object: DataObject, relationship_hops: list[str], **kwargs
    ) -> ResponseDict:
        """
        Retrieve a nested to-one relationship by following multiple relationship hops.

        This method allows traversal of complex object relationships by following
        a chain of to-one relationships defined by the relationship_hops parameter.

        Args:
            data_object: The source DataObject to start the traversal from.
            relationship_hops: A list of relationship names to traverse in order.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            A ResponseDict containing the final related object.

        Raises:
            RecursiveRelationNotFoundException: If the relationship chain cannot
                be followed or the final object is None.
            UnsupportedOperationError: If the data source doesn't support relationships.
        """
        related_object = self.__get_to_one_relation(data_object, relationship_hops)
        if related_object is None:
            raise RecursiveRelationNotFoundException()
        return self.__view.dump(related_object)

    @validate(Relational, 'get_to_many_relations_page', OperatorMethod.TO_MANY)
    def get_many_relations_page(
        self,
        data_object: DataObject,
        relationship_name: str,
        query_args: ListGetParamaters,
        **kwargs,
    ) -> ResponseDict:
        """
        Retrieve a paginated list of objects from a to-many relationship.

        This method fetches related objects that are connected through a
        to-many relationship, with support for pagination.

        Args:
            data_object: The source DataObject containing the relationship.
            relationship_name: The name of the to-many relationship to traverse.
            query_args: Parameters controlling pagination.
            **kwargs: Additional keyword arguments (including ext_and from validation).

        Returns:
            A ResponseDict containing the paginated related objects.

        Raises:
            UnsupportedOperationError: If the data source doesn't support relationships.
        """
        page = self.data_source.get_to_many_relations_page(
            data_object, relationship_name, query_args.page, query_args.page_size
        )
        return self.__view.dump_bulk(page)

    def __combine_filters(
        self,
        object_filters: Optional[DataSourceFilter] = None,
        ext_and: Optional[AndFilter] = None,
    ) -> Optional[DataSourceFilter]:
        """
        Combine user-provided filters with authorisation filters.

        This private method merges filters from query parameters with additional
        filters imposed by the authorisation system, ensuring that both sets
        of constraints are properly applied.

        Args:
            object_filters: Optional filters from the user query.
            ext_and: Optional additional AND filters from authorisation.

        Returns:
            A combined DataSourceFilter or None if no filters are present.
        """
        if ext_and is None:
            return object_filters
        else:
            if object_filters is None:
                return DataSourceFilter(and_=ext_and)
            elif object_filters.and_ is None:
                object_filters.and_ = ext_and
            else:
                object_filters.and_ |= ext_and

            return object_filters

    def __get_detail_object(self, object_type: str, object_id: str) -> DataObject:
        """
        Retrieve a single DataObject by type and identifier.

        This private method fetches an object and handles the case where
        the object doesn't exist or is None.

        Args:
            object_type: The type of object to retrieve.
            object_id: The unique identifier of the object.

        Returns:
            The requested DataObject.

        Raises:
            ObjectNotFoundByIdException: If no object with the given ID exists.
        """
        data_objects = list(self.__data_source.get_by_id(object_type, [object_id]))
        if len(data_objects) == 0 or data_objects[0] is None:
            raise ObjectNotFoundByIdException(object_type, object_id)
        return data_objects[0]

    def __get_page_number_or_1(self, query_args: ListGetParamaters) -> int:
        """
        Extract the page number from query arguments or return 1 as default.

        This private method provides a safe way to get the page number,
        defaulting to page 1 if no page is specified.

        Args:
            query_args: The query parameters containing the optional page number.

        Returns:
            The page number to use, defaulting to 1.
        """
        page_number = query_args.page
        if page_number is None:
            return 1
        return page_number

    def __get_to_one_relation(
        self, source: DataObject, relationship_hops: list[str]
    ) -> Optional[DataObject]:
        """
        Traverse a to-one relationship chain and return the final related object.

        This private method validates the relationship chain and performs
        the actual traversal through the data source.

        Args:
            source: The source DataObject to start traversal from.
            relationship_hops: The list of relationship names to traverse.

        Returns:
            The final related DataObject, or None if the chain cannot be followed.
        """
        self.__data_source.validate_to_one_recurse(source.type, relationship_hops)
        return self.__data_source.get_recursive_relation(source, relationship_hops)
