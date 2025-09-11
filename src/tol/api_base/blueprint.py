# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

"""
Composite authentication inspector module for managing authorization hooks and permissions.

This module provides a flexible authentication system that allows composition of multiple
authorization strategies and hooks for different object types and methods.
"""

import urllib
from collections import ChainMap
from itertools import chain
from typing import Optional

from flask import Blueprint, request

from .auth import AuthInspector
from .auth.error import AuthError
from .controller import Controller
from .misc import (
    AggregationBody,
    AggregationParameters,
    GroupStatsParameters,
    JsonApiRequestBody,
    ListGetParamaters,
    RelataionshipHopsParser,
    StatsParameters,
)
from ..api_client.exception import BaseRuntimeException
from ..api_client.parser import DefaultParser
from ..api_client.view import DefaultView
from ..core import DataSource, DataSourceError, OperableDataSource
from ..core.data_source_dict import DataSourceDict
from ..core.operator import Relational
from ..core.operator.operator_config import DefaultOperatorConfig, OperatorConfig


class DataBlueprint(Blueprint):
    """
    A Flask Blueprint for dynamically routing DataObject endpoints defined in DataSource instances.

    This blueprint provides the foundation for creating REST API endpoints that interact with
    various data sources, handling common operations like GET, POST, PATCH, and DELETE requests.

    Args:
        url_prefix (str): The URL prefix for all routes registered to this blueprint.
    """

    def __init__(self, url_prefix: str) -> None:
        """
        Initialize the DataBlueprint.

        Args:
            url_prefix (str): URL prefix for all routes in this blueprint.
        """
        super().__init__('data_source_handler', __name__, url_prefix=url_prefix)


class ConfigBlueprint(Blueprint):
    """
    A Flask Blueprint for configuration endpoints, nested under DataBlueprint.

    This blueprint stores and serves configuration information about the stored data as a whole,
    including relationships, attribute types, metadata, and operational configurations.

    Args:
        url_prefix (str): The URL prefix for configuration routes.
    """

    def __init__(self, url_prefix: str) -> None:
        """
        Initialize the ConfigBlueprint.

        Args:
            url_prefix (str): URL prefix for configuration routes.
        """
        super().__init__('data_source_config', __name__, url_prefix=url_prefix)


class CustomBlueprint(Blueprint):
    """
    A Flask Blueprint for custom endpoints that need access to DataSources.

    This blueprint provides a flexible way to add custom endpoints that can leverage
    the existing DataSource infrastructure while implementing specialized business logic.

    Args:
        url_prefix (str): The URL prefix for custom routes.
        name (str, optional): The name for this blueprint. Defaults to __name__.
    """

    def __init__(self, url_prefix: str, name: str = __name__) -> None:
        """
        Initialize the CustomBlueprint.

        Args:
            url_prefix (str): URL prefix for custom routes.
            name (str, optional): Blueprint name. Defaults to __name__.
        """
        super().__init__(name, __name__, url_prefix=url_prefix)


