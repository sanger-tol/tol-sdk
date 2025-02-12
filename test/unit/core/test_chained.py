# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterator
from unittest.mock import create_autospec

import pytest

from tol.core import (
    ChainedConverter,
    Converter,
    DataObject
)


def _mock_do(
    type_: str = 'test',
    id_: str = '100',
    attributes: dict[str, Any] = {}
) -> DataObject:

    mock_do: DataObject = create_autospec(DataObject)
    mock_do.type = type_
    mock_do.id = id_
    mock_do.attributes = attributes

    for k, v in attributes.items():
        setattr(mock_do, k, v)

    return mock_do


def __convert_to_one(in_: DataObject, suffix: str) -> DataObject:
    new_attributes = {
        k: f'{v}_{suffix}' if isinstance(v, str) else v
        for k, v in in_.attributes.items()
    }

    return _mock_do(
        attributes=new_attributes
    )


def __convert_to_iter(
    in_: DataObject,
    suffix: str
) -> Iterator[DataObject]:

    return (
        __convert_to_one(
            in_,
            f'{suffix}_{i}'
        )
        for i in range(3)
    )


@pytest.fixture
def to_one_converter() -> Converter:
    mock_converter: Converter = create_autospec(
        Converter,
        spec_set=True
    )
    mock_converter.convert.side_effect = (
        lambda in_: __convert_to_one(in_, 'one')
    )

    return mock_converter


@pytest.fixture
def to_iter_converter() -> Converter:
    mock_converter: Converter = create_autospec(
        Converter,
        spec_set=True
    )
    mock_converter.convert.side_effect = (
        lambda in_: __convert_to_iter(in_, 'iter')
    )

    return mock_converter


class TestChainedConverter:
    """
    All converters suffix any `str` attribute
    with their given `suffix`.
    """

    def test_to_one(
        self,
        to_one_converter: Converter
    ):
        """
        Just `to_one_converter`, no generators or `yield`.
        """

        cc = ChainedConverter(
            to_one_converter
        )

        in_ = _mock_do(
            attributes={
                'hello': 'world',
                'welcome': True,
                'answer': 42,
                'certainty': 100.0
            }
        )

        expected = [
            {
                'hello': 'world_one',
                'welcome': True,
                'answer': 42,
                'certainty': 100.0
            }
        ]
        observed = [
            o.attributes
            for o in cc.convert(in_)
        ]

        assert observed == expected

        to_one_converter.convert.assert_called_once()

    def test_to_iter(
        self,
        to_iter_converter: Converter
    ):
        """
        Just `to_iter_converter`, returning multiple
        in an `Iterator`.
        """

        cc = ChainedConverter(
            to_iter_converter
        )

        in_ = _mock_do(
            attributes={
                'hello': 'world',
                'answer': 42,
            }
        )

        expected = [
            {
                'hello': 'world_iter_0',
                'answer': 42
            },
            {
                'hello': 'world_iter_1',
                'answer': 42
            },
            {
                'hello': 'world_iter_2',
                'answer': 42
            }
        ]
        observed = [
            o.attributes
            for o in cc.convert(in_)
        ]

        assert observed == expected

        to_iter_converter.convert.assert_called_once()

    def test_many(
        self,
        to_one_converter: Converter,
        to_iter_converter: Converter
    ):

        cc = ChainedConverter(
            to_iter_converter,
            to_one_converter
        )

        in_ = _mock_do(
            attributes={
                'hello': 'world',
                'certainty': 100.0
            }
        )

        expected = [
            {
                'hello': 'world_iter_0_one',
                'answer': 42
            },
            {
                'hello': 'world_iter_1_one',
                'answer': 42
            },
            {
                'hello': 'world_iter_2_one',
                'answer': 42
            }
        ]
        observed = [
            o.attributes
            for o in cc.convert(in_)
        ]

        assert observed == expected

        to_iter_converter.convert.assert_called_once()
        to_one_converter.convert.assert_called_once()
