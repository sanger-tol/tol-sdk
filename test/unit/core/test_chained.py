# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any
from unittest.mock import create_autospec

import pytest

from tol.core import (
    ChainedConverter,
    Converter,
    DataObject
)


@dataclass
class Converters:
    a: Converter
    b: Converter
    c: Converter


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


def __convert(in_: DataObject, char: str) -> DataObject:
    new_attributes = {
        k: f'{v}_{char}' if isinstance(v, str) else v
        for k, v in in_.attributes.items()
    }

    return _mock_do(
        attributes=new_attributes
    )


def __mock_converter(char: str) -> Converter:
    mock_converter: Converter = create_autospec(
        Converter,
        spec_set=True
    )
    mock_converter.convert.side_effect = (
        lambda in_: __convert(in_, char)
    )

    return mock_converter


@pytest.fixture
def converters() -> Converters:
    return Converters(
        *[
            __mock_converter(char)
            for char in 'abc'
        ]
    )


class TestChainedConverter:
    """
    All converters suffix any `str` attribute
    with their given `char`.
    """

    def test_one(
        self,
        converters: Converters
    ):

        cc = ChainedConverter(
            converters.a
        )

        in_ = _mock_do(
            attributes={
                'hello': 'world',
                'welcome': True,
                'answer': 42,
                'certainty': 100.0
            }
        )

        expected = {
            'hello': 'world_a',
            'welcome': True,
            'answer': 42,
            'certainty': 100.0
        }
        observed = cc.convert(in_).attributes

        assert observed == expected

        converters.a.convert.assert_called_once()

    def test_many(
        self,
        converters: Converters
    ):

        cc = ChainedConverter(
            converters.a,
            converters.b,
            converters.c
        )

        in_ = _mock_do(
            attributes={
                'hello': 'world',
                'welcome': True,
                'answer': 42,
                'certainty': 100.0
            }
        )

        expected = {
            'hello': 'world_a_b_c',
            'welcome': True,
            'answer': 42,
            'certainty': 100.0
        }
        observed = cc.convert(in_).attributes

        assert observed == expected

        converters.a.convert.assert_called_once()
        converters.b.convert.assert_called_once()
        converters.c.convert.assert_called_once()
