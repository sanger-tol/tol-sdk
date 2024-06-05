# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List
from unittest.mock import Mock, PropertyMock, create_autospec

from flask import Flask

from flask_testing import TestCase

from tol.core import (
    DataObject,
    DataSource,
    DataSourceFilter,
    core_data_object
)
from tol.core.operator import (
    Aggregator,
    Counter,
    Deleter,
    DetailGetter,
    Inserter,
    PageGetter,
    Relational,
    Updater,
    Upserter
)
from tol.core.operator.updater import DataObjectUpdate

from .app import _test_application


class ParrotDataSource(DataSource, DetailGetter, PageGetter, Aggregator, Counter):
    """Mimics what its told."""

    def get_by_id(self, object_type: str, object_ids, **kwargs):
        return [
            self.data_object_factory(
                object_type,
                id_=object_ids[0],
                attributes={
                    'parrot': 'parrot'
                }
            )
        ]

    def get_list_page(self, object_type: str, *args, **kwargs):
        return [
            self.data_object_factory(
                object_type,
                id_=str(i + 1),
                attributes={
                    'parrot': 'parrot'
                }
            )
            for i in range(self.get_page_size())
        ], 400  # just a silly number, arbitrary

    def get_count(self, object_type: str, *args, **kwargs):
        return 9876  # just a silly number, arbitrary

    def get_aggregations(
            self,
            object_type: str,
            aggregations: Dict,
            object_filters: DataSourceFilter = None
    ) -> Dict:
        return {
            'completed_over_time': {
                'buckets': [
                    {
                        'key_as_string': '2015-04-01T00:00:00.000Z',
                        'key': 1427846400000,
                        'doc_count': 3
                    },
                    {
                        'key_as_string': '2015-05-01T00:00:00.000Z',
                        'key': 1430438400000,
                        'doc_count': 0
                    },
                ]
            }
        }

    @property
    def supported_types(self):
        return [
            'polly',
            'wants',
            'a',
            'cracker'
        ]

    @property
    def attribute_types(self):
        return {
            'cracker': {
                'parrot': 'str'
            }
        }


class EmptyDataSource(DataSource, DetailGetter, PageGetter):
    """Never finds anything."""

    def get_by_id(self, _object_type: str, ids: List[str], *args, **kwargs):
        """This should always 404."""
        return [
            None for _ in range(len(ids))
        ]

    def get_list_page(self, *args, **kwargs):
        return [], 0

    @property
    def supported_types(self):
        return [
            'know',
            'nothing'
        ]


class WriteableDataSource(DataSource):
    """Can be augmented with "write" `Operator` classes"""

    def __init__(self):
        pass

    @property
    def supported_types(self) -> List[str]:
        return ['write', 'only']


parrot_ds = ParrotDataSource({})
empty_ds = EmptyDataSource({})


core_data_object(parrot_ds, empty_ds, WriteableDataSource())


class BlueprintTestCase(TestCase):
    def create_app(self) -> Flask:
        return _test_application(parrot_ds, empty_ds)


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
        """A good detail GET returns 200 and correct data, including decoding"""
        response = self.client.open('/data/polly/909%2f111', method='GET')
        print(response.request.url)
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'data': {
                    'type': 'polly',
                    'id': '909/111',
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

    def test_200_on_good_aggregations(self):
        """A good aggregations POST returns 200 and correct data"""
        body = {'aggs': {}}  # We are mocking the result
        response = self.client.open('/data/cracker:aggregations', method='POST', json=body)
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        expected_aggregations = {
            'completed_over_time': {
                'buckets': [
                    {
                        'key_as_string': '2015-04-01T00:00:00.000Z',
                        'key': 1427846400000,
                        'doc_count': 3
                    },
                    {
                        'key_as_string': '2015-05-01T00:00:00.000Z',
                        'key': 1430438400000,
                        'doc_count': 0
                    },
                ]
            }
        }
        self.assertEqual(
            response.json,
            {
                'meta': {'aggregations': expected_aggregations,
                         'types': {'parrot': 'str'}},
                'data': []
            }
        )

    def test_200_on_good_count(self):
        """A good count GET returns 200 and correct data"""
        response = self.client.open('/data/cracker:count', method='GET')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        self.assertEqual(
            response.json,
            {
                'meta': {'total': 9876},
                'data': []
            }
        )


class TestBlueprintDelete(TestCase):
    def create_app(self):
        class DeleteThis(WriteableDataSource, Deleter):
            def delete(
                self,
                object_type: str,
                object_ids: Iterable[str]
            ) -> None:

                assert object_type == 'only'
                assert list(object_ids) == ['20934l']

        return _test_application(DeleteThis())

    def test_200_good_delete(self):
        """`Deleter().delete()` called correctly -> 200"""

        response = self.client.open('/data/only/20934l', method='DELETE')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )


