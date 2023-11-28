# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from string import ascii_uppercase

import pytest

from tol.api_base2.misc import RelataionshipHopsParser
from tol.core import DataSourceError


class TestRelationshipHopsParser:
    def test_populated_string(self):
        """
        `RelataionshipHopsParser().relationship_hops` with
        a valid, populated string
        """

        in_ = '/'.join(ascii_uppercase)
        expected = list(ascii_uppercase)

        self.__compare(in_, expected)

    def test_invalid_string(self):
        """
        `RelataionshipHopsParser().relationship_hops` with
        an invalid string raises `DataSourceError`.
        """

        # empty relationship hops
        self.__assert_invalid('a/b//d////h')
        # fully empty string
        self.__assert_invalid('')
        # only whitespace
        self.__assert_invalid('      ')

    def __compare(self, in_: str, expected: list[str]):
        observed = self.__hops(in_)

        assert observed == expected

    def __hops(self, in_: str) -> list[str]:
        return RelataionshipHopsParser(in_).relationship_hops

    def __assert_invalid(self, in_: str):
        with pytest.raises(DataSourceError):
            self.__hops(in_)
