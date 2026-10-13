# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric import rsa

import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, sessionmaker

from tol.api_base.auth.config import OidcConfig
from tol.api_base.auth.error import ForbiddenError
from tol.api_base.misc.auth_context import AuthContext
from tol.sql import model_base
from tol.sql.auth.blueprint import DbAuthManager
from tol.sql.auth.models import create_models


class UserMixin:
    @declared_attr
    def name(cls) -> Mapped[str | None]:
        return mapped_column(nullable=True)

    @declared_attr
    def email(cls) -> Mapped[str]:
        return mapped_column()


class TestDbAuthManagerKeycloak:
    def set_up_test(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
        token_audience: str = 'AUDIENCE NOT RELEVANT FOR THIS TEST',
        token_issuer: str = 'ISSUER NOT RELEVANT FOR THIS TEST',
        token_subject: str = 'SUBJECT NOT RELEVANT FOR THIS TEST',
        db_user_data: dict | None = None,
        db_keycloak_info_data: list[dict] | None = None,
    ) -> tuple[str, DbAuthManager, object, object]:
        for environment in ('dev', 'staging', 'production'):
            monkeypatch.setenv(
                f'KEYCLOAK_{environment.upper()}_REALM_URL',
                f'https://keycloak.com/{environment}'
            )
            monkeypatch.setenv(
                f'KEYCLOAK_STAGING_{environment.upper()}_REALM_URL',
                f'https://keycloak.com/{environment}'
            )

        private_key, public_key = jwt_keys
        token = jwt.encode(
            {
                'aud': token_audience,
                'iss': token_issuer,
                'sub': token_subject,
                'exp': int((datetime.now() + timedelta(hours=1)).timestamp()),
                'name': 'testname',
                'email': 'company@example.com',
            },
            private_key,
            algorithm='RS256',
        )
        mock_client = SimpleNamespace(
            get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=public_key)
        )
        monkeypatch.setattr(jwt, 'PyJWKClient', lambda *_args, **_kwargs: mock_client)

        base = model_base()
        models = create_models(
            base,
            'user',
            'oidc_id',
            UserMixin,
            object,
            False,
            object,
            timedelta(days=7),
            False,
            True,
        )
        engine = create_engine('sqlite://')
        base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)
        manager = DbAuthManager(
            OidcConfig('', '', '', '', '', '', ''),
            session_factory,
            models,
            timedelta(hours=1),
            'email',
            {},
            None,
            True,
        )

        with session_factory() as session:
            users = []
            for user_data in ([db_user_data] if db_user_data else []):
                user = models.user_class.get_or_create(
                    session,
                    user_data['oidc_id'],
                    name=user_data['name'],
                    email=user_data['email'],
                )
                users.append(user)

            for info_data in db_keycloak_info_data or []:
                user = users[0]
                session.add(models.keycloak_info_class(
                    id=info_data['id'],
                    environment=info_data['environment'],
                    user_id=user.id,
                ))
            session.commit()

        return token, manager, models, session_factory

    @pytest.fixture
    def jwt_keys(self) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        return private_key, private_key.public_key()

    def test_missing_token_is_forbidden(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        _, manager, _, _ = self.set_up_test(monkeypatch, jwt_keys)

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), '')

    def test_issuer_not_being_an_expected_keycloak_realm_is_forbidden(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, _, _ = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://notkeycloak.com/dev',
        )

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), token)

    def test_audience_of_quasar_but_no_matching_tokens_is_forbidden(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, _, _ = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='deliberately not quasar',
        )

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), token)

    def test_multiple_users_raises_forbidden_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, models, session_factory = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='quasar',
            db_user_data={
                'name': 'Alice',
                'email': 'company@example.com',
                'oidc_id': 'alice@example.com',
            },
        )
        with session_factory() as session:
            models.user_class.get_or_create(
                session,
                'bob@example.com',
                name='Bob',
                email='company@example.com',
            )

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), token)

    def test_valid_incoming_jwt_token_is_accepted(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, _, _ = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='quasar',
            token_subject='user-keycloak-id',
            db_user_data={
                'name': 'testname',
                'email': 'company@example.com',
                'oidc_id': 'company@example.com',
            },
            db_keycloak_info_data=[
                {
                    'id': 'user-keycloak-id',
                    'environment': 'https://keycloak.com/dev',
                }
            ],
        )
        context = AuthContext()

        manager.authenticate(context, token)

        assert context.authenticated
        assert context.user_id == '1'

    def test_token_where_keycloak_id_does_not_match_stored_realm_is_forbidden(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, _, _ = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='quasar',
            token_subject='user-keycloak-id',
            db_user_data={
                'name': 'testname',
                'email': 'company@example.com',
                'oidc_id': 'company@example.com',
            },
            db_keycloak_info_data=[
                {
                    'id': 'user-keycloak-id',
                    'environment': 'https://keycloak.com/production',
                }
            ],
        )

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), token)

    def test_token_where_realm_does_not_match_stored_keycloak_id_is_forbidden(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, _, _ = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='quasar',
            token_subject='user-keycloak-id',
            db_user_data={
                'name': 'testname',
                'email': 'company@example.com',
                'oidc_id': 'company@example.com',
            },
            db_keycloak_info_data=[
                {
                    'id': 'a-different-keycloak-id',
                    'environment': 'https://keycloak.com/dev',
                }
            ],
        )

        with pytest.raises(ForbiddenError):
            manager.authenticate(AuthContext(), token)

    def test_valid_jwt_with_first_request_adds_user_and_keycloak_info(
        self,
        monkeypatch: pytest.MonkeyPatch,
        jwt_keys: tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey],
    ) -> None:
        token, manager, models, session_factory = self.set_up_test(
            monkeypatch,
            jwt_keys,
            token_issuer='https://keycloak.com/dev',
            token_audience='quasar',
            token_subject='user-keycloak-id',
        )
        context = AuthContext()

        manager.authenticate(context, token)

        with session_factory() as session:
            users = session.query(models.user_class).all()
            keycloak_infos = session.query(models.keycloak_info_class).all()
            assert len(users) == 1
            assert users[0].name == 'testname'
            assert users[0].email == 'company@example.com'
            assert users[0].oidc_id == 'company@example.com'
            assert len(keycloak_infos) == 1
            assert keycloak_infos[0].id == 'user-keycloak-id'
            assert keycloak_infos[0].environment == 'https://keycloak.com/dev'

        assert context.authenticated
