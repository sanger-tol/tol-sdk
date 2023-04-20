# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestRelationListGet(BaseTestCase):
    def test_relation_list_get_a_b_200(self):
        # add two A's
        self.add_a(id=20)
        self.add_a(id=29)

        # add two B's on the first A
        self.add_b(id_string='89', a_id=20)
        self.add_b(id_string='290', a_id=20)

        # add one B on the second A
        self.add_b(id_string='8080', a_id=29)

        # get the first A's B's
        response = self.client.open(
            '/api/v1/a/20/b',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that 2 were found
        self.assertEqual(len(response.json['data']), 2)
        # assert that the correct two were found
        self.assertEqual(
            response.json,
            {
                'meta': {
                    'page': 1,
                    'page_size': 20,
                    'offset': 0,
                    'limit': 20,
                    'total': 2,
                    'types': {
                        'id_string': 'str',
                        'a_id': 'int'
                    }
                },
                'data': [
                    {
                        'id': '290',
                        'type': 'b',
                        'attributes': {
                            'id_string': '290'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '20',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/20'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/290/e'
                                }
                            }
                        }
                    },
                    {
                        'id': '89',
                        'type': 'b',
                        'attributes': {
                            'id_string': '89'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '20',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/20'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/89/e'
                                }
                            }
                        }
                    }
                ]
            }
        )

        # get the second A's B
        response = self.client.open(
            '/api/v1/a/29/b',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that 1 was found
        self.assertEqual(len(response.json['data']), 1)
        # assert that the correct one was found
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
                        'id_string': 'str',
                        'a_id': 'int'
                    }
                },
                'data': [
                    {
                        'id': '8080',
                        'type': 'b',
                        'attributes': {
                            'id_string': '8080'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '29',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/29'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/8080/e'
                                }
                            }
                        }
                    }
                ]
            }
        )

    def test_relation_list_get_no_stem_a_b_404(self):
        # add an irrelevant A and connected B
        self.add_a(id=99)
        self.add_b(id_string='100', a_id=99)

        # try to get the B's of a non-existent A
        response = self.client.open(
            '/api/v1/a/560/b',
            method='GET'
        )
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_relation_list_get_with_page_parameter_200(self):
        """Confirm that the page parameter works with a relation
        list get endpoint"""
        # add an A
        self.add_a(id=789)

        # add 59 B's
        for i in range(1, 60):
            self.add_b(id_string=f'{i}', a_id=789)

        # combine parameters on relation list get
        response = self.client.open(
            '/api/v1/a/789/b?page=3',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # 19 = 59 - 20*2
        self.assertEqual(len(response.json['data']), 19)

    def test_relation_list_get_with_sort_by_parameter_200(self):
        # add an A
        self.add_a(id=298)

        # add 3 B's in no particular order
        self.add_b(id_string='9090', a_id=298)
        self.add_b(id_string='348', a_id=298)
        self.add_b(id_string='200000', a_id=298)

        # combine parameters on relation list get
        response = self.client.open(
            '/api/v1/a/298/b?sort_by=-id_string',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(len(response.json['data']), 3)
        # assert they're in the right order (descending id)
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
                        'id_string': 'str',
                        'a_id': 'int'
                    }
                },
                'data': [
                    {
                        'id': '9090',
                        'type': 'b',
                        'attributes': {
                            'id_string': '9090'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '298',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/298'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/9090/e'
                                }
                            }
                        }
                    },
                    {
                        'id': '348',
                        'type': 'b',
                        'attributes': {
                            'id_string': '348'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '298',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/298'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/348/e'
                                }
                            }
                        }
                    },
                    {
                        'id': '200000',
                        'type': 'b',
                        'attributes': {
                            'id_string': '200000'
                        },
                        'relationships': {
                            'a': {
                                'data': {
                                    'id': '298',
                                    'type': 'a'
                                },
                                'links': {
                                    'related': '/a/298'
                                }
                            },
                            'e': {
                                'links': {
                                    'related': '/b/200000/e'
                                }
                            }
                        }
                    }
                ]
            }
        )
