# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import reduce, wraps
from inspect import BoundArguments
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
from ..misc import AuthContext, CtxGetter, default_ctx_getter
from ...core import DataSource
from ...core.datasource_filter import AndFilter
from ...core.operator import OperatorMethod


class InspectorHook(Protocol):
    """
    Protocol for authorisation hook functions that can be decorated
    by methods of `CompositeAuthInspector`.

    Hook functions are called during authorisation inspection to determine
    whether operations should be permitted, forbidden, or require additional
    filtering.
    """

    def __call__(
        self,
        object_type: str,
        op: OperatorMethod,
        auth_ctx: Optional[AuthContext] = None,
        bound_args: Optional[BoundArguments] = None,
    ) -> Optional[AndFilter]:
        """
        Authorize an operation and optionally return additional filters.

        Args:
            object_type: The type of object being accessed (e.g., 'users', 'orders').
            op: The operation being performed (e.g., OperatorMethod.DETAIL,
                OperatorMethod.INSERT).
            auth_ctx: Authentication context containing user information and roles.
                     None for unauthenticated requests.
            bound_args: Arguments bound to the original request, containing request
                       parameters and data that may be needed for authorisation decisions.

        Returns:
            Optional[AndFilter]: Additional filter to apply to the operation, or None
                               if no additional filtering is needed.

        Raises:
            ForbiddenError: If the operation should be denied.
        """


_TypeHandlerDict = dict[str, list[InspectorHook]]


_HookDecorator = Union[InspectorHook, Callable[[InspectorHook], InspectorHook]]


