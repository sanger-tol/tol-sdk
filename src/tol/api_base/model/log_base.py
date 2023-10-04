# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from sqlalchemy.ext.declarative import declared_attr

from .auth import get_request_user_id
from .base import Base, db


class LogMixin(object):
    @declared_attr
    def created_at(self):
        return db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now())

    @declared_attr
    def created_by(self):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def last_modified_at(self):
        return db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now())

    @declared_attr
    def last_modified_by(self):
        return db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    @declared_attr
    def history(self):
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

    def add(self, user_id=None):
        if self.is_new():
            self._add_metadata(user_id=user_id)
        else:
            self._update_metadata(user_id=user_id)
        super().add()

    def save(self, user_id=None):
        self.add(user_id=user_id)
        self.commit()

    def _add_metadata(self, user_id=None):
        if not user_id:
            user_id = get_request_user_id()
        self.created_by = user_id
        self.last_modified_by = user_id

    def _update_metadata(self, *args, user_id=None, **kwargs):
        history_entry = self._get_history_entry()
        if history_entry is None:
            return
        self.history = [*self.history, history_entry]
        if not user_id:
            user_id = get_request_user_id()
        self.last_modified_by = user_id
        self.last_modified_at = datetime.now()

    def _get_history_entry(self):
        state = db.inspect(self)
        old_state_for_changed = {
            attr.key: attr.load_history().deleted[0]
            for attr in state.attrs
            if attr.load_history().has_changes()
        }

        if not old_state_for_changed:
            return None
        dump = {
            **self.to_dict(),
            **old_state_for_changed
        }
        # create a clone of the original model, pre-update
        model = self.__class__(dump)
        return self.schema.create_history_entry(model)
