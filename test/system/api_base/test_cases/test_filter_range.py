# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestFilterRange(BaseTestCase):
    def test_range_on_float(self):
        self.add_g(id=991, float_column=1.1)
        self.add_g(id=992, float_column=2.1)
        self.add_g(id=993, float_column=3.1)
        self.add_g(id=994, float_column=3.1)
        self.add_g(id=995, float_column=5.1)
        self.add_g(id=996, float_column=6.1)

        response = self.client.open(
            '/api/v1/g?filter={"range":{"float_column":{"from":2.1,"to":4.1}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check retrieved 3 results as range includes number given
        self.assertEqual(len(response.json['data']), 3)

        # confirm it's the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 3,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'g',
                        'id': '992',
                        'attributes': {
                            'float_column': 2.1,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '993',
                        'attributes': {
                            'float_column': 3.1,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '994',
                        'attributes': {
                            'float_column': 3.1,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    }
                ]
            }
        )

    def test_range_on_int(self):
        self.add_g(id=640)
        self.add_g(id=641)
        self.add_g(id=642)
        self.add_g(id=643)

        response = self.client.open(
            '/api/v1/g?filter={"range":{"id":{"from":640,"to":642}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check retrieved 3 results as range includes number given
        self.assertEqual(len(response.json['data']), 3)

        # confirm it's the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 3,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'g',
                        'id': '640',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '641',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '642',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': None
                        }
                    }
                ]
            }
        )

    def test_range_on_datetime(self):
        self.add_g(id=780, datetime_column='2020-11-03 14:42:17')
        self.add_g(id=781, datetime_column='2020-11-04 14:42:17')
        self.add_g(id=782, datetime_column='2020-11-05 14:42:17')
        self.add_g(id=783, datetime_column='2020-11-06')
        self.add_g(id=784, datetime_column='2020-11-07 14:42:17')

        # test detailed date
        response = self.client.open(
            '/api/v1/g?filter={"range":{"datetime_column":{'
            '"from":"2020-11-04T14:42:17","to":"2020-11-06T14:42:17"}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check retrieved 3 results as range includes number given
        self.assertEqual(len(response.json['data']), 3)

        # confirm it's the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 3,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'g',
                        'id': '781',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-04T14:42:17',
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '782',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-05T14:42:17',
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '783',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-06T00:00:00',
                            'string_column': None
                        }
                    }
                ]
            }
        )

        # test a simplified date
        response = self.client.open(
            '/api/v1/g?filter={"range":{"datetime_column":{'
            '"from":"2020-11-04","to":"2020-11-06"}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check retrieved 3 results as range includes number given
        self.assertEqual(len(response.json['data']), 3)

        # confirm it's the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 3,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': [
                    {
                        'type': 'g',
                        'id': '781',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-04T14:42:17',
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '782',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-05T14:42:17',
                            'string_column': None
                        }
                    },
                    {
                        'type': 'g',
                        'id': '783',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': '2020-11-06T00:00:00',
                            'string_column': None
                        }
                    }
                ]
            }
        )

    def test_range_errors(self):
        # test a mix of types entered (number and datetime)
        response = self.client.open(
            '/api/v1/g?filter={"range":{"datetime_column":{'
            '"from":25,"to":"2020-11-06T14:42:17"}}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json['errors'][0]['detail'],
            "The filter value '25' must be a valid datetime."
        )

        # test a mix of types entered (int and float)
        response = self.client.open(
            '/api/v1/g?filter={"range":{"id":{'
            '"from":25,"to":"39.330"}}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json['errors'][0]['detail'],
            "The filter value '39.330' must be an integer."
        )

        # test incorrect range params given
        response = self.client.open(
            '/api/v1/g?filter={"range":{"datetime_column":{'
            '"RANDOM":25}}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json['errors'][0]['detail'],
            "The range filter JSON should only contain 2 entries: 'from' and 'to'."
        )