_updates = [
    [
        'hype',
        {
            '1sdkljsad': True,
            'sdfi': 39845
        }
    ],
    [
        'train',
        {
            'locomoting': 'yess mate'
        }
    ]
]


class TestBlueprintUpdate(TestCase):

    def create_app(self):
        class UpdatingToTheEnd(WriteableDataSource, Updater):
            def update(
                self,
                object_type: str,
                updates: Iterable[tuple[str, DataObjectUpdate]]
            ) -> None:

                assert object_type == 'write'
                assert updates == _updates

        return _test_application(UpdatingToTheEnd())

    def test_200_good_update(self):
        """`Updater().update()` called correctly -> 200"""

        response = self.client.open(
            '/data/write',
            method='PATCH',
            json={'data': _updates}
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )


class TestBlueprintUpsert(TestCase):

    def create_app(self):
        class NeverEverStopUpserting(WriteableDataSource, Upserter):

            @property
            def supported_types(self) -> List[str]:
                return ['write', 'only', 'hyped_up']

            def upsert(
                self,
                object_type: str,
                objects: Iterable[DataObject]
            ) -> None:

                # correct type
                assert object_type == 'write'

                # both objects are correct
                list_objects = list(objects)

                assert list_objects[0].type == object_type
                assert list_objects[0].id == '123'
                assert not list_objects[0].attributes
                # first object's to one relationship
                ones = list_objects[0]._to_one_objects
                assert len(ones) == 1
                one_relation = ones['neverending_hype']
                assert one_relation.type == 'hyped_up'
                assert one_relation.id == '23498'

                # second object
                assert list_objects[1].type == object_type
                assert list_objects[1].id == 'abc'
                assert list_objects[1].attributes == {
                    'hype': 'train'
                }

        # add a data object factory
        ds_upsert = NeverEverStopUpserting()
        core_data_object(ds_upsert)

        return _test_application(ds_upsert)

    def test_200_good_upsert(self):
        """`Upserter().upsert()` called correctly -> 200"""
        body = {
            'data': [
                {
                    'type': 'write',
                    'id': '123',
                    'relationships': {
                        'neverending_hype': {
                            'data': {
                                'type': 'hyped_up',
                                'id': '23498'
                            }
                        }
                    }
                },
                {
                    'type': 'write',
                    'id': 'abc',
                    'attributes': {
                        'hype': 'train'
                    }
                }
            ]
        }
        response = self.client.open(
            '/data/write:upsert',
            method='POST',
            json=body
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )


