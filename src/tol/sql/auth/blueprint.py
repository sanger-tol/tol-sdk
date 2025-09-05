# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth

from .models import ModelClass, ModelTuple, create_models
from ..session import SessionFactory, create_session_factory
from ...api_base.auth import (
    AuthBlueprint,
    AuthManager,
    OidcConfig,
    StateNotFoundError,
    env_oidc_config,
)
from ...api_base.auth.abc import AuthorisationManager
from ...api_base.misc import AuthContext


class DbAuthManager(AuthManager):
    """
    Implements `AuthManager` using SQLAlchemy and a database to achieve an OIDC workflow.

    This class provides database-backed authentication management with OpenID Connect (OIDC)
    integration. It handles the complete OIDC flow including state management, token exchange,
    user profile creation, authentication, and token revocation.

    The manager supports:
    - OIDC authorization code flow
    - Database storage of users, tokens, and state
    - Automatic cleanup of expired tokens and states
    - User profile creation from OIDC claims
    - Token-based authentication and authorization
    """

    def __init__(
        self,
        oidc_config: OidcConfig,
        session_factory: SessionFactory,
        model_tuple: ModelTuple,
        state_delete_delta: timedelta,
        oidc_id_target: str,
        oidc_ext_mapping: dict[str, str],
        authorisation_manager: AuthorisationManager,
    ) -> None:
        """
        Initialize the database authentication manager.

        Args:
            oidc_config: OIDC configuration containing URLs, client credentials, etc.
            session_factory: Factory function for creating database sessions
            model_tuple: Container with the SQLAlchemy model classes for auth tables
            state_delete_delta: Time delta after which OIDC state entries are cleaned up
            oidc_id_target: Field name in OIDC user info to use as the user identifier
            oidc_ext_mapping: Mapping from OIDC field names to local user attribute names
        """
        self.__config = oidc_config
        self.__session_factory = session_factory
        self.__models = model_tuple
        self.__state_delta = state_delete_delta
        self.__oidc_id_target = oidc_id_target
        self.__ext_map = oidc_ext_mapping
        self.__authorisation_manager = authorisation_manager

    def login(self) -> dict[str, str]:
        """
        Initiate the OIDC login flow by generating a new state and returning the authorization URL.

        This method performs cleanup of old states and expired tokens before creating a new
        login session. It generates a unique state parameter for CSRF protection and returns
        the complete authorization URL the user should be redirected to.

        Returns:
            dict: Dictionary containing the 'loginUrl' key with the complete authorization URL
        """
        self.__cleanup_before_login()
        state_uuid = self.__create_new_state()

        return self.__format_login_url(state_uuid)

    def get_token_from_callback(self, state: str, code: str) -> dict[str, str]:
        """
        Exchange the authorization code for an access token after OIDC callback.

        This method validates the state parameter to prevent CSRF attacks and then
        exchanges the authorization code for an access token by posting to the
        OIDC token endpoint.

        Args:
            state: The state parameter returned from the OIDC provider
            code: The authorization code returned from the OIDC provider

        Returns:
            dict: Token response from the OIDC provider, typically containing
                 access_token, token_type, expires_in, etc.

        Raises:
            StateNotFoundError: If the provided state parameter is not found or expired
        """
        self.__check_state_exists(state)

        return self.__post_to_token_url(code)

    def create_user_profile(self, token: str) -> dict[str, Any]:
        """
        Create or update a user profile using the provided access token.

        This method fetches user information from the OIDC provider using the access token,
        creates or updates the user record in the database, stores the token, and returns
        a complete user profile including OIDC ID and any extended user information.

        Args:
            token: Access token to use for fetching user information

        Returns:
            dict: Complete user profile containing:
                - oidc_id: The user's OIDC identifier
                - Any additional user attributes from the database
                - Any token-related extra information
        """
        oidc_id, oidc_ext = self.__get_oidc_details(token)
        user_id, user_ext = self.__get_or_create_user(oidc_id, oidc_ext)
        token_extra = self.__get_or_create_token(token, user_id)

        return {**token_extra, **user_ext, 'oidc_id': oidc_id}

    def authenticate(
        self,
        ctx: AuthContext,
        token: str,
    ) -> None:
        """
        Authenticate a user using the provided token and populate the auth context.

        This method looks up the user associated with the token and populates the
        authentication context with the user ID and role names if the token is valid.
        If the token is not found or invalid, the context remains unchanged.

        Args:
            ctx: Authentication context to populate with user information
            token: Access token to authenticate with
        """
        user_id, role_names, memberships = self.__get_user_details_for_token(token)
        if user_id is not None:
            ctx.user_id = user_id
            ctx.roles = role_names
            ctx.memberships = memberships

    def revoke_token(self, token: str) -> None:
        """
        Revoke an access token both locally and at the OIDC provider.

        This method deletes the token from the local database and then calls the
        OIDC provider's token revocation endpoint to invalidate the token.

        Args:
            token: Access token to revoke
        """
        self.__delete_token(token)
        self.__post_revoke(token)

    def __map_oidc_extra(self, json_return: dict[str, Any]) -> dict[str, Any]:
        """
        Map OIDC user information fields to local user attribute names.

        Uses the oidc_ext_mapping configuration to transform field names from the
        OIDC provider response to the expected local attribute names.

        Args:
            json_return: User information response from OIDC provider

        Returns:
            dict: Mapped user attributes with local field names
        """
        return {v: json_return.get(k) for k, v in self.__ext_map.items()}

    def __post_revoke(self, token: str) -> None:
        """
        Revoke a token at the OIDC provider's revocation endpoint.

        Makes a POST request to the OIDC provider's token revocation endpoint
        with the token and client credentials.

        Args:
            token: Access token to revoke

        Raises:
            requests.HTTPError: If the revocation request fails
        """
        r = requests.post(
            self.__config.revoke_url,
            data={
                'token': token,
                'client_id': self.__config.client_id,
                'client_secret': self.__config.client_secret,
            },
        )
        r.raise_for_status()

    def __get_oidc_details(self, token: str) -> tuple[str, dict[str, Any]]:
        """
        Fetch user details from the OIDC provider using an access token.

        Makes a request to the OIDC user info endpoint with the Bearer token
        and extracts the user ID and additional mapped attributes.

        Args:
            token: Access token to use for the user info request

        Returns:
            tuple: A tuple containing:
                - str: User's OIDC identifier
                - dict: Mapped additional user attributes

        Raises:
            requests.HTTPError: If the user info request fails
        """
        headers = {'Authorization': f'Bearer {token}'}

        r = requests.get(self.__config.user_info_url, headers=headers)
        r.raise_for_status()

        json_return = r.json()

        return (json_return[self.__oidc_id_target], self.__map_oidc_extra(json_return))

    def __get_user_details_for_token(
        self, token: str
    ) -> tuple[Optional[str], list[str], list[str]]:
        """
        Retrieve user details associated with a token from the database.

        Looks up the token in the database and returns the associated user ID
        and role names. Returns None and empty list if token is not found.

        Args:
            token: Access token to look up

        Returns:
            tuple: A tuple containing:
                - Optional[str]: User ID if token exists, None otherwise
                - list[str]: List of role names for the user, empty if no token
                - list[str]: List of membership identifiers for the user, empty if no token
        """
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            instance = token_model.get(sess, token)

            if instance is None:
                return None, [], []
            else:
                user = instance.user

                if self.__authorisation_manager:
                    memberships = self.__authorisation_manager.get_user_memberships(user)
                else:
                    memberships = []

                return str(user.id), user.role_names, memberships

    def __get_or_create_user(
        self, oidc_id: str, oidc_ext: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        """
        Get an existing user or create a new one using OIDC information.

        Looks up a user by their OIDC ID and creates a new user if one doesn't exist.
        Returns the user ID and any extended user information.

        Args:
            oidc_id: The user's OIDC identifier
            oidc_ext: Additional user attributes from OIDC mapping

        Returns:
            tuple: A tuple containing:
                - int: User's database ID
                - dict: Extended user information from the user model
        """
        user_model = self.__models.user_class

        with self.__session_factory() as sess:
            user = user_model.get_or_create(sess, oidc_id, **oidc_ext)
            userinfo_ext = self.__get_user_ext(user)

            return user.id, userinfo_ext

    def __get_user_ext(self, user: Any) -> dict[str, Any]:
        """
        Extract extended user information from a user model instance.

        If the user model defines a `get_userinfo_ext()` method, calls it to
        get additional user information. Otherwise returns an empty dictionary.

        Args:
            user: User model instance

        Returns:
            dict: Extended user information, empty if method not defined
        """
        if self.__user_model_defines_ext(user):
            return user.get_userinfo_ext()
        else:
            return {}

    def __user_model_defines_ext(self, user: Any) -> bool:
        """
        Check if the user model defines a method for extended user information.

        Returns `True` if a `get_userinfo_ext()` method is
        defined on the mixin for `User`.

        Args:
            user: User model instance to check

        Returns:
            bool: True if the user model has a get_userinfo_ext method, False otherwise
        """
        return hasattr(user, 'get_userinfo_ext') and callable(user.get_userinfo_ext)

    def __get_or_create_token(self, token: str, user_id: int) -> str:
        """
        Store a token in the database or update existing token record.

        Creates or updates a token record associated with the given user ID.

        Args:
            token: Access token to store
            user_id: ID of the user associated with the token

        Returns:
            str: Any additional token information returned by the model
        """
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            return token_model.get_or_create(sess, token, user_id)

    def __delete_token(self, token: str) -> str:
        """
        Delete a token from the database.

        Removes the token record from the database.

        Args:
            token: Access token to delete

        Returns:
            str: Result of the delete operation from the model
        """
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            return token_model.delete(sess, token)

    def __check_state_exists(self, state_uuid: str) -> None:
        """
        Verify that an OIDC state parameter exists in the database.

        Checks if the provided state UUID exists in the database to prevent
        CSRF attacks. Raises an exception if the state is not found.

        Args:
            state_uuid: State UUID to verify

        Raises:
            StateNotFoundError: If the state is not found in the database
        """
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            if not state_model.exists(sess, state_uuid):
                raise StateNotFoundError()

    def __post_to_token_url(self, code: str) -> dict[str, str]:
        """
        Exchange authorization code for access token at OIDC token endpoint.

        Makes a POST request to the OIDC provider's token endpoint using HTTP Basic
        authentication with the authorization code to get an access token.

        Args:
            code: Authorization code from OIDC provider

        Returns:
            dict: Token response from OIDC provider

        Raises:
            requests.HTTPError: If the token request fails
        """
        r = requests.post(
            self.__config.token_url,
            auth=self.__basic_auth(),
            data=self.__token_post_data(code),
        )
        r.raise_for_status()

        return r.json()

    def __basic_auth(self) -> HTTPBasicAuth:
        """
        Create HTTP Basic Authentication object for OIDC client credentials.

        Returns:
            HTTPBasicAuth: Authentication object with client ID and secret
        """
        return HTTPBasicAuth(self.__config.client_id, self.__config.client_secret)

    def __token_post_data(self, code: str) -> dict[str, str]:
        """
        Create the POST data for token exchange request.

        Builds the form data required for the OIDC authorization code grant.

        Args:
            code: Authorization code to exchange

        Returns:
            dict: Form data for token request
        """
        return {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.__config.redirect_uri,
        }

    def __delete_old_states(self) -> None:
        """
        Delete expired OIDC state entries from the database.

        Removes state entries that are older than the configured state_delete_delta
        to prevent accumulation of old state records.
        """
        before = datetime.now() - self.__state_delta
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            state_model.delete_old(sess, before)

    def __cleanup_before_login(self) -> None:
        """
        Perform cleanup operations before initiating a new login.

        Deletes old state entries and expired tokens to maintain database hygiene.
        """
        self.__delete_old_states()
        self.__delete_expired_tokens()

    def __delete_expired_tokens(self) -> None:
        """
        Remove expired access tokens from the database.

        Calls the token model's delete_expired method to clean up tokens
        that have passed their expiration time.
        """
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            token_model.delete_expired(sess)

    def __create_new_state(self) -> str:
        """
        Generate and store a new OIDC state parameter.

        Creates a new unique state UUID for CSRF protection during the OIDC flow
        and stores it in the database.

        Returns:
            str: The generated state UUID
        """
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            return state_model.add(sess)

    def __format_login_url(self, state_uuid: str) -> dict[str, str]:
        """
        Format the complete OIDC authorization URL with all required parameters.

        Constructs the authorization URL with the state parameter and other
        OIDC parameters like client_id, response_type, redirect_uri, and scope.

        Args:
            state_uuid: State parameter for CSRF protection

        Returns:
            dict: Dictionary containing 'loginUrl' with the complete authorization URL
        """
        encoded = self.__encode_params(state_uuid)
        login_url = f'{self.__config.auth_url}?{encoded}'

        return {'loginUrl': login_url}

    def __encode_params(self, state_uuid: str) -> str:
        """
        URL encode the OIDC authorization parameters.

        Creates and encodes the query parameters needed for the OIDC authorization request.

        Args:
            state_uuid: State parameter value

        Returns:
            str: URL-encoded query string with all OIDC parameters
        """
        params = {
            'client_id': self.__config.client_id,
            'response_type': 'code',
            'state': state_uuid,
            'redirect_uri': self.__config.redirect_uri,
            'scope': 'openid profile email',
        }

        return urlencode(params)

    def __get_membership(self, user: Any):
        pass


class DbAuthBlueprint(AuthBlueprint):
    """
    Flask Blueprint for database-backed authentication with OIDC.

    Extends the base `AuthBlueprint` to include database model classes
    for authentication. This blueprint provides all the standard auth
    endpoints while maintaining access to the underlying SQLAlchemy
    model classes used for user, token, and state management.

    The blueprint exposes the auth models through a `models` property,
    allowing other parts of the application to interact directly with
    the authentication database tables when needed.
    """

    def __init__(
        self, auth_manager: AuthManager, url_prefix: str, models: ModelTuple
    ) -> None:
        """
        Initialize the database authentication blueprint.

        Args:
            auth_manager: Authentication manager instance for handling auth operations
            url_prefix: URL prefix for all authentication endpoints
            models: Tuple containing the SQLAlchemy model classes for auth tables
        """
        super().__init__(auth_manager, url_prefix)

        self.__models = models

    @property
    def models(self) -> ModelTuple:
        """
        Get the authentication database model classes.

        Returns a `ModelTuple` containing the created `Model` classes for auth.
        These models can be used for direct database operations or for creating
        additional database relationships.

        Returns:
            ModelTuple: Container with the User, Token, State, and Role model classes
        """
        return self.__models


def __db_auth_manager(
    model_base: ModelClass,
    db_uri: str,
    oidc_config: OidcConfig,
    user_mixin_class: ModelClass,
    user_model_name: str,
    token_mixin_class: ModelClass,
    token_is_pk: bool,
    role_mixin_class: ModelClass,
    oidc_id_column_name: str,
    state_delete_delta: timedelta,
    token_expiry_delta: timedelta,
    oidc_id_target: str,
    oidc_ext_mapping: dict[str, str],
    prefix_with_name: bool,
    authorisation_manager: Optional[AuthorisationManager] = None
) -> tuple[DbAuthManager, ModelTuple]:
    """
    Create a database authentication manager with all required components.

    This internal function sets up the complete database authentication system
    including session factory, model creation, and auth manager initialization.

    Args:
        model_base: SQLAlchemy declarative base class for models
        db_uri: Database connection URI
        oidc_config: OIDC configuration object
        user_mixin_class: Mixin class to extend the User model
        user_model_name: Name for the User model class
        token_mixin_class: Mixin class to extend the Token model
        token_is_pk: Whether token should be used as primary key
        role_mixin_class: Mixin class to extend the Role model
        oidc_id_column_name: Column name for OIDC identifier
        state_delete_delta: Time after which states are cleaned up
        token_expiry_delta: Time after which tokens expire
        oidc_id_target: OIDC field to use as user identifier
        oidc_ext_mapping: Mapping of OIDC fields to local attributes
        prefix_with_name: Whether to prefix model names

    Returns:
        tuple: A tuple containing the DbAuthManager instance and ModelTuple
    """
    session_factory = create_session_factory(db_uri)

    model_tuple = create_models(
        model_base,
        user_model_name,
        oidc_id_column_name,
        user_mixin_class,
        token_mixin_class,
        token_is_pk,
        role_mixin_class,
        token_expiry_delta,
        prefix_with_name,
    )

    auth_manager = DbAuthManager(
        oidc_config,
        session_factory,
        model_tuple,
        state_delete_delta,
        oidc_id_target,
        oidc_ext_mapping,
        authorisation_manager,
    )

    return auth_manager, model_tuple


def db_auth_blueprint(
    model_base: ModelClass,
    db_uri: str,
    authorisation_manager: Optional[AuthorisationManager] = None,
    url_prefix: str = '/auth',
    prefix_with_name: bool = False,
    oidc_config_factory: Callable[[], OidcConfig] = env_oidc_config,
    user_mixin_class: ModelClass = object,
    user_model_name: str = 'user',
    token_mixin_class: ModelClass = object,
    token_is_pk: bool = False,
    role_mixin_class: ModelClass = object,
    oidc_id_column_name: str = 'oidc_id',
    state_delete_delta: timedelta = timedelta(hours=1),
    token_expiry_delta: timedelta = timedelta(days=7),
    oidc_id_target: str = 'email',
    oidc_ext_mapping: dict[str, str] = {},
) -> DbAuthBlueprint:
    """
    Create a Flask Blueprint for database-backed authentication with OIDC.

    Creates a complete authentication system using a database for persistence
    and OIDC for user identity verification. The function sets up all necessary
    database models, creates the authentication manager, and returns a Flask
    Blueprint ready to be registered with a Flask application.

    The blueprint provides standard authentication endpoints for login, callback,
    token management, and user profile access. It automatically handles token
    expiration, state cleanup, and user profile synchronization with OIDC.

    Args:
        model_base: SQLAlchemy declarative base class for creating models
        db_uri: Database connection URI (e.g., 'postgresql://user:pass@host/db')
        url_prefix: URL prefix for all authentication endpoints (default: '/auth')
        prefix_with_name: Whether to prefix model table names with the user model name
        oidc_config_factory: Factory function returning OIDC configuration
        user_mixin_class: Optional mixin class to extend the User model with additional
                         columns. All additional columns must be nullable or have defaults.
        user_model_name: Name for the generated User model class (default: 'user')
        token_mixin_class: Optional mixin class to extend the Token model
        token_is_pk: Whether the token value should be used as the primary key
        role_mixin_class: Optional mixin class to extend the Role model
        oidc_id_column_name: Column name for storing OIDC user identifier
        state_delete_delta: Time after which OIDC state entries are cleaned up
                           (default: 1 hour)
        token_expiry_delta: Time after which access tokens expire (default: 7 days)
        oidc_id_target: Field name in OIDC user info response to use as user ID
                       (default: 'email')
        oidc_ext_mapping: Dictionary mapping OIDC response field names to local
                         user attribute names for additional user information

    Returns:
        DbAuthBlueprint: Flask Blueprint instance containing authentication endpoints
                        and providing access to the generated database model classes

    Note:
        The returned blueprint must be registered with a Flask application using
        `app.register_blueprint(blueprint)` before the authentication endpoints
        will be available.

        Database tables will be created automatically when the models are first
        used. Ensure your database exists and is accessible via the provided URI.
    """
    auth_manager, models = __db_auth_manager(
        model_base,
        db_uri,
        oidc_config_factory(),
        user_mixin_class,
        user_model_name,
        token_mixin_class,
        token_is_pk,
        role_mixin_class,
        oidc_id_column_name,
        state_delete_delta,
        token_expiry_delta,
        oidc_id_target,
        oidc_ext_mapping,
        prefix_with_name,
        authorisation_manager=authorisation_manager,
    )

    auth_bp = DbAuthBlueprint(auth_manager, url_prefix, models)

    return auth_bp
