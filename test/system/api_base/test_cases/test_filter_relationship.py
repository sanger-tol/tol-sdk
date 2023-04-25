# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestFilterRelationship(BaseTestCase):
    def test_one_hop_relationship_filter(self):
        self.add_a(id=494, string_column='match')
        self.add_b(id=393, a_id=494)

        response = self.client.open(
            '/api/v1/b?filter={"exact":{"a.string_column":"match"}}'
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
                    }
                },
                'data': [
                    {
                        'type': 'b',
                        'id': '393',
                    } # add relationship later
                ]
            }
        )

    def test_two_hop_relationship_filter(self):
        self.add_a(id=494, string_column='match')
        self.add_b(id=393, a_id=494)
        self.add_e(id=595, b_id=393)

        response = self.client.open(
            '/api/v1/e?filter={"exact":{"b.a.string_column":"match"}}'
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
                    }
                },
                'data': [
                    {
                        'type': 'e',
                        'id': '595',
                    } # add relationship later
                ]
            }
        )


'''
SELECT *
FROM e
JOIN e on b
JOIN b on a
WHERE a.string_column = 'match'

--> be aware of FK names - cannot assume x_id
--> iterate through relationship dict?
'''