# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from tol.sql import ext
from tol.sql.model import model_base


BaseModel = model_base()  # noqa


class TestExtColumn:
    """
    Tests `ext` from `tol.sql` with and without overriding:

    - the "ext" column is added to all instances, with the
      correct name
    - `column_name` is in `Model.get_excluded_column_names()`
    """

    def test_default(self):
        """no overriding of name."""

        @ext
        class _TestModel(BaseModel):
            __tablename__ = '1'

            id: Mapped[str] = mapped_column(primary_key=True)  # noqa

        excluded = _TestModel.get_excluded_column_names()
        assert excluded == ['id', 'ext']

    def test_override(self):
        """overriding of name"""

        @ext(target='absolute')
        class _TestModel(BaseModel):
            __tablename__ = '2'

            @classmethod
            def get_id_column_name(cls) -> str:
                return 'id_override'

            id_override: Mapped[str] = mapped_column(primary_key=True)

        excluded = _TestModel.get_excluded_column_names()
        assert excluded == ['id_override', 'absolute']

    def test_promotion(self):
        """
        Given a `Mock` for an ext column, tests that its entries
        are correctly promoted.
        """

        ext_data = {
            'hype': 'train',
            'yes': False
        }

        @ext
        class _TestModel(BaseModel):
            __tablename__ = '3'

            id: Mapped[str] = mapped_column(primary_key=True)  # noqa
            already_there: Mapped[str] = mapped_column()

            @property
            def ext(self) -> dict[str, Any]:
                return ext_data

        m = _TestModel(id='101', already_there='I love this!!!')
        attrs = m.instance_attributes

        assert attrs == {
            'hype': 'train',
            'yes': False,
            'already_there': 'I love this!!!'
        }
