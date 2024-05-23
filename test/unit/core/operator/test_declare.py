# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from tol.core.operator import get_operator_member_names


class TestDeclare:

    def test_get_operator_member_names(self):
        """
        `get_operator_member_names` works.
        """

        class _TestABC(ABC):

            @property
            @abstractmethod
            def a(self) -> None:
                pass

            @classmethod
            @abstractmethod
            def b(cls) -> None:
                pass

            @abstractmethod
            def c(self) -> None:
                pass

            def not_abstract(self) -> None:
                pass

        expected = ['a', 'b', 'c', 'not_abstract']
        observed = get_operator_member_names(_TestABC)

        assert observed == expected
