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
                'sub_category': ['cat1', 'cat2', 'cat3', 'cat4'][(i - 1) % 4],
                'list': ['alpha', 'beta', 'gamma'],
                'link': 'https://www.google.com/',
                'links': [
                    'https://www.google.com/',
                    'https://www.instagram.com/',
                    'https://www.facebook.com/',
                    'https://www.twitter.com/',
                ],
                'image': {
                    'url': 'https://picsum.photos/200/300',
                    'caption': 'cap1',
                },
                'images': [
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap1'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap2'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap3'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap4'},
                ],
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
                'sub_category': ['cat1', 'cat2', 'cat3', 'cat4'][(i - 1) % 4],
                'list': ['alpha', 'beta', 'gamma'],
                'link': 'https://www.google.com/',
                'links': [
                    'https://www.google.com/',
                    'https://www.instagram.com/',
                    'https://www.facebook.com/',
                    'https://www.twitter.com/',
                ],
                'image': {
                    'url': 'https://picsum.photos/200/300',
                    'caption': 'cap1',
                },
                'images': [
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap1'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap2'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap3'},
                    {'url': 'https://picsum.photos/200/300', 'caption': 'cap4'},
                ],
            }
            for i in range(0, 2)
        ]

        observed = client.get_list('record')
        assert len(observed) == 20000
        assert observed[0] == objs[0]
        assert observed[1] == objs[1]

    def test_get_list_category(self):
        client = DummyClient()

        observed = client.get_list('category')

        assert observed == [
            {'id': 'cat1', 'name': 'CAT1', 'type': 'category'},
            {'id': 'cat2', 'name': 'CAT2', 'type': 'category'},
            {'id': 'cat3', 'name': 'CAT3', 'type': 'category'},
            {'id': 'cat4', 'name': 'CAT4', 'type': 'category'},
        ]
