# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict
from unittest import TestCase

from tol.actions import Action
from tol.core import DataSource


class _MockDataSource(DataSource):
    """Empty DataSource for testing"""

    @property
    def supported_types(self):
        return ['non-relational']

    @property
    def attribute_types(self):
        return {
            'non-relational': {}
        }


class MockAction(Action):
    def __init__(self):
        super().__init__()

    def run(
        self,
        ids: list[str],
        datasource: DataSource,
        object_type: str,
        params: dict[str, Any] | None = None
    ) -> tuple[Dict[str, bool], int]:
        return {'success': True}, 200


class TestAction(TestCase):
    def test_run(self):
        action = MockAction()
        self.assertEqual(
            action.run(
                ids=['id1', 'id2'],
                datasource=_MockDataSource({}),
                params=None,
                object_type='test_type'
            ),
            ({'success': True}, 200)
        )
