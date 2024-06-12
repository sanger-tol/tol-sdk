# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, DataSource, core_data_object


@pytest.fixture(scope='function')
def ds() -> DataSource:
    return create_autospec(
        DataSource,
        spec_set=True
    )


@pytest.fixture(scope='function')
def obj_class(
    ds: DataSource
) -> type[DataObject]:

    return core_data_object(ds)


class TestFetch:
    """
    No superfluous fetches on "False-y" to-one
    relations
    """

    def test_empty_dict(
        self,
        ds: DataSource,
        obj_class: type[DataObject]
    ):
        """
        `_to_one_objects[__k] == {}` -> no fetch
        """

    def test_none(
        self,
        ds: DataSource,
        obj_class: type[DataObject]
    ):
        """
        `_to_one_objects[__k] is None` -> no fetch
        """
