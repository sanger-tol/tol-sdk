# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from tol.core import DataSource


class DataSourceFixture(ABC):
    """
    Manages a given `DataSource` as a fixture in pytest
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this `DataSource` - used as ID in tests"""

    @abstractmethod
    def get_ds_instance(self) -> DataSource:
        """
        Called before each test, to get a `DataSource` instance.

        Can be either new every time, or a singleton.
        """

    @abstractmethod
    def after_test(self) -> None:
        """
        Called after each test.

        Can be used for cleanup between tests.
        """

    @abstractmethod
    def tear_down(self) -> None:
        """
        Called by pytest when finished with this fixture.

        Do NOT call manually.
        """