def _config_blueprint(
    url_prefix: str,
    data_sources: tuple[OperableDataSource],
    operator_config: OperatorConfig,
) -> ConfigBlueprint:
    """
    Create and configure a ConfigBlueprint instance with configuration endpoints.

    This function sets up various configuration endpoints that provide metadata about
    the data sources, including relationships, attribute types, operations, and modes.

    Args:
        url_prefix (str): The URL prefix on which to serve the configuration endpoints.
        data_sources (tuple[OperableDataSource]): A tuple of DataSource instances behind the API.
        operator_config (OperatorConfig): Configuration for supported operations.

    Returns:
        ConfigBlueprint: A configured blueprint instance with all configuration routes.

    Routes created:
        - GET /relationships: Returns relationship configurations for relational data sources
        - GET /attribute_types: Returns combined attribute types from all data sources
        - GET /attribute_metadata: Returns combined attribute metadata from all data sources
        - GET /operations: Returns available operations configuration
        - GET /write_mode: Returns write mode configurations for data sources
        - GET /return_mode: Returns return mode configurations for data sources
    """
    config_handler = ConfigBlueprint(url_prefix)

    @config_handler.route('/relationships', methods=['GET'])
    def get_relationships():
        """Get relationship configurations from all relational data sources."""
        relationship_configs = chain(
            *[d.relationship_config.items() for d in data_sources if isinstance(d, Relational)]
        )
        return {t: d.to_dict() for t, d in relationship_configs if not d.empty}

    @config_handler.route('/attribute_types', methods=['GET'])
    def get_attribute_types():
        """Get combined attribute types from all data sources."""
        types_list = [d.attribute_types for d in data_sources]
        chain_map = ChainMap(*types_list)
        return dict(chain_map)

    @config_handler.route('/attribute_metadata', methods=['GET'])
    def get_attribute_metadata():
        """Get combined attribute metadata from all data sources."""
        types_list = [d.attribute_metadata for d in data_sources]
        chain_map = ChainMap(*types_list)
        return dict(chain_map)

    @config_handler.route('/operations', methods=['GET'])
    def get_operations():
        """Get available operations configuration."""
        return operator_config.to_dict()

    @config_handler.get('/write_mode')
    def get_relation_write_mode():
        """Get write mode configurations for all data sources."""
        modes_list = [d.write_mode for d in data_sources]
        chain_map = ChainMap(*modes_list)
        return dict(chain_map)

    @config_handler.get('/return_mode')
    def get_return_mode():
        """Get return mode configurations for all data sources."""
        modes_list = [d.return_mode for d in data_sources]
        chain_map = ChainMap(*modes_list)
        return dict(chain_map)

    return config_handler


