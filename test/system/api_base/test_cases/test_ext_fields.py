# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..models import AModelRelationship, FModelWithExtField
from ..test_case import BaseTestCase


class TestExtraFieldsInRequestBody(BaseTestCase):
    def test_ext_field_does_not_exist_a(self):
        self.assertEqual(
            AModelRelationship.has_ext_column(),
            False
        )

    def test_ext_field_exists_f(self):
        self.assertEqual(
            FModelWithExtField.has_ext_column(),
            True
        )

    def test_extra_fields_post_f_201(self):
        extra_fields = {
            'extra_field': 'superfluity',
            'another_ext': 'Yet another extra field'
        }
        response = self.client.open(
            '/api/v1/f',
            method='POST',
            json={
                'data': {
                    'type': 'f',
                    'meta': {
                        'ext': extra_fields
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert201(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        id_ = response.json['data']['id']
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'f',
                    'id': id_,
                    'attributes': {
                        'other_column': None
                    },
                    'meta': {
                        'ext': extra_fields
                    }
                }
            }
        )
        f_instance = FModelWithExtField.find_by_id(id_)
        self.assertEqual(f_instance.ext, extra_fields)

    def test_no_extra_fields_post_f_201(self):
        response = self.client.open(
            '/api/v1/f',
            method='POST',
            json={
                'data': {
                    'type': 'f',
                    'attributes': {
                        'other_column': 'nice test'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert201(response)

        id_ = response.json['data']['id']
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'f',
                    'attributes': {
                        'other_column': 'nice test'
                    },
                    'id': id_,
                    'meta': {
                        'ext': {}
                    }
                }
            }
        )
        f_instance = FModelWithExtField.find_by_id(id_)
        self.assertEqual(f_instance.ext, {})

    def test_extra_fields_patch_b_400(self):
        self.add_a(id=50)
        self.add_b(id=20, a_id=50)

        response = self.client.open(
            '/api/v1/b/20',
            method='PATCH',
            json={
                'data': {
                    'type': 'b',
                    'attributes': {},
                    'meta': {
                        'ext': {
                            'extra_field': 'superfluity'
                        }
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_no_extra_fields_get_f_200(self):
        self.add_f(id=290)

        response = self.client.open(
            '/api/v1/f/290',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'f',
                    'id': '290',
                    'attributes': {
                        'other_column': None
                    },
                    'meta': {
                        'ext': {}
                    }
                }
            }
        )

    def test_variety_type_extra_fields_get_f_200(self):
        ext_data = {
            'arrayData': [27, {
                'testElement': '123'
            }],
            'float': 9090.248,
            'null': [None]
        }
        self.add_f(id=297, ext=ext_data)

        response = self.client.open(
            '/api/v1/f/297',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'f',
                    'id': '297',
                    'attributes': {
                        'other_column': None
                    },
                    'meta': {
                        'ext': ext_data
                    }
                }
            }
        )

    def test_extra_fields_overwrite_patch_f_200(self):
        self.add_f(
            id=90900,
            ext={
                'first': 'nice',
                'second': 'nicer',
                'third': 'nicest',
                'fourth': 'irrelevant'
            }
        )
        # overwrite 1,2 ; remove 3, leave 4 unchanged, add 5
        response = self.client.open(
            '/api/v1/f/90900',
            method='PATCH',
            json={
                'data': {
                    'type': 'f',
                    'attributes': {},
                    'meta': {
                        'ext': {
                            'first': 'not very nice',
                            'second': 'much less nice',
                            'third': None,
                            'fifth': 'the worst of the bunch'
                        }
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        expected = {
            'data': {
                'type': 'f',
                'id': '90900',
                'attributes': {
                    'other_column': None
                },
                'meta': {
                    'ext': {
                        'first': 'not very nice',
                        'second': 'much less nice',
                        'fourth': 'irrelevant',
                        'fifth': 'the worst of the bunch',
                    },
                }
            }
        }
        self.assertEqual(response.json, expected)