class CompositeAuthInspector(AuthInspector):
    """
    Implements a composite authorisation inspection system for data access control.

    This class provides a flexible, hook-based authorisation system that allows for
    managing and executing multiple authorisation checks tied to specific object
    types and operations during authorisation processes. It supports different
    behaviors for authenticated and unauthenticated requests through registered
    hooks that can either permit operations, apply additional filters, or explicitly
    forbid certain operations.

    Hook Execution Order:
        1. Global hooks (registered without object_type) are executed first
        2. Type-specific hooks (registered with object_type) are executed second
        3. Hooks within each category are executed in registration order
        4. If multiple hooks return filters, they are combined using OR logic
           (user needs to satisfy at least one filter)

    Error Handling:
        - If any hook raises ForbiddenError, authorisation fails immediately
        - Other exceptions are not caught and will propagate up
        - Admin users bypass all hooks and restrictions

    Attributes:
        admin_role: The name of the role that grants administrative privileges.
                   Users with this role bypass all authorisation restrictions.
        ctx_getter: A callable used to retrieve the current authorisation context.
    """

    def __init__(
        self, admin_role: str = 'admin', ctx_getter: CtxGetter = default_ctx_getter
    ) -> None:
        """
        Initialize the CompositeAuthInspector.

        Args:
            admin_role: The role name that grants administrative privileges,
                       bypassing all authorisation checks. Defaults to 'admin'.
            ctx_getter: Function to retrieve the current authentication context.
                       Should return an AuthContext object. Defaults to the
                       system default context getter.
        """

        self.__admin_role = admin_role
        self.__ctx_getter = ctx_getter

        self.__noauths: list[InspectorHook] = []
        self.__auths: list[InspectorHook] = []
        self.__typed_noauths = self.__new_type_handler_dict()
        self.__typed_auths = self.__new_type_handler_dict()

    def __call__(
        self, object_type: str, method: OperatorMethod, bound_args: BoundArguments
    ) -> Optional[AndFilter]:
        """
        Execute authorisation inspection for a given object type and operation.

        This is the main entry point called by the authorisation system. It
        determines the user's authentication status and invokes the appropriate
        hooks, combining their results into a single filter or raising
        ForbiddenError if access should be denied.

        Args:
            object_type: The type of object being accessed (e.g., 'users', 'orders').
            method: The operation being performed (e.g., OperatorMethod.DETAIL,
                   OperatorMethod.INSERT).
            bound_args: BoundArguments object containing the arguments bound to
                       the original request, used by hooks for authorisation decisions.

        Returns:
            Optional[AndFilter]: Combined filter from all applicable hooks, or None
                               if no additional filtering is needed. Admin users
                               always return None (no restrictions).

        Raises:
            ForbiddenError: If any hook determines access should be denied.

        Note:
            Admin users (those with the admin_role) bypass all authorisation
            checks and always return None.
        """
        ctx = self.__ctx_getter()

        if ctx.authenticated is True:
            if self.__admin_role in ctx.roles:
                return
            else:
                return self.__invoke_auth(object_type, method, ctx, bound_args)
        else:
            return self.__invoke_noauth(object_type, method, bound_args)

    def noauth(
        self, hook: Optional[InspectorHook] = None, *, object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Register a hook for unauthenticated requests.

        This decorator registers a function to be called when processing
        authorisation for requests where no user has authenticated.

        Args:
            hook: The hook function to register. If None, returns a decorator.
            object_type: Specific object type(s) to limit the hook's invocation.
                        Can be a single string, list of strings, or None for all types.

        Returns:
            _HookDecorator: Either the decorated hook function or a decorator function.

        Examples:
            ```python
            # Register for all object types
            @inspector.noauth()
            def global_noauth_check(object_type, op, auth_ctx=None, bound_args=None):
                # Allow read-only operations, forbid writes
                if op in [OperatorMethod.INSERT, OperatorMethod.DELETE]:
                    raise ForbiddenError('Authentication required for write operations')
                return None

            # Register for specific object types
            @inspector.noauth(object_type=['sensitive_data', 'admin_panel'])
            def sensitive_noauth_check(object_type, op, auth_ctx=None, bound_args=None):
                raise ForbiddenError('Authentication required')
            ```
        """

        return self.__hook_decorator(hook, lambda h: self.__noauth_append(h, object_type))

    def auth(
        self, hook: Optional[InspectorHook] = None, *, object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Register a hook for authenticated requests.

        This decorator registers a function to be called when processing
        authorisation for requests from authenticated users (excluding admin users
        who bypass all checks).

        Args:
            hook: The hook function to register. If None, returns a decorator.
            object_type: Specific object type(s) to limit the hook's invocation.
                        Can be a single string, list of strings, or None for all types.

        Returns:
            _HookDecorator: Either the decorated hook function or a decorator function.

        Examples:
            ```python
            # User-specific data filtering
            @inspector.auth(object_type='user_profiles')
            def user_profile_filter(object_type, op, auth_ctx=None, bound_args=None):
                # Users can only access their own profiles
                return AndFilter({'user_id': auth_ctx.user_id})

            # Role-based access control
            @inspector.auth(object_type='financial_reports')
            def financial_access(object_type, op, auth_ctx=None, bound_args=None):
                if 'finance' not in auth_ctx.roles:
                    raise ForbiddenError('Finance role required')
                return None
            ```
        """

        return self.__hook_decorator(hook, lambda h: self.__auth_append(h, object_type))

    def always(
        self, hook: Optional[InspectorHook] = None, *, object_type: str | list[str] | None = None
    ) -> _HookDecorator:
        """
        Register a hook that executes for both authenticated and unauthenticated requests.

        This decorator registers a function to be called regardless of the user's
        authentication status. The hook will be invoked for both authenticated
        and unauthenticated requests (but not for admin users who bypass all checks).

        Args:
            hook: The hook function to register. If None, returns a decorator.
            object_type: Specific object type(s) to limit the hook's invocation.
                        Can be a single string, list of strings, or None for all types.

        Returns:
            _HookDecorator: Either the decorated hook function or a decorator function.

        Examples:
            ```python
            # Apply rate limiting regardless of authentication
            @inspector.always()
            def rate_limit_check(object_type, op, auth_ctx=None, bound_args=None):
                # Implementation would check rate limits
                # Return None if within limits, raise ForbiddenError if exceeded
                return None

            # Time-based access restrictions
            @inspector.always(object_type='maintenance_panel')
            def maintenance_hours(object_type, op, auth_ctx=None, bound_args=None):
                # Only allow access during maintenance hours
                if not is_maintenance_hours():
                    raise ForbiddenError('Access only during maintenance hours')
                return None
            ```
        """

        return self.__hook_decorator(hook, lambda h: self.__always_append(h, object_type))

    def forbid(self, object_type: str | list[str]) -> None:
        """
        Unconditionally forbid all operations on specified object types for non-admin users.

        This convenience method registers a hook that always raises ForbiddenError
        for the specified object types, effectively blocking all access except for
        admin users who bypass all authorisation checks.

        Args:
            object_type: Object type(s) to forbid access to. Can be a single string
                        or list of strings.

        Examples:
            ```python
            # Forbid access to deprecated endpoints
            inspector.forbid(['legacy_api', 'old_reports'])

            # Block access to maintenance functions
            inspector.forbid('system_maintenance')
            ```

        Note:
            This method uses the `always()` decorator internally, so it affects
            both authenticated and unauthenticated users. Admin users are still
            exempt from this restriction.
        """

        @self.always(object_type=object_type)
        def __hook(*args, **kwargs) -> None:
            raise ForbiddenError

    def forbid_noauth(self, object_type: str | list[str]) -> None:
        """
        Forbid operations on specified object types for unauthenticated users only.

        This convenience method registers a hook that raises ForbiddenError for
        unauthenticated requests to the specified object types. This restriction
        does not affect authenticated users (including non-admin users).

        Args:
            object_type: Object type(s) to forbid unauthenticated access to.
                        Can be a single string or list of strings.

        Examples:
            ```python
            # Require authentication for user data
            inspector.forbid_noauth(['user_profiles', 'personal_data'])

            # Block unauthenticated write operations
            inspector.forbid_noauth('protected_content')
            ```

        Note:
            This only affects unauthenticated users. Authenticated users can still
            access these object types (subject to other authorisation hooks).
        """

        @self.noauth(object_type=object_type)
        def __hook(*args, **kwargs) -> None:
            raise ForbiddenError

    def __noauth_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:
        """
        Internal method to append a hook to the unauthenticated hook collections.

        Args:
            hook: The hook function to append.
            object_type: Object type(s) to associate with the hook, or None for global.
        """

        if object_type is None:
            self.__noauths.append(hook)
        else:
            self.__append_to_dict(hook, object_type, self.__typed_noauths)

    def __auth_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:
        """
        Internal method to append a hook to the authenticated hook collections.

        Args:
            hook: The hook function to append.
            object_type: Object type(s) to associate with the hook, or None for global.
        """

        if object_type is None:
            self.__auths.append(hook)
        else:
            self.__append_to_dict(hook, object_type, self.__typed_auths)

    def __always_append(
        self,
        hook: InspectorHook,
        object_type: str | list[str] | None,
    ) -> None:
        """
        Internal method to append a hook to both auth and noauth collections.

        This method implements the `always()` functionality by registering the
        hook for both authenticated and unauthenticated scenarios.

        Args:
            hook: The hook function to append.
            object_type: Object type(s) to associate with the hook, or None for global.
        """

        self.__noauth_append(hook, object_type)
        self.__auth_append(hook, object_type)

    def __hook_decorator(
        self, hook: InspectorHook | None, append_func: Callable[[InspectorHook], None]
    ) -> InspectorHook:
        """
        Internal method that implements the decorator pattern for hook registration.

        This method handles the dual-mode decorator pattern where decorators can
        be used with or without arguments.

        Args:
            hook: The hook function if called directly, None if used as decorator.
            append_func: Function to call to register the hook.

        Returns:
            InspectorHook: The decorated hook function or decorator function.
        """

        def decorator(arg_hook: InspectorHook) -> _HookDecorator:

            append_func(arg_hook)

            @wraps(arg_hook)
            def wrapper(
                __type: str,
                __op: OperatorMethod,
                auth_ctx: AuthContext | None = None,
                bound_args: BoundArguments | None = None,
            ):

                return arg_hook(__type, __op, auth_ctx=auth_ctx, bound_args=bound_args)

            return wrapper

        if callable(hook):
            return decorator(hook)
        else:
            return decorator

    def __append_to_dict(
        self,
        hook: InspectorHook,
        object_type: str | list[str],
        target: dict[str, list[InspectorHook]],
    ) -> None:
        """
        Internal method to append a hook to a type-specific hook dictionary.

        Handles both single object types and lists of object types.

        Args:
            hook: The hook function to append.
            object_type: Object type(s) to register the hook for.
            target: The dictionary to append to (either typed_auths or typed_noauths).
        """

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
        self, existing: Optional[AndFilter], add: Optional[AndFilter]
    ) -> Optional[AndFilter]:
        """
        Internal method to combine filters from multiple hooks.

        Combines filters using OR logic (| operator), meaning if multiple hooks
        return filters, the user only needs to satisfy at least one of them to
        gain access. This allows for flexible authorisation where different
        conditions can grant access.

        Args:
            existing: The accumulated filter so far, or None.
            add: New filter to add, or None.

        Returns:
            Optional[AndFilter]: Combined filter using OR logic, or None if no
                               filters to combine.
        """

        if add is None:
            return existing
        else:
            if existing is None:
                return add
            else:
                return existing | add

    def __invoke_noauth(
        self, object_type: str, op: OperatorMethod, bound_args: BoundArguments
    ) -> Optional[AndFilter]:
        """
        Internal method to invoke all applicable hooks for unauthenticated requests.

        Collects and executes all hooks registered for unauthenticated access,
        both global and type-specific, combining their results. Global hooks are
        executed before type-specific hooks.

        Args:
            object_type: The object type being accessed.
            op: The operation being performed.
            bound_args: Arguments bound to the original request.

        Returns:
            Optional[AndFilter]: Combined filter from all hooks, or None.

        Raises:
            ForbiddenError: If any hook raises this exception.
        """

        hooks = self.__get_noauth_hooks(object_type)

        return reduce(
            lambda d, h: self.__accumulate(d, h(object_type, op, bound_args=bound_args)),
            hooks,
            None,
        )

    def __invoke_auth(
        self,
        object_type: str,
        op: OperatorMethod,
        auth_ctx: AuthContext,
        bound_args: BoundArguments,
    ) -> Optional[AndFilter]:
        """
        Internal method to invoke all applicable hooks for authenticated requests.

        Collects and executes all hooks registered for authenticated access,
        both global and type-specific, combining their results. Global hooks are
        executed before type-specific hooks.

        Args:
            object_type: The object type being accessed.
            op: The operation being performed.
            auth_ctx: The authentication context of the current user.
            bound_args: Arguments bound to the original request.

        Returns:
            Optional[AndFilter]: Combined filter from all hooks, or None.

        Raises:
            ForbiddenError: If any hook raises this exception.
        """

        hooks = self.__get_auth_hooks(object_type)

        return reduce(
            lambda d, h: self.__accumulate(
                d, h(object_type, op, auth_ctx=auth_ctx, bound_args=bound_args)
            ),
            hooks,
            None,
        )

    def __new_type_handler_dict(self) -> _TypeHandlerDict:
        """
        Internal method to create a new type handler dictionary.

        Creates a defaultdict that returns empty lists for missing keys,
        used for storing type-specific hooks.

        Returns:
            _TypeHandlerDict: A defaultdict for storing hooks by object type.
        """

        return defaultdict(lambda: [])

    def __get_auth_hooks(self, object_type: str) -> Iterable[InspectorHook]:
        """
        Internal method to get all hooks applicable for authenticated requests.

        Combines global authenticated hooks with type-specific authenticated hooks.
        Global hooks are returned first, followed by type-specific hooks.

        Args:
            object_type: The object type to get hooks for.

        Returns:
            Iterable[InspectorHook]: All applicable hooks for authenticated requests,
                                   in execution order (global first, then type-specific).
        """

        return chain(self.__auths, self.__typed_auths[object_type])

    def __get_noauth_hooks(self, object_type: str) -> Iterable[InspectorHook]:
        """
        Internal method to get all hooks applicable for unauthenticated requests.

        Combines global unauthenticated hooks with type-specific unauthenticated hooks.
        Global hooks are returned first, followed by type-specific hooks.

        Args:
            object_type: The object type to get hooks for.

        Returns:
            Iterable[InspectorHook]: All applicable hooks for unauthenticated requests,
                                   in execution order (global first, then type-specific).
        """

        return chain(self.__noauths, self.__typed_noauths[object_type])


