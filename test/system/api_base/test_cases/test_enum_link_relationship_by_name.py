# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestEnumLinkRelationshipByName(BaseTestCase):
    def test_post_j_specify_i_by_name(self):
        self.add_i(id=4857, name='nicely')
        response = self.client.open(
            '/api/v1/j',
            method='POST',
            headers=self._get_auth_user_1_headers(),
            json={
                'data': {
                    'type': 'j',
                    'attributes': {
                        'i': 'nicely'
                    }
                }
            }
        )
        self.assert201(response)

        # get non predictable id
        created_id = response.json['data']['id']

        # assert response json is correct
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'j',
                    'id': created_id,
                    'attributes': {
                        'i': 'nicely'
                    }
                }
            }
        )

    def test_bad_enum_name_link_400(self):
        # add an enum and a dependant
        self.add_i(id=39489, name='biology')
        self.add_j(id=349992, i='biology')

        # attempt to patch the enum ref to non-existent name
        response = self.client.open(
            '/api/v1/j/349992',
            method='PATCH',
            json={
                'data': {
                    'type': 'j',
                    'attributes': {
                        'i': 'physics'
                    }
                }
            },
            headers=self._get_auth_user_1_headers()
        )
        # assert that this failed
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # assert that it failed for the right reason
        # TODO improve this error, if only for enums
        self.assertEqual(
            response.json,
            {
                'errors': [{
                    'detail': 'An integrity error occured in the database. This is '
                              'most likely due to either a dependency on this '
                              'instance, if deleting, or a foreign reference to an '
                              'object that does not exist, if creating/updating.',
                    'title': 'Integrity Error'
                }]
            }
        )
