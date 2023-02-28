# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestFilterWildcard(BaseTestCase):
    def test_string_good_delimiters_list_get_g_200(self):
        self.add_g(id=101, string_column='match', bool_column=True)
        self.add_g(id=1090, string_column='no metch', bool_column=False)  # contains a typo

        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"match"}}'
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
                    'total': 1
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

    def test_wildcard_escaping(self):
        self.add_g(
            id=2002,
            string_column='this should only match directly!'
        )
        self.add_g(
            id=2003,
            string_column="don't match anything please :)"
        )

        # try to get it directly
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column": " should only"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check 1 retrived result
        self.assertEqual(len(response.json['data']), 1)

        # underscore matches just one character.
        # Check that it doesn't either added G (especially the first)
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"this should only match directly_"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check no retrieved results
        self.assertEqual(len(response.json['data']), 0)

        # precent sign matches any string. Check that it doesn't match either added G
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"%"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check no retrieved results
        self.assertEqual(len(response.json['data']), 0)

    def test_wildcard_non_string_400(self):
        self.add_g(id=2004)

        # try to filter against each non string column
        #
        # float
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"float_column":"not a string"}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check specific error message
        assert (
            response.json['errors'][0]['title'] == 'Wildcard filter on non-string column'
        )
        # bool
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"bool_column":"not a string"}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check specific error message
        assert (
            response.json['errors'][0]['title'] == 'Wildcard filter on non-string column'
        )
        # datetime
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"datetime_column":"not a string"}}'
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check specific error message
        assert (
            response.json['errors'][0]['title'] == 'Wildcard filter on non-string column'
        )

    def test_search_string_has_wildcard_underscore(self):
        self.add_g(
            id=2004,
            string_column='This has % a single character that is a wildcard.'
        )
        self.add_g(
            id=4594985,
            string_column='Nope'
        )

        # filter against a direct match around it
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"has % a singl"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check only 1 retrieved result
        self.assertEqual(len(response.json['data']), 1)

        # no matches trying to use the underscore single-char wildcard
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"has _ a singl"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check no retrieved results
        self.assertEqual(len(response.json['data']), 0)

    def test_search_string_has_wildcard_percent(self):
        self.add_g(
            id=2034,
            string_column='This has _ a single character that is a wildcard.'
        )
        self.add_g(
            id=458985,
            string_column='Nope'
        )

        # filter against a direct match around it
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"has _ a singl"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check only 1 retrieved result
        self.assertEqual(len(response.json['data']), 1)

        # no matches trying to use the percent-sign wildcard
        response = self.client.open(
            '/api/v1/g?filter={"wildcard":{"string_column":"has % a singl"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check no retrieved results
        self.assertEqual(len(response.json['data']), 0)

    def test_both_wildcard_and_exact_filter(self):
        self.add_g(
            id=2034,
            string_column='This is a test',
            bool_column=False
        )
        self.add_g(
            id=458985,
            string_column='This is a test too!',
            bool_column=True
        )

        # filter should return only one, combining both:
        # - wildcard "a test"
        # - exact True
        response = self.client.open(
            '/api/v1/g?filter='
            '{"exact":{"bool_column": true},"wildcard":{"string_column":"a test"}}'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # check only 1 retrieved result
        self.assertEqual(len(response.json['data']), 1)