class BaseAuthInspectorHelper(ABC):
    def __init__(self, inspector: CompositeAuthInspector, data_source: DataSource):
        self.inspector = inspector
        self.data_source = data_source

    def apply_all_rules(self) -> CompositeAuthInspector:
        self._add_allowed_method_rules()
        self._add_create_rules()
        self._add_read_rules()
        self._add_update_rules()
        self._add_delete_rules()

        return self.inspector

    @abstractmethod
    def _add_allowed_method_rules(self):
        """Add authorisation rules that determine which operator methods are allowed.

        This method should define and register authorisation rules that specify
        which OperatorMethod values (e.g., PAGE, DETAIL, COUNT, CREATE, UPDATE, DELETE)
        are permitted for the specific object type handled by this helper.

        The implementation should use the inspector's @auth,
        @noauth and @always decorators to register
        functions that:
        - Accept parameters: object_type (str), op (OperatorMethod),
          auth_ctx (Optional[AuthContext]), bound_args (BoundArguments)
        - Validate the auth_ctx and user roles
        - Check if the requested operation (op) is in the allowed methods list
        - Raise ForbiddenError if the operation is not permitted

        Example implementation pattern:
            ```python
            @self.inspector.auth(object_type=self.object_type)
            def allowed_methods_rule(object_type, op, auth_ctx=None, bound_args=None):
                ALLOWED_METHODS = (OperatorMethod.PAGE, OperatorMethod.DETAIL)
                if auth_ctx is None or not auth_ctx.roles:
                    raise ForbiddenError()
                if op not in ALLOWED_METHODS:
                    raise ForbiddenError()
                return None
            ```

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by concrete subclasses.
        """

    @abstractmethod
    def _add_create_rules(self):
        """Add authorisation rules for create operations.

        This method should define and register authorisation rules that control
        access to CREATE operations for the specific object type handled by this helper.

        The implementation should use the inspector's @auth,
        @noauth and @always decorators to register
        functions that:
        - Accept parameters: object_type (str), op (OperatorMethod),
          auth_ctx (Optional[AuthContext]), bound_args (BoundArguments)
        - Validate the auth_ctx and user roles for create permissions
        - Check if the requested operation is CREATE
        - Validate any additional create-specific requirements
            (e.g., data ownership, resource limits)
        - Use bound_args to access request data for validation
        - Raise ForbiddenError if the operation is not permitted

        Example implementation pattern:
            ```python
            @self.inspector.auth(object_type=self.object_type)
            def create_rule(object_type, op, auth_ctx=None, bound_args=None):
                if op != OperatorMethod.CREATE:
                    return  # Rule doesn't apply to non-create operations
                if auth_ctx is None or 'creator' not in auth_ctx.roles:
                    raise ForbiddenError()
                # Use bound_args to validate request data if needed
                if bound_args and hasattr(bound_args.arguments, 'data'):
                    # Validate creation data based on user permissions
                    pass
                return None
            ```

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by concrete subclasses.
        """

    @abstractmethod
    def _add_read_rules(self):
        """Add authorisation rules for read operations.

        This method should define and register authorisation rules that control
        access to READ operations (PAGE, DETAIL, COUNT) for the specific object type
        handled by this helper.

        The implementation should use the inspector's
        @auth, @noauth and @always decorators to register
        functions that:
        - Accept parameters: object_type (str), op (OperatorMethod),
          auth_ctx (Optional[AuthContext]), bound_args (BoundArguments)
        - Validate the auth_ctx and user roles for read permissions
        - Check if the requested operation is a read operation (PAGE, DETAIL, COUNT)
        - Use bound_args to access query parameters for filtering decisions
        - Return AndFilter for row-level security or None for no additional filtering
        - Raise ForbiddenError if the operation is not permitted

        Example implementation pattern:
            ```python
            @self.inspector.auth(object_type=self.object_type)
            def read_rule(object_type, op, auth_ctx=None, bound_args=None):
                READ_METHODS = (OperatorMethod.PAGE, OperatorMethod.DETAIL, OperatorMethod.COUNT)
                if op not in READ_METHODS:
                    return  # Rule doesn't apply to non-read operations
                if auth_ctx is None or 'reader' not in auth_ctx.roles:
                    raise ForbiddenError()
                # Return filter to limit data based on user permissions
                return AndFilter({'owner_id': auth_ctx.user_id})
            ```

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by concrete subclasses.
        """

    @abstractmethod
    def _add_update_rules(self):
        """Add authorisation rules for update operations.

        This method should define and register authorisation rules that control
        access to UPDATE operations for the specific object type handled by this helper.

        The implementation should use the inspector's
        @auth, @noauth and @always decorators to register
        functions that:
        - Accept parameters: object_type (str), op (OperatorMethod),
          auth_ctx (Optional[AuthContext]), bound_args (BoundArguments)
        - Validate the auth_ctx and user roles for update permissions
        - Check if the requested operation is UPDATE
        - Use bound_args to access update data and target record information
        - Validate any additional update-specific requirements
            (e.g., data ownership, field restrictions)
        - Raise ForbiddenError if the operation is not permitted

        Example implementation pattern:
            ```python
            @self.inspector.auth(object_type=self.object_type)
            def update_rule(object_type, op, auth_ctx=None, bound_args=None):
                if op != OperatorMethod.UPDATE:
                    return  # Rule doesn't apply to non-update operations
                if auth_ctx is None or 'editor' not in auth_ctx.roles:
                    raise ForbiddenError()
                # Use bound_args to validate update permissions on specific records
                if bound_args and hasattr(bound_args.arguments, 'id'):
                    record_id = bound_args.arguments['id']
                    # Check if user can update this specific record
                    pass
                return None
            ```

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by concrete subclasses.
        """

    @abstractmethod
    def _add_delete_rules(self):
        """Add authorisation rules for delete operations.

        This method should define and register authorisation rules that control
        access to DELETE operations for the specific object type handled by this helper.

        The implementation should use the inspector's @auth,
        @noauth and @always decorators to register
        functions that:
        - Accept parameters: object_type (str), op (OperatorMethod),
          auth_ctx (Optional[AuthContext]), bound_args (BoundArguments)
        - Validate the auth_ctx and user roles for delete permissions
        - Check if the requested operation is DELETE
        - Use bound_args to access target record information for ownership validation
        - Validate any additional delete-specific requirements
            (e.g., data ownership, cascade effects)
        - Raise ForbiddenError if the operation is not permitted

        Example implementation pattern:
            ```python
            @self.inspector.auth(object_type=self.object_type)
            def delete_rule(object_type, op, auth_ctx=None, bound_args=None):
                if op != OperatorMethod.DELETE:
                    return  # Rule doesn't apply to non-delete operations
                if auth_ctx is None or 'admin' not in auth_ctx.roles:
                    raise ForbiddenError()
                # Use bound_args to validate delete permissions on specific records
                if bound_args and hasattr(bound_args.arguments, 'id'):
                    record_id = bound_args.arguments['id']
                    # Check if user can delete this specific record
                    pass
                return None
            ```

        Raises:
            NotImplementedError: This is an abstract method that must be implemented
                by concrete subclasses.
        """