def _core_blueprint(
    data_source_dict: dict[str, DataSource],
    url_prefix: str,
    auth_inspector: Optional[AuthInspector] = None,
) -> DataBlueprint:
    """
    Create the core blueprint responsible for managing DataSource endpoints.

    This function creates a comprehensive set of REST API endpoints for interacting
    with DataSource instances, including CRUD operations, relationships, aggregations,
    and specialised operations like cursor-based pagination.

    Args:
        data_source_dict (dict[str, DataSource]): Dictionary mapping object
            types to DataSource instances.
        url_prefix (str): URL prefix for all data endpoints.
        auth_inspector (Optional[AuthInspector], optional): Authentication
            inspector for request authorisation.

    Returns:
        DataBlueprint: A configured blueprint with all data endpoints and error handlers.

    Routes created:
        - GET /<object_type>/<object_id>: Get individual object details
        - GET /<object_type>: Get paginated list of objects
        - GET /<object_type>:count: Get count of objects matching filters
        - GET /<object_type>:stats: Get statistical information about objects
        - GET /<object_type>:group-stats: Get grouped statistical information
        - DELETE /<object_type>/<object_id>: Delete individual object
        - PATCH /<object_type>: Update multiple objects
        - POST /<object_type>:insert: Insert new objects
        - POST /<object_type>:upsert: Insert or update objects
        - POST /<object_type>:aggregations: Get aggregated data
        - POST /<object_type>:cursor: Get cursor-based pagination
        - GET /<object_type>:to-one/<object_id>/<hops_suffix>: Navigate to-one relationships
        - GET /<object_type>:to-many/<object_id>/<relationship_name>: Get to-many relationships
    """
    data_handler = DataBlueprint(url_prefix=url_prefix)

    def __new_controller(
        object_type: str,
        requested_fields: list[str] | None = None,
    ) -> Controller:
        """
        Create a new Controller instance for handling requests to a specific object type.

        Args:
            object_type (str): The type of object this controller will handle.
            requested_fields (list[str] | None, optional): Specific fields to include in responses.

        Returns:
            Controller: Configured controller instance.
        """
        hop_limit = None if requested_fields else 1

        data_source = data_source_dict[object_type]
        view = DefaultView(
            prefix=url_prefix,
            include_all_to_ones=True,
            hop_limit=hop_limit,
            requested_fields=requested_fields,
        )
        return Controller(data_source, view, auth_inspector=auth_inspector)

    @data_handler.route('/<object_type>/<path:object_id>', methods=['GET'])  # Allow slashes
    def get_detail(*, object_type: str, object_id: str):
        """Get details of a specific object by ID."""
        controller = __new_controller(object_type)
        object_id_unencoded = urllib.parse.unquote(object_id)
        return controller.get_detail(object_type, object_id_unencoded)

    @data_handler.route('/<object_type>', methods=['GET'])
    def get_list(*, object_type: str):
        """Get a paginated list of objects of the specified type."""
        request_args = ListGetParamaters(request.args)
        controller = __new_controller(
            object_type,
            requested_fields=request_args.requested_fields,
        )
        return controller.get_list(object_type, request_args)

    @data_handler.route('/<object_type>:count', methods=['GET'])
    def get_count(*, object_type: str):
        """Get the count of objects matching the specified filters."""
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        return controller.get_count(object_type, request_args)

    @data_handler.route('/<object_type>:stats', methods=['GET'])
    def get_stats(*, object_type: str):
        """Get statistical information about objects of the specified type."""
        controller = __new_controller(object_type)
        request_args = StatsParameters(request.args)
        return controller.get_stats(object_type, request_args)

    @data_handler.get('/<object_type>:group-stats')
    def get_group_stats(*, object_type: str):
        """Get grouped statistical information about objects."""
        controller = __new_controller(object_type)
        request_args = GroupStatsParameters(request.args)
        return controller.get_group_stats(object_type, request_args)

    @data_handler.route('/<object_type>/<path:object_id>', methods=['DELETE'])
    def delete_detail(*, object_type: str, object_id: str):
        """Delete a specific object by ID."""
        controller = __new_controller(object_type)
        object_id_unencoded = urllib.parse.unquote(object_id)
        return controller.delete_detail(object_type, object_id_unencoded)

    @data_handler.route('/<object_type>', methods=['PATCH'])
    def patch_list(*, object_type: str):
        """Update multiple objects of the specified type."""
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        return controller.patch_list(object_type, request_body.data)

    @data_handler.post('/<object_type>:insert')
    def post_inserts(*, object_type: str):
        """Insert new objects of the specified type."""
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        parser = DefaultParser(data_source_dict)
        objects = parser.parse_iterable(request_body.data)
        return controller.post_inserts(object_type, objects)

    @data_handler.route('/<object_type>:upsert', methods=['POST'])
    def post_upserts(*, object_type: str):
        """Insert or update objects of the specified type."""
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        parser = DefaultParser(data_source_dict)
        objects = parser.parse_iterable(request_body.data)
        return controller.post_upserts(object_type, objects)

    @data_handler.route('/<object_type>:aggregations', methods=['POST'])
    def get_aggregations(*, object_type: str):
        """Get aggregated data for objects of the specified type."""
        controller = __new_controller(object_type)
        request_args = AggregationParameters(request.args)
        body = AggregationBody(request.json)
        return controller.post_aggregations(object_type, request_args, body)

    @data_handler.post('/<object_type>:cursor')
    def get_cursor_page(*, object_type: str):
        """Get a page of results using cursor-based pagination."""
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        search_after = request.json.get('search_after')
        return controller.get_cursor_page(object_type, request_args, search_after)

    @data_handler.route('/<object_type>:to-one/<object_id>/<path:hops_suffix>', methods=['GET'])
    def get_to_one_relation(*, object_type: str, object_id: str, hops_suffix: str):
        """Navigate through to-one relationships following the specified path."""
        controller = __new_controller(object_type)
        source = data_source_dict[object_type].data_object_factory(object_type, object_id)
        hops = RelataionshipHopsParser(hops_suffix).relationship_hops
        return controller.get_recursive_relation(source, hops)

    @data_handler.route('/<object_type>:to-many/<object_id>/<relationship_name>', methods=['GET'])
    def get_to_many_relations(*, object_type: str, object_id: str, relationship_name: str):
        """Get objects related through a to-many relationship."""
        controller = __new_controller(object_type)
        source = data_source_dict[object_type].data_object_factory(object_type, object_id)
        params = ListGetParamaters(request.args)
        return controller.get_many_relations_page(source, relationship_name, params)

    @data_handler.app_errorhandler(BaseRuntimeException)
    def handle_runtime_error(error: BaseRuntimeException):
        """Handle base runtime exceptions and format error responses."""
        return {'errors': error.errors}, error.status_code

    @data_handler.app_errorhandler(DataSourceError)
    def handle_datasource_error(error: DataSourceError):
        """Handle data source errors and format error responses."""
        return {'errors': [{'title': error.title, 'detail': error.detail}]}, error.status_code

    @data_handler.app_errorhandler(AuthError)
    def handle_auth_error(error: AuthError):
        """Handle authentication/authorization errors and format error responses."""
        return {'errors': error.errors}, error.status_code

    return data_handler


