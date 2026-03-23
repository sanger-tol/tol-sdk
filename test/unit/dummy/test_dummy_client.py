# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.dummy.client import DummyClient


class TestDummyClient:
    """The `DummyClient` and its methods"""

    def test_get_detail(self):
        """Default values, no token"""

        client = DummyClient()
        objs = [
            {
                'id': i,
                'little_string': ['a', 'b', 'c'][i % 3],
                'big_string': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[i % 52],
                'int': i,
                'bool': i % 2 == 0,
                'date': f'2024-01-{(i % 28) + 1:02d}',
                'type': 'record',
                'category': ['cat1', 'cat2', 'cat3', 'cat4'][i % 4],
            }
            for i in range(1, 3)
        ]
        expected = [
            objs[0],
            objs[1]
        ]

        observed = client.get_detail('record', [1, 2])
        assert observed == expected

    def test_get_list(self):
        """Default values, no token"""

        client = DummyClient()
        objs = [
            {
                'id': i,
                'little_string': ['a', 'b', 'c'][i % 3],
                'big_string': 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[i % 52],
                'int': i,
                'bool': i % 2 == 0,
                'date': f'2024-01-{(i % 28) + 1:02d}',
                'type': 'record',
                'category': ['cat1', 'cat2', 'cat3', 'cat4'][i % 4],
            }
            for i in range(0, 2)
        ]

        observed = client.get_list('record')
        assert len(observed) == 10000
        assert observed[0] == objs[0]
        assert observed[1] == objs[1]