class TestBlueprintRelational(TestCase):

    def create_app(self):

        class _RelationalDS(DataSource, Relational):
            """Inherits both `DataSource` and `Relational`"""

        self.__mock_object = Mock()
        type(self.__mock_object).type = 'test_type'
        type(self.__mock_object).id = 'neverending-hype'
        type(self.__mock_object).attributes = {
            'yes': True,
            'int': False,
            'lol': 349508
        }

        def __get_recursive_relation(
            __s: DataObject,
            hops: list[str]
        ) -> DataObject:

            return None if hops[0] == 'not_found' else self.__mock_object

        def __get_many_page(
            __s: DataObject,
            __r_name: str,
            __page: int,
            __page_size: int
        ) -> Iterable[DataObject]:

            return [self.__mock_object]

        self.__mock_ds = create_autospec(_RelationalDS)
        type(self.__mock_ds).supported_types = PropertyMock(
            return_value=['test_type']
        )
        self.__mock_ds.get_recursive_relation.side_effect = (
            __get_recursive_relation
        )
        self.__mock_ds.get_to_many_relations_page.side_effect = (
            __get_many_page
        )
        type(self.__mock_ds).data_object_factory = PropertyMock(
            return_value=lambda *_: self.__mock_object
        )

        return _test_application(self.__mock_ds)

    def test_get_recursive_relation(self):
        """
        Tests `Relational().get_recursive_relation()`,
        behind a blueprint, at the correct endpoint.
        """

        expected = {
            'data': {
                'type': 'test_type',
                'id': 'neverending-hype',
                'attributes': {
                    'yes': True,
                    'int': False,
                    'lol': 349508
                }
            }
        }

        endpoint = (
            '/data/test_type:to-one/neverending-hype/a/b/c/d'
        )
        response = self.client.open(endpoint, method='GET')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        assert response.json == expected

        self.__mock_ds.get_recursive_relation.assert_called_once_with(
            self.__mock_object,
            ['a', 'b', 'c', 'd']
        )

    def test_get_recursive_relation_404(self):
        """
        Tests `Relational().get_recursive_relation()`,
        behind a blueprint, at the correct endpoint, with
        a 404 not found.
        """

        # include the magic phrase "not_found" as a hop
        endpoint = (
            '/data/test_type:to-one/neverending-hype/not_found/a/d'
        )
        response = self.client.open(endpoint, method='GET')
        self.assert404(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    def test_get_to_many_relations_page(self):
        """
        Tests page getter of to-many relation objects endpoint
        """

        expected = {
            'data': [
                {
                    'type': 'test_type',
                    'id': 'neverending-hype',
                    'attributes': {
                        'yes': True,
                        'int': False,
                        'lol': 349508
                    }
                }
            ]
        }

        endpoint = (
            '/data/test_type:to-many/irrelevant-id/a-nice-to-many?'
            'page=3849&page_size=1'
        )
        response = self.client.open(endpoint, method='GET')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

        assert response.json == expected

        self.__mock_ds.get_to_many_relations_page.assert_called_once_with(
            self.__mock_object,
            'a-nice-to-many',
            3849,
            1
        )


class TestInserter(TestCase):
    def create_app(self):

        insert_ds_class = type('', (DataSource, Inserter), {})

        def __obj_factory(
            type_: str,
            id_: str,
            attributes: dict = None,
            **kwargs
        ) -> DataObject:

            obj = create_autospec(DataObject, spec_set=True)
            obj.type = type_
            obj.id = id_
            obj.attributes = attributes

            return obj

        self.insert_ds = create_autospec(insert_ds_class, spec_set=True)
        self.insert_ds.supported_types = ['test']
        self.insert_ds.data_object_factory = __obj_factory

        def __side_effect(
            __obj_type,
            objs: Iterable[DataObject],
            __user_id=None
        ):
            for c, obj in zip('abcd', objs):
                assert obj.id == c
                assert obj.attributes == {c: f'attr_{c.upper()}'}

        self.insert_ds.insert.side_effect = __side_effect

        return _test_application(self.insert_ds)

    def test_insert_list(self):
        """`Inserter().insert()` on an `Iterable`"""

        body = {
            'data': [
                {
                    'type': 'test',
                    'id': c,
                    'attributes': {
                        c: f'attr_{c.upper()}'
                    }
                }
                for c in 'abcd'
            ]
        }

        response = self.client.open(
            '/data/test:insert',
            method='POST',
            json=body
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
