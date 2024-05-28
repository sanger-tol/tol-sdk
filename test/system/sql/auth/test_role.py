# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest


@pytest.fixture(scope='module')
def user_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'user'
    ]
    return matches[0]


@pytest.fixture(scope='module')
def role_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'role'
    ]
    return matches[0]


@pytest.fixture(scope='module')
def role_binding_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'role_binding'
    ]
    return matches[0]


@pytest.fixture(scope='module')
def token_model(full_models_list):
    matches = [
        m for m in full_models_list
        if m.__tablename__ == 'token'
    ]
    return matches[0]


class TestRole:
    """`User().role_names`"""

    def test_no_roles(
        self,
        session_factory,
        user_model
    ):
        """no roles -> `[]`"""

        with session_factory() as sess:
            user = user_model(
                id=970,
                oidc_id='lol'
            )
            sess.add(user)
            sess.commit()

            assert user.role_names == []

    def test_existing_roles(
        self,
        session_factory,
        user_model,
        role_model,
        role_binding_model
    ):
        """
        roles exist -> a `list` of their names in alphabetical order
        """

        with session_factory() as sess:
            user = user_model(
                id=970,
                oidc_id='lol'
            )
            sess.add(user)

            # yet another role
            sess.add(
                role_model(
                    id=3498,
                    name='yar'
                )
            )
            sess.add(
                role_binding_model(
                    user_id=970,
                    role_id=3498
                )
            )

            # admin role
            sess.add(
                role_model(
                    id=34230,
                    name='admin'
                )
            )
            sess.add(
                role_binding_model(
                    user_id=970,
                    role_id=34230
                )
            )
            sess.commit()

            assert user.role_names == ['admin', 'yar']


class TestRequireRole:
    """the Sql-auth methods correctly assign roles."""

    def test_no_auth(self, client):
        """
        no auth -> 401 on `/auth/roles`
        """

        r = client.get('/auth/roles')
        assert r.status_code == 401

    def test_no_roles(
        self,
        session_factory,
        user_model,
        role_model,
        role_binding_model,
        token_model,
        client
    ):
        """
        no roles -> denied, empty `/auth/roles`
        """

        self.__add_models(
            session_factory,
            user_model,
            role_model,
            role_binding_model,
            token_model,
        )

        r = client.get(
            '/hi',
            headers={'Dummy-Token': 'no_roles'}
        )
        assert r.status_code == 403

        r = client.get(
            '/auth/roles',
            headers={'Dummy-Token': 'no_roles'}
        )
        assert r.status_code == 200
        assert r.json == {
            'id': '404',
            'roles': []
        }

    def test_bad_roles(
        self,
        session_factory,
        user_model,
        role_model,
        role_binding_model,
        token_model,
        client
    ):
        """
        roles exist, but are irrelevant -> denied,
        `/auth/roles` -> existing roles
        """

        self.__add_models(
            session_factory,
            user_model,
            role_model,
            role_binding_model,
            token_model,
        )

        r = client.get(
            '/hi',
            headers={'Dummy-Token': 'bad'}
        )
        assert r.status_code == 403

        r = client.get(
            '/auth/roles',
            headers={'Dummy-Token': 'bad'}
        )
        assert r.status_code == 200
        assert r.json == {
            'id': '403',
            'roles': [
                'bad_A',
                'bad_B',
                'bad_C'
            ]
        }

    def test_good_role(
        self,
        session_factory,
        user_model,
        role_model,
        role_binding_model,
        token_model,
        client
    ):
        """good role -> permitted"""

        self.__add_models(
            session_factory,
            user_model,
            role_model,
            role_binding_model,
            token_model,
        )

        r = client.get(
            '/hi',
            headers={'Dummy-Token': 'good'}
        )
        assert r.status_code == 200

        r = client.get(
            '/auth/roles',
            headers={'Dummy-Token': 'good'}
        )
        assert r.status_code == 200
        assert r.json == {
            'id': '200',
            'roles': ['admin']
        }

    def __add_models(
        self,
        session_factory,
        user_model,
        role_model,
        role_binding_model,
        token_model
    ):

        with session_factory() as sess:
            # no roles user
            sess.add(
                user_model(id=404, oidc_id='no_roles')
            )
            sess.add(
                token_model(
                    id=4040,
                    user_id=404,
                    token='no_roles'
                )
            )

            # bad roles user
            sess.add(
                user_model(id=403, oidc_id='bad')
            )
            sess.add(
                token_model(
                    id=4030,
                    user_id=403,
                    token='bad'
                )
            )
            for i, c in enumerate('ABC'):
                sess.add(
                    role_model(
                        id=i + 400,
                        name=f'bad_{c}'
                    )
                )
                sess.add(
                    role_binding_model(
                        id=i + 405,
                        user_id=403,
                        role_id=i + 400
                    )
                )

            # good roles user
            sess.add(
                user_model(id=200, oidc_id='good')
            )
            sess.add(
                token_model(
                    id=2000,
                    user_id=200,
                    token='good'
                )
            )
            sess.add(
                role_model(id=2000, name='admin')
            )
            sess.add(
                role_binding_model(
                    id=2030,
                    user_id=200,
                    role_id=2000
                )
            )

            sess.commit()
