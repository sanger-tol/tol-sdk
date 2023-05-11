# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List

from flask import Flask

from flask_testing import TestCase

from tol.core import (
    CoreDataObject,
    ReadOnlyDataSource,
    unsupported
)

from .app import _test_application


class ParrotDataSource(ReadOnlyDataSource):
    """Mimics what its told."""

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    def get_by_id(self, object_type: str, object_ids, **kwargs):
        return [
            CoreDataObject(
                object_type,
                {
                    'id': object_ids[0],
                    'parrot': 'parrot'
                }
            )
        ]

    def get_list_page(self, object_type: str, *args, **kwargs):
        return [
            CoreDataObject(
                object_type,
                {
                    'id': str(i + 1),
                    'parrot': 'parrot'
                }
            )
            for i in range(self.get_page_size())
        ], 400  # just a silly number, arbitrary

    @property
    def supported_types(self):
        return [
            'polly',
            'wants',
            'a',
            'cracker'
        ]

    def get_attribute_types(self, object_type: str) -> Dict:
        if object_type == 'cracker':
            return {'parrot': 'str'}


class EmptyDataSource(ReadOnlyDataSource):
    """Never finds anything."""

    def get_by_id(self, _object_type: str, ids: List[str], *args, **kwargs):
        """This should always 404."""
        return [
            None for _ in range(len(ids))
        ]

    def get_list_page(self, *args, **kwargs):
        return [], 0

    @unsupported
    def get_list(self, *args, **kwargs):
        pass

    @property
    def supported_types(self):
        return [
            'know',
            'nothing'
        ]

    def get_attribute_types(self, object_type: str) -> Dict:
        raise NotImplementedError()


class BlueprintTestCase(TestCase):
    def create_app(self) -> Flask:
        return _test_application(
            ParrotDataSource({}),
            EmptyDataSource({})
        )


class TestBlueprint(BlueprintTestCase):
    def test_404_on_empty_get_by_id(self):
        """
        EmptyDataSource().get_by_id() returning [] causes a 404
        """
        response = self.client.open('/data/know/468', method='GET')
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # make sure it 404'd for the right reason
        assert '468' in response.data.decode('utf-8')

    def test_404_on_unknown_type(self):
        """
        Using an unknown type (e.g. 'completely_fake') returns a 404
        """
        response = self.client.open('/data/completely_fake', method='GET')
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        # make sure it 404'd for the right reason
        assert 'completely_fake' in response.data.decode('utf-8')

    def test_200_on_good_detail_get(self):
        """A good detail GET returns 200 and correct data"""
        response = self.client.open('/data/polly/909', method='GET')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'polly',
                    'id': '909',
                    'attributes': {
                        'parrot': 'parrot'
                    }
                }
            }
        )

    def test_200_on_good_list_get(self):
        """A good list GET returns 200 and correct data"""
        response = self.client.open('/data/cracker', method='GET')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        expected_objects = [
            {
                'type': 'cracker',
                'id': str(i + 1),
                'attributes': {
                    'parrot': 'parrot'
                }
            }
            for i in range(len(response.json['data']))
        ]
        self.assertEqual(
            response.json,
            {
                'meta': {'total': 400,
                         'types': {'parrot': 'str'}},
                'data': expected_objects
            }
        )
