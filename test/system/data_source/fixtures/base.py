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
    def before_test(self) -> None:
        """
        Called before each test (separately from
        `DataSourceFixture().get_ds_instance()`).

        Used for setup that must occur on both the core
        fixture, as well as the very same behind an API.
        """

    def sleep(self, time_: float) -> None:
        """
        Requests a specific `time_` seconds to pause
        execution. Some fixtures, i.e. the (api ->) sql
        pair, ignore these instructions (which is the
        default).
        """
