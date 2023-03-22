# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from ..test_case import BaseTestCase


class TestFilterTypes(BaseTestCase):
    def test_string_good_delimiters_list_get_g_200(self):
        self.add_g(id=101, string_column='match', bool_column=True)
        self.add_g(id=1090, string_column='no match', bool_column=False)

        response = self.client.open(
            '/api/v1/g?filter={"exact":{"string_column":"match"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check only 1 retrieved result
        self.assertEqual(len(response.json['data']), 1)

        # confirm it's the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 1,
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
                        'id': '101',
                        'attributes': {
                            'float_column': None,
                            'bool_column': True,
                            'datetime_column': None,
                            'string_column': 'match'
                        }
                    }
                ]
            }
        )

    def test_float_filter_correct_list_get_g_200(self):
        self.add_g(id=501, string_column='laughter', float_column=9.16)
        self.add_g(id=17890, string_column='good medicine', float_column=1.89)

        # filter for one
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"float_column":1.89}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # check only 1 retrieved result
        self.assertEqual(len(response.json['data']), 1)

        # check the result is the correct one
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 1,
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
                        'id': '17890',
                        'attributes': {
                            'float_column': 1.89,
                            'bool_column': None,
                            'datetime_column': None,
                            'string_column': 'good medicine'
                        }
                    }
                ]
            }
        )

        # filter for none
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"float_column":42.9}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert no results
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 0,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': []
            }
        )

    def test_datetime_filter_correct_list_get_g_200(self):
        first_datetime = datetime.now()
        second_datetime = datetime.now()
        self.add_g(id=501, string_column='hamburger', datetime_column=first_datetime)
        self.add_g(id=17890, string_column='cat', datetime_column=second_datetime)

        # filter for none
        response = self.client.open(
            f'/api/v1/g?filter={{"exact": {{"datetime_column": "{str(datetime.now())}"}}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert no results
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 0,
                    'types': {
                        'id': 'int',
                        'float_column': 'float',
                        'bool_column': 'bool',
                        'datetime_column': 'datetime',
                        'string_column': 'str'
                    }
                },
                'data': []
            }
        )

        # filter for one
        response = self.client.open(
            f'/api/v1/g?filter={{"exact": {{"datetime_column":"{str(first_datetime)}"}}}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # one result, and is correct
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 1,
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
                        'id': '501',
                        'attributes': {
                            'float_column': None,
                            'bool_column': None,
                            'datetime_column': first_datetime.strftime(
                                '%Y-%m-%dT%H:%M:%S.%f'
                            ),
                            'string_column': 'hamburger'
                        }
                    }
                ]
            }
        )

    def test_multiple_filters_correct_list_get_c_200(self):
        # testing bool and float
        self.add_g(id=999, float_column=1.0, bool_column=True)
        self.add_g(id=1021, float_column=49584.0, bool_column=True)
        self.add_g(id=34989, float_column=1.0, bool_column=False)

        # get none
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"float_column":898.34,"bool_column":true}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 0)

        # get one
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"float_column":1.0,"bool_column":true}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 1)
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 1,
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
                        'id': '999',
                        'attributes': {
                            'float_column': 1.0,
                            'bool_column': True,
                            'datetime_column': None,
                            'string_column': None
                        }
                    }
                ]
            }
        )

    def test_bad_json_filter(self):
        """Has a bad JSON string"""

        # missing a closing brace
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"float_column":898.34,"bool_column":true}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        # missing an opening brace
        response = self.client.open(
            '/api/v1/g?filter={"exact":"float_column":898.34,"bool_column":true}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_string_delimiters_in_filter(self):
        # contains an (escaped) string delimiter
        response = self.client.open(
            '/api/v1/g?filter={"exact":{"string_column":"this one\'s gnarly string"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
