# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from itertools import chain
from typing import Callable

from flask import Blueprint, request

from .controller import Controller
from .exception import BaseRuntimeException
from .misc import (
    AggregationBody,
    AggregationParameters,
    JsonApiRequestBody,
    ListGetParamaters
)
from .parser import DefaultParser
from .view import DefaultView
from ..core import DataSource
from ..core.data_source_dict import DataSourceDict
from ..core.datasource_error import DataSourceError
from ..core.operator import Relational


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


ConfigFactory = Callable[[str, tuple[DataSource]], Blueprint]
"""A `Callable` that returns a `ConfigBlueprint`"""


def config_blueprint(
    url_prefix: str,
    data_sources: tuple[DataSource]
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

    return config_handler


def data_blueprint(
    *data_sources: DataSource,
    url_prefix: str = '/data',
    config_prefix: str = '/_config',
    config_factory: ConfigFactory = lambda p, d: config_blueprint(p, d)
) -> DataBlueprint:
    """
    Given a tuple of DataSource instances, this provides a flask
    Blueprint instance for routing the basic operations on said
    DataSource instances as endpoints.
    """

    data_handler = DataBlueprint(url_prefix=url_prefix)

    config = config_factory(config_prefix, data_sources)
    data_handler.register_blueprint(config)

    data_source_dict = DataSourceDict(*data_sources)

    def __new_controller(object_type: str) -> Controller:
        data_source = data_source_dict[object_type]
        view = DefaultView()
        return Controller(data_source, view)

    @data_handler.route('/<object_type>/<object_id>', methods=['GET'])
    def get_detail(*, object_type: str, object_id: str):
        controller = __new_controller(object_type)
        return controller.get_detail(object_type, object_id)

    @data_handler.route('/<object_type>', methods=['GET'])
    def get_list(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = ListGetParamaters(request.args)
        return controller.get_list(object_type, request_args)

    @data_handler.route('/<object_type>/<object_id>', methods=['DELETE'])
    def delete_detail(*, object_type: str, object_id: str):
        controller = __new_controller(object_type)
        return controller.delete_detail(object_type, object_id)

    @data_handler.route('/<object_type>', methods=['PATCH'])
    def patch_list(*, object_type: str):
        controller = __new_controller(object_type)
        request_body = JsonApiRequestBody(request.json)
        return controller.patch_list(object_type, request_body.data)

    @data_handler.route('/<object_type>:upsert', methods=['POST'])
    def post_upserts(*, object_type: str):
        controller = __new_controller(object_type)
        data_source = data_source_dict[object_type]
        request_body = JsonApiRequestBody(request.json)
        parser = DefaultParser(data_source.data_object_factory)
        objects = parser.parse_iterable(request_body.data)
        return controller.post_upserts(object_type, objects)

    @data_handler.route('/<object_type>:aggregations', methods=['POST'])
    def get_aggregations(*, object_type: str):
        controller = __new_controller(object_type)
        request_args = AggregationParameters(request.args)
        body = AggregationBody(request.json)
        return controller.post_aggregations(object_type, request_args, body)

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

    return data_handler