def data_blueprint(
    *data_sources: DataSource,
    url_prefix: str = '/data',
    config_prefix: str = '/_config',
    auth_inspector: Optional[AuthInspector] = None,
) -> DataBlueprint:
    """
    Create a complete data blueprint with both core and configuration endpoints.

    This is the main factory function for creating a full-featured data API blueprint
    that includes both data manipulation endpoints and configuration/metadata endpoints.

    Args:
        *data_sources (DataSource): Variable number of DataSource instances to expose.
        url_prefix (str, optional): URL prefix for data endpoints. Defaults to '/data'.
        config_prefix (str, optional): URL prefix for configuration endpoints.
            Defaults to '/_config'.
        auth_inspector (Optional[AuthInspector], optional): Authentication inspector.
            Defaults to None.

    Returns:
        DataBlueprint: A complete blueprint with both data and configuration endpoints.

    Example:
        ```python
        # Create blueprint with multiple data sources
        blueprint = data_blueprint(
            user_datasource,
            project_datasource,
            url_prefix='/api/v1/data',
            auth_inspector=my_auth_inspector
        )

        # Register with Flask app
        app.register_blueprint(blueprint)
        ```
    """
    config_bp = _config_blueprint(
        config_prefix, data_sources, DefaultOperatorConfig(*data_sources)
    )
    core_bp = _core_blueprint(
        DataSourceDict(*data_sources), url_prefix, auth_inspector=auth_inspector
    )
    core_bp.register_blueprint(config_bp)

    return core_bp


def custom_blueprint(url_prefix: str = '/custom', name: str = 'custom') -> DataBlueprint:
    """
    Create a Flask Blueprint instance for adding custom endpoints.

    This function provides a basic blueprint that can be extended with custom routes
    while still having access to the DataSource infrastructure if needed.

    Args:
        url_prefix (str, optional): URL prefix for custom endpoints. Defaults to '/custom'.
        name (str, optional): Name for the blueprint. Defaults to 'custom'.

    Returns:
        DataBlueprint: A blueprint instance ready for custom endpoint registration.

    Example:
        ```python
        # Create custom blueprint
        custom_bp = custom_blueprint('/api/v1/custom', 'my_custom_endpoints')

        # Add custom routes
        @custom_bp.route('/health', methods=['GET'])
        def health_check():
            return {'status': 'healthy'}

        # Register with Flask app
        app.register_blueprint(custom_bp)
        ```
    """
    custom_handler = CustomBlueprint(name=name, url_prefix=url_prefix)

    return custom_handler
