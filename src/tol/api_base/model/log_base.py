# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr

from .base import Base, db
from .user import get_request_user_id


class LogMixin(object):
    @declared_attr
    def created_at(cls):
        return db.Column(db.DateTime, nullable=False, default=db.func.now())

    @declared_attr
    def created_by(cls):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def last_modified_at(cls):
        return db.Column(db.DateTime, nullable=False, default=db.func.now())

    @declared_attr
    def last_modified_by(cls):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def history(cls):
        return db.Column(db.JSON, nullable=False, default=[])


class LogBase(Base, LogMixin):
    """Logs all three of:
    - creation details
    - last modification details
    - all previous modifcation detail snapshots (in history)"""

    __abstract__ = True

    @classmethod
    def has_log_details(cls):
        return True

    def save_update(self, user_id=None):
        if self._should_update:
            if not user_id:
                user_id = get_request_user_id()
            self.last_modified_by = user_id
            self.last_modified_at = datetime.now()
        super().save_update()

    def save_create(self, user_id=None):
        self._update_metadata(user_id)
        super().save_create()

    def add(self, user_id=None):
        self._update_metadata(user_id)
        super().add()
        db.session.flush()

    def _update_metadata(self, user_id):
        if not user_id:
            user_id = get_request_user_id()
        self.created_by = user_id
        self.last_modified_by = user_id

    def _get_updated_history(self, schema):
        old_history = [*self.history]
        return old_history + [
            schema.create_history_entry(self)
        ]

    def update(self, *args, schema=None, **kwargs):
        updated_history = self._get_updated_history(schema)
        super().update(*args, **kwargs)
        if self._should_update:
            self.history = updated_history
