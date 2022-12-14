# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from flask import has_request_context, request

from .base import Base, db, setup_model


@setup_model
class Auth(Base):
    __tablename__ = 'auth'

    class Meta:
        type_ = 'auth'

    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(), nullable=False)
    expires_at = db.Column(db.DateTime(), nullable=False)
    user = db.relationship('User', back_populates='auth',
                           uselist=False, foreign_keys=[user_id])


def get_user_id_via_token(token):
    with db.session.no_autoflush:
        auth_token = Auth.query() \
            .filter(Auth.token == token) \
            .one_or_none()

        if auth_token is not None:
            # check expiry date
            if auth_token.expires_at < datetime.now():
                auth_token.delete()
                return None

        return auth_token.user_id if auth_token is not None else None


def get_request_user_id():
    if has_request_context():
        api_key = request.headers.get('Token')
        return get_user_id_via_token(api_key)
