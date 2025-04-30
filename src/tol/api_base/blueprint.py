# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

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
    StatsParameters
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
    A flask Blueprint for dynamically routing DataObject endpoints
    defined in DataSource instances.
    """

    def __init__(
        self,
        url_prefix: str
    ) -> None:

        super().__init__(
            'data_source_handler',
            __name__,
            url_prefix=url_prefix
        )


class ConfigBlueprint(Blueprint):
    """
    A flask `Blueprint`, to be nested under `DataBlueprint`, that
    stores configuration information about the stored data as a
    whole.
    """

    def __init__(self, url_prefix: str) -> None:
        super().__init__(
            'data_source_config',
            __name__,
            url_prefix=url_prefix
        )


class CustomBlueprint(Blueprint):
    """
    A flask Blueprint for custom endpoints needing to use
    DataSources.
    """

    def __init__(
        self,
        url_prefix: str,
        name: str = __name__
    ) -> None:

        super().__init__(
            name,
            __name__,
            url_prefix=url_prefix
        )


def _config_blueprint(
    url_prefix: str,
    data_sources: tuple[OperableDataSource],
    operator_config: OperatorConfig
) -> ConfigBlueprint:
    """
    Returns a `ConfigBlueprint` instance given:

    - a `url_prefix`, on which to serve the endpoints
    - `data_sources`, a `tuple` of `DataSource` instances behind the API
    """

    config_handler = ConfigBlueprint(url_prefix)

    @config_handler.route('/relationships', methods=['GET'])
    def get_relationships():
        relationship_configs = chain(
            *[
                d.relationship_config.items()
                for d in data_sources
                if isinstance(d, Relational)
            ]
        )
        return {
            t: d.to_dict() for t, d in relationship_configs
            if not d.empty
        }

    @config_handler.route('/attribute_types', methods=['GET'])
    def get_attribute_types():
        types_list = [d.attribute_types for d in data_sources]
        chain_map = ChainMap(*types_list)
        return dict(chain_map)

    @config_handler.route('/attribute_metadata', methods=['GET'])
    def get_attribute_metadata():
        types_list = [d.attribute_metadata for d in data_sources]
        chain_map = ChainMap(*types_list)
        return dict(chain_map)

    @config_handler.route('/operations', methods=['GET'])
    def get_operations():
        return operator_config.to_dict()

    @config_handler.get('/write_mode')
    def get_relation_write_mode():
        modes_list = [d.write_mode for d in data_sources]
        chain_map = ChainMap(*modes_list)
        return dict(chain_map)

    @config_handler.get('/return_mode')
    def get_return_mode():
        modes_list = [d.return_mode for d in data_sources]
        chain_map = ChainMap(*modes_list)
        return dict(chain_map)

    return config_handler


def _core_blueprint(
    data_source_dict: dict[str, DataSource],
    url_prefix: str,
    auth_inspector: Optional[AuthInspector] = None
) -> DataBlueprint:
    """
    Creates the "core" blueprint, responsible for managing
    (non-metadata) endpoints of the `DataSource` instances
    in the given `dict`.
    """

    data_handler = DataBlueprint(url_prefix=url_prefix)

    def __new_controller(
        object_type: str,
        requested_fields: list[str] | None = None,
    ) -> Controller:

        hop_limit = None if requested_fields else 1

        data_source = data_source_dict[object_type]
        view = DefaultView(
            prefix=url_prefix,
            include_all_to_ones=True,
            hop_limit=hop_limit,
            requested_fields=requested_fields,
        )
        return Controller(
            data_source,
            view,
            auth_inspector=auth_inspector
        )

    @data_handler.route('/<object_type>/<path:object_id>', methods=['GET'])  # Allow slashes
    def get_detail(*, object_type: str, object_id: str):
        controller = __new_controller(object_type)
        object_id_unencoded = urllib.parse.unquote(object_id)
        return controller.get_detail(object_type, object_id_unencoded)

    @data_handler.route('/<object_type>', methods=['GET'])
    def get_list(*, object_type: str):
        request_args = ListGetParamaters(request.args)
        controller = __new_controller(
            object_type,
            requested_fields=request_args.requested_fields,
        )
        return controller.get_list(object_type, request_args)

    @data_handler.route('/<object_type>:export', methods=['POST'])
    def post_list_export(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        body = JsonApiRequestBody(request.json)
        response = controller.post_list_export(object_type, request_args, body)
        return response, 200, {'Content-Type': 'application/vnd.ms-excel'}

    @data_handler.route('/<object_type>:count', methods=['GET'])
    def get_count(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        return controller.get_count(object_type, request_args)

    @data_handler.route('/<object_type>:stats', methods=['GET'])
    def get_stats(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = StatsParameters(request.args)
        return controller.get_stats(object_type, request_args)

    @data_handler.get('/<object_type>:group-stats')
    def get_group_stats(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = GroupStatsParameters(request.args)
        return controller.get_group_stats(object_type, request_args)

    @data_handler.route('/<object_type>/<path:object_id>', methods=['DELETE'])
    def delete_detail(*, object_type: str, object_id: str):
        controller = __new_controller(object_type)
        object_id_unencoded = urllib.parse.unquote(object_id)
        return controller.delete_detail(object_type, object_id_unencoded)

    @data_handler.route('/<object_type>', methods=['PATCH'])
    def patch_list(*, object_type: str):
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        return controller.patch_list(object_type, request_body.data)

    @data_handler.post('/<object_type>:insert')
    def post_inserts(*, object_type: str):
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        parser = DefaultParser(data_source_dict)
        objects = parser.parse_iterable(request_body.data)
        return controller.post_inserts(object_type, objects)

    @data_handler.route('/<object_type>:upsert', methods=['POST'])
    def post_upserts(*, object_type: str):
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        parser = DefaultParser(data_source_dict)
        objects = parser.parse_iterable(request_body.data)
        return controller.post_upserts(object_type, objects)

    @data_handler.route('/<object_type>:aggregations', methods=['POST'])
    def get_aggregations(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = AggregationParameters(request.args)
        body = AggregationBody(request.json)
        return controller.post_aggregations(object_type, request_args, body)

    @data_handler.post('/<object_type>:cursor')
    def get_cursor_page(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        search_after = request.json.get('search_after')
        return controller.get_cursor_page(object_type, request_args, search_after)

    @data_handler.route(
        '/<object_type>:to-one/<object_id>/<path:hops_suffix>',
        methods=['GET']
    )
    def get_to_one_relation(
        *,
        object_type: str,
        object_id: str,
        hops_suffix: str
    ):
        controller = __new_controller(object_type)
        source = data_source_dict[object_type].data_object_factory(
            object_type,
            object_id
        )
        hops = RelataionshipHopsParser(hops_suffix).relationship_hops
        return controller.get_recursive_relation(source, hops)

    @data_handler.route(
        '/<object_type>:to-many/<object_id>/<relationship_name>',
        methods=['GET']
    )
    def get_to_many_relations(
        *,
        object_type: str,
        object_id: str,
        relationship_name: str
    ):
        controller = __new_controller(object_type)
        source = data_source_dict[object_type].data_object_factory(
            object_type,
            object_id
        )
        params = ListGetParamaters(request.args)
        return controller.get_many_relations_page(
            source,
            relationship_name,
            params
        )

    @data_handler.app_errorhandler(BaseRuntimeException)
    def handle_runtime_error(error: BaseRuntimeException):
        return {
            'errors': error.errors
        }, error.status_code

    @data_handler.app_errorhandler(DataSourceError)
    def handle_datasource_error(error: DataSourceError):
        return {
            'errors': [{
                'title': error.title,
                'detail': error.detail
            }]
        }, error.status_code

    @data_handler.app_errorhandler(AuthError)
    def handle_auth_error(error: AuthError):
        return {
            'errors': error.errors
        }, error.status_code

    return data_handler


def data_blueprint(
    *data_sources: DataSource,
    url_prefix: str = '/data',
    config_prefix: str = '/_config',
    auth_inspector: Optional[AuthInspector] = None
) -> DataBlueprint:

    config_bp = _config_blueprint(
        config_prefix,
        data_sources,
        DefaultOperatorConfig(*data_sources)
    )
    core_bp = _core_blueprint(
        DataSourceDict(*data_sources),
        url_prefix,
        auth_inspector=auth_inspector
    )
    core_bp.register_blueprint(config_bp)

    return core_bp


def custom_blueprint(
    url_prefix: str = '/custom',
    name: str = 'custom'
) -> DataBlueprint:
    """
    Provides a flask `Blueprint` instance for adding custom endpoints to.
    """

    custom_handler = CustomBlueprint(name=name, url_prefix=url_prefix)

    return custom_handler
