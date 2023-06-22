# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional

from flask import Blueprint, request

from .controller import Controller
from .exception import BaseRuntimeException
from .misc import (
    AggregationBody,
    AggregationParameters,
    ListGetParamaters
)
from .view import DefaultView
from ..core import DataSource
from ..core.data_source_dict import DataSourceDict
from ..core.datasource_error import DataSourceError


class DataBlueprint(Blueprint):
    """
    A flask Blueprint for dynamically routing DataObject endpoints
    defined in DataSource instances.
    """

    def __init__(
        self,
        url_prefix: Optional[str] = None
    ) -> None:
        super().__init__(
            'data_source_handler',
            __name__,
            url_prefix=url_prefix
        )


def data_blueprint(
    *data_sources: DataSource,
    url_prefix: str = '/data'
) -> DataBlueprint:
    """
    Given a tuple of DataSource instances, this provides a flask
    Blueprint instance for routing the basic operations on said
    DataSource instances as endpoints.
    """

    data_handler = DataBlueprint(url_prefix=url_prefix)
    data_source_dict = DataSourceDict(*data_sources)

    @data_handler.route('/<object_type>/<object_id>', methods=['GET'])
    def get_detail(*, object_type: str, object_id: str):
        data_source = data_source_dict[object_type]
        view = DefaultView()
        controller = Controller(data_source, view)
        return controller.get_detail(object_type, object_id)

    @data_handler.route('/<object_type>', methods=['GET'])
    def get_list(*, object_type: str):
        data_source = data_source_dict[object_type]
        view = DefaultView()
        controller = Controller(data_source, view)
        request_args = ListGetParamaters(request.args)
        return controller.get_list(object_type, request_args)

    @data_handler.route('/<object_type>:aggregations', methods=['POST'])
    def get_aggregations(*, object_type: str):
        data_source = data_source_dict[object_type]
        view = DefaultView()
        controller = Controller(data_source, view)
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
