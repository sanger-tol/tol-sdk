# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from string import ascii_lowercase
from typing import Callable
from unittest.mock import Mock, PropertyMock, call, create_autospec

import pytest

from tol.core import DataObject, DataSourceError
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig


class TestRelational:

    def test_validate_to_one_recurse_invalid(self):
        """
        `Relational().validate_to_one_recurse()` with an
        invalid relationship hop.
        """

        r_config = {
            'a': RelationshipConfig(
                to_one={'hype_train': 'b'}
            )
        }

        mock_ds = self.__create_mock_relational(r_config, None)

        with pytest.raises(DataSourceError):
            mock_ds.validate_to_one_recurse(
                'a',
                ['this is not, in any way, hype']
            )

    def test_get_recursive_relation_one(self):
        """
        `Relational().get_recursive_relation()` with
        just one `list` element
        """

        mock_object = self.__create_mock_object('test')

        get_to_one_relation = Mock()
        get_to_one_relation.return_value = mock_object

        mock_ds = self.__create_mock_relational(
            {
                'test': RelationshipConfig(
                    to_one={'fun_relation': 'test_too'}
                )
            },
            get_to_one_relation
        )

        mock_ds.get_recursive_relation(
            mock_object,
            ['fun_relation']
        )

        get_to_one_relation.assert_called_once_with(
            mock_object,
            'fun_relation'
        )

    def test_get_recursive_relation_many(self):
        """
        `Relational().get_recursive_relation()` with
        several `list` elements
        """

        def __next_char(index: int) -> str:
            return ascii_lowercase[(index + 1) % 26]

        # test_a->b, test_b->c, ..., test_y->z, test_z->a
        r_config = {
            c: RelationshipConfig(
                to_one={
                    f'test_{c}': __next_char(i)
                }
            )
            for i, c in enumerate(ascii_lowercase)
        }

        mock_objects = [
            self.__create_mock_object(c)
            for c in ascii_lowercase
        ]

        def __get_relation(
            source: DataObject,
            __relationship_name: str
        ) -> str:

            index = mock_objects.index(source)
            return mock_objects[index + 1]

        mock_get_one = Mock()
        mock_get_one.side_effect = __get_relation

        mock_ds = self.__create_mock_relational(r_config, mock_get_one)

        # expected to hop through the alphabet, excluding test_z->a
        expected_calls = [
            call(m, f'test_{m.type}')
            for m in mock_objects[:-1]
        ]

        # should be last element (z)
        expected = mock_objects[-1]

        # go 25 hops through the alphabet
        relationship_hops = [
            f'test_{c}' for c in ascii_lowercase[:-1]
        ]

        observed = mock_ds.get_recursive_relation(
            mock_objects[0],
            relationship_hops
        )

        assert mock_get_one.call_args_list == expected_calls
        assert observed == expected

    def test_get_recursive_relation_none(self):
        """
        `Relational().get_recursive_relation()` has a `None`
        value in the middle of the hops -> returns `None`
        without progressing further.
        """

        mock_object = self.__create_mock_object('1')

        def __get_relation(
            __source: DataObject,
            __relationship_name: str
        ) -> str:

            return (
                None if __relationship_name == 'not_found'
                else __source
            )

        get_to_one_relation = Mock()
        get_to_one_relation.side_effect = __get_relation

        mock_ds = self.__create_mock_relational(
            {
                '1': RelationshipConfig(
                    to_one={'not_found': '1'}
                ),
                '2': RelationshipConfig(
                    to_one={'fun_relation': '3'}
                )
            },
            get_to_one_relation
        )

        observed = mock_ds.get_recursive_relation(
            mock_object,
            ['not_found', 'fun_relation']
        )

        assert observed is None
        get_to_one_relation.assert_called_once_with(
            mock_object,
            'not_found'
        )

    def test_get_to_many_relations_page_populated(self):
        """
        `Relational().get_to_many_relations_page() returns
        a populated (not necesarilly full) slice.
        """

        in_ = [
            self.__create_mock_object('3')
            for _ in range(5)
        ]
        get_to_many_relation = Mock()
        get_to_many_relation.return_value = in_

        mock_object = self.__create_mock_object('2')

        expected = in_[2:4]

        mock_ds = self.__create_mock_relational(
            {
                '1': RelationshipConfig(
                    to_one={'not_found': '1'}
                ),
                '2': RelationshipConfig(
                    to_many={'fun_relation': '3'}
                )
            },
            None,
            get_to_many_relation=get_to_many_relation
        )

        observed = mock_ds.get_to_many_relations_page(
            mock_object,
            'fun_relation',
            2,
            2
        )

        assert list(observed) == expected
        get_to_many_relation.assert_called_once_with(
            mock_object,
            'fun_relation'
        )

    def test_get_to_many_relations_page_empty(self):
        """
        `Relational().get_to_many_relations_page() returns
        an empty slice when page is out of range.
        """

        in_ = [
            self.__create_mock_object('3')
            for _ in range(5)
        ]
        get_to_many_relation = Mock()
        get_to_many_relation.return_value = in_

        mock_object = self.__create_mock_object('2')

        expected = []

        mock_ds = self.__create_mock_relational(
            {
                '1': RelationshipConfig(
                    to_one={'not_found': '1'}
                ),
                '2': RelationshipConfig(
                    to_many={'fun_relation': '3'}
                )
            },
            None,
            get_to_many_relation=get_to_many_relation
        )

        observed = mock_ds.get_to_many_relations_page(
            mock_object,
            'fun_relation',
            2,
            7
        )

        assert list(observed) == expected
        get_to_many_relation.assert_called_once_with(
            mock_object,
            'fun_relation'
        )

    def __create_mock_relational(
        self,
        relationship_config: dict[str, RelationshipConfig],
        get_to_one_relation: Callable[[DataObject, str], DataObject],
        get_to_many_relation=None
    ) -> Relational:

        mock_ds_class = type(
            '',
            (Relational,),
            {
                'relationship_config': relationship_config,
                'get_to_many_relations': get_to_many_relation,
                'get_to_one_relation': get_to_one_relation
            }
        )

        return mock_ds_class()

    def __create_mock_object(
        self,
        type_: str
    ) -> DataObject:

        mock_object = create_autospec(DataObject)
        type(mock_object).type = PropertyMock(
            return_value=type_
        )

        return mock_object
