# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base2.view import DefaultView
from tol.core import CoreDataObject


class TestDefaultView:
    def test_dump_one_object(self):
        """
        Test dumping one object with no relationships
        """
        obj = CoreDataObject(
            'test',
            {
                'int': 45980
            }
        )
        obj.id = '9606'
        dump = DefaultView().dump(obj)
        expected = {
            'data': {
                'type': 'test',
                'id': '9606',
                'attributes': {
                    'int': 45980
                }
            }
        }
        assert dump == expected

    def test_dump_many_objects(self):
        """
        Dump a list of objects with no relationships
        """
        objs = [
            CoreDataObject('test', {'id': str(i), 'string': f'field_{i}'})
            for i in range(349)
        ]
        dump = DefaultView().dump_bulk(objs)
        expected = {
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {
                        'string': f'field_{i}'
                    }
                }
                for i in range(349)
            ]
        }
        assert dump == expected

    def test_meta(self):
        """Dump a single object with document meta"""
        obj = CoreDataObject('test', {'id': 'pop3', 'hype': 'train'})
        meta = {
            'meta': 'you bet!',
            '2+2': '5'
        }
        expected = {
            'meta': meta,
            'data': {
                'type': 'test',
                'id': 'pop3',
                'attributes': {
                    'hype': 'train'
                }
            }
        }
        observed = DefaultView().dump(obj, document_meta=meta)
        assert expected == observed

    def test_bulk_meta(self):
        """Dump many objects with document meta"""
        objs = [
            CoreDataObject('test', {'id': str(i), 'hype': 'train'})
            for i in range(50)
        ]
        meta = {
            'meta': 'you bet!',
            '2+2': '5'
        }
        expected = {
            'meta': meta,
            'data': [
                {
                    'type': 'test',
                    'id': str(i),
                    'attributes': {
                        'hype': 'train'
                    }
                }
                for i in range(50)
            ]
        }
        observed = DefaultView().dump_bulk(objs, document_meta=meta)
        assert expected == observed
