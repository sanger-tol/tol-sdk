# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import urllib.parse
import uuid
from datetime import datetime, timedelta

from flask import jsonify

import requests
from requests.auth import HTTPBasicAuth

from . import provide_body_data
from ..model import Auth, State, User


class AuthService:
    class Meta:
        model = Auth

    @classmethod
    def login(cls):
        state_uuid = str(uuid.uuid4())
        params = {
            'client_id': os.getenv('ELIXIR_CLIENT_ID'),
            'response_type': 'code',
            'state': state_uuid,
            'redirect_uri': os.getenv('ELIXIR_REDIRECT_URI'),
            'scope': 'openid profile email'
        }
        # save the state in a table so that we can use it
        state = State()
        state.state = state_uuid
        state.add()
        State.commit()

        # clear out states older than one hour so this table doesn't fill up
        since = datetime.now() - timedelta(hours=1)
        State.query() \
            .filter(State.created_at < since) \
            .delete()

        # clear out expired auth tokens
        Auth.query() \
            .filter(Auth.expires_at < datetime.now()) \
            .delete()
        Auth.commit()

        login_url = {
            'loginUrl': 'https://login.elixir-czech.org/oidc/authorize?'
                        + urllib.parse.urlencode(params)
        }

        return login_url, 200

    @classmethod
    @provide_body_data
    def get_token_from_callback(cls, data):
        # check that we know about this state
        state_from_db = State.query() \
            .filter(State.state == data['state']) \
            .one_or_none()
        if state_from_db is None:
            return {
                'detail': 'Unknown state'
            }, 404
        client_auth = HTTPBasicAuth(
            os.getenv('ELIXIR_CLIENT_ID'),
            os.getenv('ELIXIR_CLIENT_SECRET')
        )
        post_data = {
            'grant_type': 'authorization_code',
            'code': data['code'],
            'redirect_uri': os.getenv('ELIXIR_REDIRECT_URI')
        }
        response = requests.post(
            'https://login.elixir-czech.org/oidc/token',
            auth=client_auth,
            data=post_data
        )
        return response.json(), 200

    @classmethod
    @provide_body_data
    def create_user_profile(cls, data):
        # get the user infromation from Elixir for this token
        response = requests.get(
            'https://login.elixir-czech.org/oidc/userinfo',
            headers={'Authorization': 'Bearer ' + data['token']}
        )
        user_info_from_elixir = response.json()
        if user_info_from_elixir.get('error') is None:
            user = User.query() \
                .filter(User.email == user_info_from_elixir['email']) \
                .one_or_none()
            if not user:
                # a new user for the system - create entry
                user = User()
                user.email = user_info_from_elixir['email']
                user.name = user_info_from_elixir['name']
                user.add()
            # save the token so that we can authenticate against it in future
            auth = Auth(user_id=user.id,
                        token=data['token'],
                        created_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(days=7))
            auth.save_create()
            return jsonify(user)
        else:
            return {
                'detail': 'Error getting data from Elixir'
            }, 404
