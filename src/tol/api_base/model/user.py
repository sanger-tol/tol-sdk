# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import request, has_request_context

from .base import Base, db, setup_model


@setup_model
class User(Base):
    __tablename__ = "user"

    class Meta:
        type_ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    organisation = db.Column(db.String())
    api_key = db.Column(db.String(), unique=True)
    token = db.Column(db.String(), unique=True)
    role = db.relationship('Role', lazy=False, back_populates="user")


def get_user_id_via_api_key(api_key):
    with db.session.no_autoflush:
        user = db.session.query(User).filter(User.api_key == api_key).one_or_none()
    return user.id if user is not None else None


def get_request_user_id():
    if has_request_context():
        api_key = request.headers.get('Authorization')
        return get_user_id_via_api_key(api_key)
