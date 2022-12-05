# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import Base, db, setup_model


@setup_model
class User(Base):
    __tablename__ = 'user'

    class Meta:
        type_ = 'users'

    id = db.Column(db.Integer(), primary_key=True)  # noqa A003
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    organisation = db.Column(db.String())
    role = db.relationship('Role', lazy=False, back_populates='user')
    auth = db.relationship('Auth', lazy=False, back_populates='user')
