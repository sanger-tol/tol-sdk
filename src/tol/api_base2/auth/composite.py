# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections import defaultdict
from functools import reduce
from itertools import chain
from typing import (
    Callable,
    Iterator,
    Optional,
    Protocol
)


from .asserts import AuthInspector
from ..misc import (
    AuthContext,
    CtxGetter,
    default_ctx_getter
)
from ...core.datasource_filter import AndFilter
from ...core.operator import OperatorMethod


class InspectorHook(Protocol):
    """
    Decorated by one of the methods of
    `CompositeAuthInspector`
    """

    def __call__(
        self,
        object_type: str,
        op: OperatorMethod,
        auth_ctx: Optional[AuthContext] = None
    ) -> Optional[AndFilter]:
        """
        Args:

        - `str`            - the object_type
        - `OperatorMethod` - the requested operation

        Keyword Args:

        - auth_ctx - is either `None` (if unauthenticated)
                     or `AuthContext` (if authenticated).
                     Suffix signature with `**kwargs` if
                     not needed.

        Returns either:

        - `AndFilter` - if extra filter restrictions
                        are needed
        - `None`      - if not
        """


_TypeHandlerDict = dict[
    str,
    list[InspectorHook]
]


class CompositeAuthInspector(AuthInspector):
    """
    Composes many inspection hooks into
    a single `AuthInspector`.
    """

    def __init__(
        self,
        admin_role: str = 'admin',
        ctx_getter: CtxGetter = default_ctx_getter
    ) -> None:

        self.__admin_role = admin_role
        self.__ctx_getter = ctx_getter

        self.__noauths: list[InspectorHook] = []
        self.__auths: list[InspectorHook] = []
        self.__type_handlers = self.__new_type_handler_dict()

    def __call__(
        self,
        object_type: str,
        method: OperatorMethod
    ) -> Optional[AndFilter]:

        ctx = self.__ctx_getter()

        if ctx.authenticated is True:
            if self.__admin_role in ctx.roles:
                return
            else:
                return self.__auth(
                    object_type,
                    method,
                    ctx
                )
        else:
            return self.__noauth(object_type, method)

    def handle_noauth(
        self,
        handler: InspectorHook
    ) -> InspectorHook:
        """
        Registers a handler `Callable` for an
        unauthenticated user of `data_blueprint`.
        """

        self.__noauths.append(handler)

        return handler

    def handle_type(
        self,
        object_type: str
    ) -> Callable[[InspectorHook], InspectorHook]:
        """
        Registers a handler `Callable` for an
        authenticated user, for a specific
        `object_type`.
        """

        def wrapper(
            handler: InspectorHook
        ) -> InspectorHook:

            self.__register_type_handler(
                object_type,
                handler
            )

            return handler

        return wrapper

    def handle(
        self,
        handler: InspectorHook
    ) -> InspectorHook:
        """
        Registers a handler `Callable` for an
        authenticated user, for all values of
        `object_type`.
        """

        self.__auths.append(handler)

        return handler

    def __accumulate(
        self,
        existing: Optional[AndFilter],
        add: Optional[AndFilter]
    ) -> Optional[AndFilter]:

        if add is None:
            return existing
        else:
            if existing is None:
                return add
            else:
                return existing | add

    def __noauth(
        self,
        object_type: str,
        op: OperatorMethod
    ) -> Optional[AndFilter]:

        return reduce(
            lambda d, h: self.__accumulate(
                d,
                h(object_type, op)
            ),
            self.__noauths,
            None
        )

    def __auth(
        self,
        object_type: str,
        op: OperatorMethod,
        auth_context: AuthContext
    ) -> Optional[AndFilter]:

        handlers = self.__get_auth_handlers(
            object_type
        )

        return reduce(
            lambda d, h: self.__accumulate(
                d,
                h(
                    object_type,
                    op,
                    auth_context=auth_context
                )
            ),
            handlers,
            None
        )

    def __new_type_handler_dict(
        self
    ) -> _TypeHandlerDict:

        return defaultdict(
            lambda: []
        )

    def __register_type_handler(
        self,
        object_type: str,
        handler: InspectorHook
    ) -> None:

        handlers = self.__type_handlers.get(
            object_type,
            []
        )
        handlers.append(handler)
        self.__type_handlers[object_type] = handlers

    def __get_auth_handlers(
        self,
        object_type: str
    ) -> Iterator[InspectorHook]:

        return chain(
            self.__auths,
            self.__type_handlers[object_type]
        )
