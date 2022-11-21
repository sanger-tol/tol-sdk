# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import Base, db, setup_model


@setup_model
class State(Base):
    __tablename__ = "state"

    class Meta:
        type_ = 'states'

    state = db.Column(db.String(), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
