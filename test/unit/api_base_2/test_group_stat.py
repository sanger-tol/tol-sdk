# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.core import DataSource, OperableDataSource
from tol.core.operator import GroupStatter

from .app import _test_application


@pytest.fixture
def mock_ds() -> OperableDataSource:
    _GroupStatterDS = type(  # noqa
        '',
        (DataSource, GroupStatter),
        {}
    )

    mock_ds = create_autospec(
        _GroupStatterDS,
        spec_set=True
    )
    mock_ds.supported_types = ['test']

    return mock_ds


@pytest.fixture
def app(mock_ds: OperableDataSource) -> Flask:
    return _test_application(mock_ds)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


class TestGroupStatterAPI:
    """
    `GroupStatter` operations behind `data_blueprint`.
    """

    def test_return(
        self,
        mock_ds: OperableDataSource,
        client: FlaskClient
    ) -> None:
        """
        Complex return structure is formatted correctly.

        Most args and kwargs set.
        """

        stats_value = [
            {
                'col1': {
                    'min': 0,
                    'max': 2390
                },
                'col2': {
                    'min': 'AAAAAA',
                    'max': 'ldkfusdf'
                }
            }
        ]

        mock_ds.supported_types = ['test']
        mock_ds.get_group_stats.return_value = stats_value

        r = client.get(
            '/data/test:group-stats?'
            'group_by=col1'
            '&stats=min,max'
            '&stats_fields=col1,col2'
        )

        assert r.status_code == 200
        assert r.json == {
            'data': [],
            'meta': {
                'stats': stats_value,
                'type': 'test'
            }
        }

        mock_ds.get_group_stats.assert_called_once_with(
            'test',
            ['col1'],
            stats_fields=['col1', 'col2'],
            stats=['min', 'max'],
            object_filters=None
        )
