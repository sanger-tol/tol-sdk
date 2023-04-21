# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from uuid import uuid4

from tol.api_base.datasource.api_upsert_parser import ApiUpsertObject


class TestApiUpsertObject:
    def test_no_relationships(self):
        """
        No relationships, no ID, just simple attributes
        """
        __uuid = uuid4().hex
        json_dict = {
            'type': 'test',
            '_uuid': __uuid,
            'attributes': {
                'test1': 'me',
                'test2': 'you'
            }
        }
        parsed = ApiUpsertObject(json_dict)
        assert parsed.id is None
        assert parsed.type == 'test'
        assert parsed._request_internal_uuid == __uuid
        assert parsed.attributes == {
            'test1': 'me',
            'test2': 'you'
        }
        assert parsed.to_one_relationships == {}
        assert parsed.to_many_relationships == {}

    def test_to_one_relationships(self):
        """
        Include just to-one relationships
        """
        __uuid = uuid4().hex
        one_uuids = {
            'live': uuid4().hex,
            'something': uuid4().hex
        }
        json_dict = {
            'type': 'testdsf98f',
            'id': 'laughlol',
            '_uuid': __uuid,
            'relationships': {
                'one': one_uuids
            }
        }
        parsed = ApiUpsertObject(json_dict)
        assert parsed.id == 'laughlol'
        assert parsed.type == 'testdsf98f'
        assert parsed._request_internal_uuid == __uuid
        assert parsed.attributes == {}
        assert parsed._to_one_uuids == one_uuids
        assert parsed._to_many_uuids == {}

    def test_to_many_relationships(self):
        """
        Include just to-many relationships
        """
        __uuid = uuid4().hex
        many_uuids = {
            '1': [
                uuid4().hex for _ in range(234)
            ],
            '5': [uuid4().hex]
        }
        json_dict = {
            'type': 'jadsfk',
            '_uuid': __uuid,
            'relationships': {
                'many': many_uuids
            }
        }
        parsed = ApiUpsertObject(json_dict)
        assert parsed.type == 'jadsfk'
        assert parsed.id is None
        assert parsed._request_internal_uuid == __uuid
        assert parsed.attributes == {}
        assert parsed._to_one_uuids == {}
        assert parsed._to_many_uuids == many_uuids

    def test_all_fields(self):
        """
        Attributes, and both kinds of relationships
        """
        __uuid = uuid4().hex
        one_uuids = {
            'live': uuid4().hex,
            'something': uuid4().hex
        }
        many_uuids = {
            '1': [
                uuid4().hex for _ in range(234)
            ],
            '5': [uuid4().hex]
        }
        json_dict = {
            'type': 'test',
            '_uuid': __uuid,
            'id': 'hype1234',
            'attributes': {
                'test1': 'me',
                'test2': 'you'
            },
            'relationships': {
                'one': one_uuids,
                'many': many_uuids
            }
        }
        parsed = ApiUpsertObject(json_dict)
        assert parsed.id == 'hype1234'
        assert parsed.type == 'test'
        assert parsed._request_internal_uuid == __uuid
        assert parsed.attributes == {
            'test1': 'me',
            'test2': 'you'
        }
        assert parsed._to_one_uuids == one_uuids
        assert parsed._to_many_uuids == many_uuids
