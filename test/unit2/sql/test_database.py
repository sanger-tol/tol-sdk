# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from sqlalchemy.orm import Mapped, mapped_column

from tol.sql.database import DefaultDatabase
from tol.sql.model import model_base


BaseModel = model_base()


class _TestModel(BaseModel):

    __tablename__ = 'test'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    int_column: Mapped[int] = mapped_column()


class TestDefaultDatabase:
    def test_get_by_id_not_found(self):
        """get_by_id() gets a non-existent row -> return None"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    # return no results for searching id == 404
                    [
                        mock.call.query(_TestModel),
                        mock.call.filter(_TestModel.id == '404')
                    ],
                    []
                ),
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_by_id('test', '404')
        assert result is None

    def test_get_by_id_exists(self):
        """get_by_id() gets an existing row -> return it"""

        expected = _TestModel(
            id='302'
        )

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.filter(_TestModel.id == '302')
                    ],
                    [expected]
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_by_id('test', '302')
        assert result == expected

    def test_get_by_non_standard_id_column(self):
        """get_by_id using a different id_column"""

        class _OverrideIdModel(BaseModel):

            __tablename__ = 'test_override'

            id_other: Mapped[str] = mapped_column(primary_key=True)

            @classmethod
            def get_id_column_name(cls) -> str:
                return 'id_other'

        expected = _OverrideIdModel(id_other='302')

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_OverrideIdModel),
                        mock.call.filter(_OverrideIdModel.id_other == '302')
                    ],
                    [expected]
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_OverrideIdModel]
        )
        result = db.get_by_id('test_override', '302')
        assert result == expected

    def test_get_list_page_none_found(self):
        """get_list_page that returns no results at all, no filters"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.limit(100),
                        mock.call.offset(300)
                    ],
                    []
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == []

    def test_get_list_page_some(self):
        """get_list_page that does find some results, and returns them"""

        expected = [
            _TestModel(id=i)
            for i in range(300, 400)
        ]
        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.limit(100),
                        mock.call.offset(300)
                    ],
                    expected
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == expected

    def test_count_no_results(self):
        """count() works with no results (no filters) -> returns 0"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel)
                    ],
                    []  # no results
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.count('test')
        assert result == 0

    def test_count_results_found(self):
        """count() works with some results found (no filters)"""

        expected = list(range(234))

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel)
                    ],
                    expected
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.count('test')
        assert result == 234
