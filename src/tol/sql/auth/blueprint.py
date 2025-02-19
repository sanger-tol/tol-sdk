# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth

from .models import (
    ModelClass,
    ModelTuple,
    create_models
)
from ..session import (
    SessionFactory,
    create_session_factory
)
from ...api_base.auth import (
    AuthBlueprint,
    AuthManager,
    OidcConfig,
    StateNotFoundError,
    env_oidc_config
)
from ...api_base.misc import AuthContext


class DbAuthManager(AuthManager):
    """
    Implements `AuthManager` using SQLALchemy
    and a database, to achieve an OIDC workflow.
    """

    def __init__(
        self,
        oidc_config: OidcConfig,
        session_factory: SessionFactory,
        model_tuple: ModelTuple,
        state_delete_delta: timedelta,
        oidc_id_target: str,
        oidc_ext_mapping: dict[str, str],
    ) -> None:

        self.__config = oidc_config
        self.__session_factory = session_factory
        self.__models = model_tuple
        self.__state_delta = state_delete_delta
        self.__oidc_id_target = oidc_id_target
        self.__ext_map = oidc_ext_mapping

    def login(self) -> dict[str, str]:
        self.__cleanup_before_login()
        state_uuid = self.__create_new_state()

        return self.__format_login_url(state_uuid)

    def get_token_from_callback(
        self,
        state: str,
        code: str
    ) -> dict[str, str]:

        self.__check_state_exists(state)

        return self.__post_to_token_url(code)

    def create_user_profile(
        self,
        token: str
    ) -> dict[str, Any]:

        oidc_id, oidc_ext = self.__get_oidc_details(token)
        user_id, user_ext = self.__get_or_create_user(
            oidc_id,
            oidc_ext
        )
        token_extra = self.__get_or_create_token(
            token,
            user_id
        )

        return {
            **token_extra,
            **user_ext,
            'oidc_id': oidc_id
        }

    def authenticate(
        self,
        ctx: AuthContext,
        token: str,
    ) -> None:

        user_id, role_names = self.__get_user_details_for_token(token)
        if user_id is not None:
            ctx.user_id = user_id
            ctx.roles = role_names

    def revoke_token(self, token: str) -> None:
        self.__delete_token(token)
        self.__post_revoke(token)

    def __map_oidc_extra(
        self,
        json_return: dict[str, Any]
    ) -> dict[str, Any]:

        return {
            v: json_return.get(k)
            for k, v in self.__ext_map.items()
        }

    def __post_revoke(self, token: str) -> None:
        r = requests.post(
            self.__config.revoke_url,
            data={
                'token': token,
                'client_id': self.__config.client_id,
                'client_secret': self.__config.client_secret
            }
        )
        r.raise_for_status()

    def __get_oidc_details(
        self,
        token: str
    ) -> tuple[str, dict[str, Any]]:

        headers = {
            'Authorization': f'Bearer {token}'
        }

        r = requests.get(
            self.__config.user_info_url,
            headers=headers
        )
        r.raise_for_status()

        json_return = r.json()

        return (
            json_return[self.__oidc_id_target],
            self.__map_oidc_extra(json_return)
        )

    def __get_user_details_for_token(
        self,
        token: str
    ) -> tuple[Optional[str], list[str]]:

        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            instance = token_model.get(sess, token)

            if instance is None:
                return None, []
            else:
                user = instance.user
                return str(user.id), user.role_names

    def __get_or_create_user(
        self,
        oidc_id: str,
        oidc_ext: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:

        user_model = self.__models.user_class

        with self.__session_factory() as sess:
            user = user_model.get_or_create(
                sess,
                oidc_id,
                **oidc_ext
            )
            userinfo_ext = self.__get_user_ext(
                user
            )

            return user.id, userinfo_ext

    def __get_user_ext(
        self,
        user: Any
    ) -> dict[str, Any]:

        if self.__user_model_defines_ext(user):
            return user.get_userinfo_ext()
        else:
            return {}

    def __user_model_defines_ext(
        self,
        user: Any
    ) -> bool:
        """
        Returns `True` if an `get_userinfo_ext()` method is
        defined on the mixin for `User`.
        """

        return (
            hasattr(user, 'get_userinfo_ext')
            and callable(
                user.get_userinfo_ext
            )
        )

    def __get_or_create_token(
        self,
        token: str,
        user_id: int
    ) -> str:

        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            return token_model.get_or_create(
                sess,
                token,
                user_id
            )

    def __delete_token(self, token: str) -> str:
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            return token_model.delete(
                sess,
                token
            )

    def __check_state_exists(self, state_uuid: str) -> None:
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            if not state_model.exists(sess, state_uuid):
                raise StateNotFoundError()

    def __post_to_token_url(self, code: str) -> dict[str, str]:
        r = requests.post(
            self.__config.token_url,
            auth=self.__basic_auth(),
            data=self.__token_post_data(code)
        )
        r.raise_for_status()

        return r.json()

    def __basic_auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(
            self.__config.client_id,
            self.__config.client_secret
        )

    def __token_post_data(self, code: str) -> dict[str, str]:
        return {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.__config.redirect_uri
        }

    def __delete_old_states(self) -> None:
        before = datetime.now() - self.__state_delta
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            state_model.delete_old(sess, before)

    def __cleanup_before_login(self) -> None:
        self.__delete_old_states()
        self.__delete_expired_tokens()

    def __delete_expired_tokens(self) -> None:
        token_model = self.__models.token_class

        with self.__session_factory() as sess:
            token_model.delete_expired(sess)

    def __create_new_state(self) -> str:
        state_model = self.__models.state_class

        with self.__session_factory() as sess:
            return state_model.add(sess)

    def __format_login_url(
        self,
        state_uuid: str
    ) -> dict[str, str]:

        encoded = self.__encode_params(state_uuid)
        login_url = f'{self.__config.auth_url}?{encoded}'

        return {'loginUrl': login_url}

    def __encode_params(self, state_uuid: str) -> str:
        params = {
            'client_id': self.__config.client_id,
            'response_type': 'code',
            'state': state_uuid,
            'redirect_uri': self.__config.redirect_uri,
            'scope': 'openid profile email'
        }

        return urlencode(params)


class DbAuthBlueprint(AuthBlueprint):
    """
    Same as `AuthBlueprint`, but stores auth `Model`
    classes too.
    """

    def __init__(
        self,
        auth_manager: AuthManager,
        url_prefix: str,
        models: ModelTuple
    ) -> None:

        super().__init__(auth_manager, url_prefix)

        self.__models = models

    @property
    def models(self) -> ModelTuple:
        """
        Returns a `ModelTuple` containing the
        created `Model` classes for auth.
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
    prefix_with_name: bool
) -> tuple[DbAuthManager, ModelTuple]:

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
        prefix_with_name
    )

    auth_manager = DbAuthManager(
        oidc_config,
        session_factory,
        model_tuple,
        state_delete_delta,
        oidc_id_target,
        oidc_ext_mapping,
    )

    return auth_manager, model_tuple


def db_auth_blueprint(
    model_base: ModelClass,
    db_uri: str,

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
    oidc_ext_mapping: dict[str, str] = {}
) -> DbAuthBlueprint:
    """
    Creates a flask `Blueprint` for auth using a DB,
    given a suitable `ModelClass` and connection `db_uri`.

    Returns a `DbAuthBlueprint` instance, containing a `ModelTuple`
    as a member (which itself contains the newly created `Model`
    classes).

    By default, OIDC tokens expire after 7 days, and inter-request
    OIDC state objects are only valid for 1 hour.

    An SQL-Alchemy `user_mixin_class` can be provided, to
    augment the generated `User` model with extra columns.
    However - these must all either:

    - give `nullable=True`
    - provide a default value.
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
        prefix_with_name
    )

    auth_bp = DbAuthBlueprint(
        auth_manager,
        url_prefix,
        models
    )

    return auth_bp
