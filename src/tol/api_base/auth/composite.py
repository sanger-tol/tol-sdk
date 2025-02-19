# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections import defaultdict
from functools import reduce, wraps
from itertools import chain
from typing import (
    Callable,
    Iterable,
    Optional,
    Protocol,
    Union,
)


from .asserts import AuthInspector
from .error import ForbiddenError
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


_HookDecorator = Union[
    InspectorHook,
    Callable[[InspectorHook], InspectorHook]
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
        self.__typed_noauths = self.__new_type_handler_dict()
        self.__typed_auths = self.__new_type_handler_dict()

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
                return self.__invoke_auth(
                    object_type,
                    method,
                    ctx
                )
        else:
            return self.__invoke_noauth(
                object_type,
                method
            )

    def noauth(
        self,
        hook: Optional[InspectorHook] = None,
        *,
        object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Registers a hook `Callable` for a
        request for which no user has
        authenticated.

        Specify an indvidual `str` or `list[str]`
        (`object_type`) to limit its invocation,
        otherwise it will be invoked for all
        types.
        """

        return self.__hook_decorator(
            hook,
            lambda h: self.__noauth_append(
                h,
                object_type
            )
        )

    def auth(
        self,
        hook: Optional[InspectorHook] = None,
        *,
        object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Registers a hook `Callable` for an
        authenticated user.

        Specify an indvidual `str` or `list[str]`
        (`object_type`) to limit its invocation,
        otherwise it will be invoked for all
        types.
        """

        return self.__hook_decorator(
            hook,
            lambda h: self.__auth_append(
                h,
                object_type
            )
        )

    def always(
        self,
        hook: Optional[InspectorHook] = None,
        *,
        object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Registers a hook `Callable` that is always
        invoked, indepenently of the authentication
        status of the request.

        Specify an indvidual `str` or `list[str]`
        (`object_type`) to limit its invocation,
        otherwise it will be invoked for all
        types.
        """

        return self.__hook_decorator(
            hook,
            lambda h: self.__always_append(
                h,
                object_type
            )
        )

    def forbid(
        self,
        object_type: str | list[str]
    ) -> None:
        """
        Always forbids any and all operations, to every
        non-admin request, on the given `object_type`(s).
        """

        @self.always(object_type=object_type)
        def __hook(*args, **kwargs) -> None:
            raise ForbiddenError

    def forbid_noauth(
        self,
        object_type: str | list[str]
    ) -> None:
        """
        Forbids any and all operations, to every
        unauthenticated request, on the given
        `object_type`(s).
        """

        @self.noauth(object_type=object_type)
        def __hook(*args, **kwargs) -> None:
            raise ForbiddenError

    def __noauth_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:

        if object_type is None:
            self.__noauths.append(hook)
        else:
            self.__append_to_dict(
                hook,
                object_type,
                self.__typed_noauths
            )

    def __auth_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:

        if object_type is None:
            self.__auths.append(hook)
        else:
            self.__append_to_dict(
                hook,
                object_type,
                self.__typed_auths
            )

    def __always_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:

        self.__noauth_append(hook, object_type)
        self.__auth_append(hook, object_type)

    def __hook_decorator(
        self,
        hook: InspectorHook | None,
        append_func: Callable[[InspectorHook], None]
    ) -> InspectorHook:

        def decorator(
            arg_hook: InspectorHook
        ) -> _HookDecorator:

            append_func(arg_hook)

            @wraps(arg_hook)
            def wrapper(
                __type: str,
                __op: OperatorMethod,
                auth_ctx: AuthContext | None = None
            ):

                return arg_hook(
                    __type,
                    __op,
                    auth_ctx=auth_ctx
                )

            return wrapper

        if callable(hook):
            return decorator(hook)
        else:
            return decorator

    def __append_to_dict(
        self,
        hook: InspectorHook,
        object_type: str | list[str],
        target: dict[str, list[InspectorHook]]
    ) -> None:

        def __append_single(__type: str) -> None:
            existing = target.get(__type, [])
            existing.append(hook)
            target[__type] = existing

        if isinstance(object_type, str):
            __append_single(object_type)
        else:
            for __type in object_type:
                __append_single(__type)

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

    def __invoke_noauth(
        self,
        object_type: str,
        op: OperatorMethod
    ) -> Optional[AndFilter]:

        hooks = self.__get_noauth_hooks(
            object_type
        )

        return reduce(
            lambda d, h: self.__accumulate(
                d,
                h(object_type, op)
            ),
            hooks,
            None
        )

    def __invoke_auth(
        self,
        object_type: str,
        op: OperatorMethod,
        auth_context: AuthContext
    ) -> Optional[AndFilter]:

        hooks = self.__get_auth_hooks(
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
            hooks,
            None
        )

    def __new_type_handler_dict(
        self
    ) -> _TypeHandlerDict:

        return defaultdict(
            lambda: []
        )

    def __get_auth_hooks(
        self,
        object_type: str
    ) -> Iterable[InspectorHook]:

        return chain(
            self.__auths,
            self.__typed_auths[object_type]
        )

    def __get_noauth_hooks(
        self,
        object_type: str
    ) -> Iterable[InspectorHook]:

        return chain(
            self.__noauths,
            self.__typed_noauths[object_type]
        )
