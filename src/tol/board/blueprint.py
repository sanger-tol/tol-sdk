# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Iterable

from flask import Blueprint, request

from tol.api_base2.misc import (
    CtxGetter,
    ListGetParamaters,
    default_ctx_getter
)
from tol.api_client2.view import (
    DefaultView,
    View
)
from tol.core import (
    DataObject,
    DataSourceFilter,
    OperableDataSource
)


ViewFactory = Callable[[], View]


class DashboardBlueprint(Blueprint):
    def __init__(
        self,
        name: str,
        import_name: str,
        ds: OperableDataSource,
        admin_role: str,
        ctx_getter: CtxGetter,
        view_factory: ViewFactory
    ) -> None:

        super().__init__(name, import_name)

        self.__ds = ds
        self.__admin_role = admin_role
        self.__ctx_getter = ctx_getter
        self.__view_factory = view_factory

    def route_container(
        self,
        container_type: str,
        element_type: str
    ) -> None:
        """
        Routes an endpoint that abstracts away the joining table
        between a container and its elements (e.g. components
        within a zone).
        """

        @self.get(
            f'/{container_type}/<id_>/{element_type}s',
            endpoint=f'{element_type}_in_{container_type}'
        )
        def route_method(id_: str):
            view = self.__view_factory()
            args = ListGetParamaters(request.args)
            element_objs = self.__get_contained(
                container_type,
                element_type,
                id_,
                args.page,
                args.page_size,
            )

            return view.dump_bulk(element_objs)

    def __get_contained(
        self,
        container_type: str,
        element_type: str,
        container_id: str,
        page: int,
        page_size: int,
    ) -> Iterable[DataObject]:

        joinining_type = f'{element_type}_{container_type}'
        f = self.__get_filter(container_type, container_id)

        joining_objs = self.__ds.get_list_page(
            joinining_type,
            page,
            page_size=page_size,
            object_filters=f,
            sort_by='order'
        )

        return self.__get_element_objs(
            element_type,
            joining_objs
        )

    def __get_element_objs(
        self,
        element_type: str,
        joining_objs: Iterable[DataObject]
    ) -> Iterable[DataObject]:

        element_ids = (
            obj.id for obj in joining_objs
        )

        return self.__ds.get_by_ids(
            element_type,
            element_ids
        )

    def __get_filter(
        self,
        container_type: str,
        container_id: str
    ) -> DataSourceFilter:

        return DataSourceFilter(
            and_={
                f'{container_type}.id': {
                    'eq': {
                        'value': container_id
                    }
                }
            }
        )


def dashboard_blueprint(
    ds: OperableDataSource,

    admin_role: str = 'admin',
    ctx_getter: CtxGetter = default_ctx_getter,
    view_factory: ViewFactory = lambda: DefaultView()
) -> DashboardBlueprint:
    """
    A flask `Blueprint` for user-configured dashboards
    """

    board_bp = DashboardBlueprint(
        'dashboard',
        __name__,
        ds,
        admin_role,
        ctx_getter,
        view_factory
    )

    board_bp.route_container('zone', 'component')
    board_bp.route_container('view', 'zone')
    board_bp.route_container('board', 'view')

    return board_bp
