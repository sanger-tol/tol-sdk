# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, DataSource, core_data_object
from tol.core.operator import Relational


class _DS(DataSource, Relational):
    pass


@pytest.fixture(scope='function')
def ds() -> _DS:
    __ds = create_autospec(
        _DS,
        spec_set=True
    )

    __ds.supported_types = ['test_type']

    return __ds


@pytest.fixture(scope='function')
def obj_class(
    ds: _DS
) -> type[DataObject]:

    return core_data_object(ds)


class TestFetch:
    """
    No superfluous fetches on "False-y" to-one
    relations.
    """

    def test_empty_dict(
        self,
        ds: _DS,
        obj_class: type[DataObject]
    ):
        """
        `_to_one_objects[__k] == {}` -> no fetch
        """

        obj = obj_class(
            'test_type',
            'test ID',
            attributes={'hype': 'train'},
            to_one={'relation': {}}
        )

        assert not obj.relation
        ds.get_to_one_relation.assert_not_called()

    def test_none(
        self,
        ds: _DS,
        obj_class: type[DataObject]
    ):
        """
        `_to_one_objects[__k] is None` -> no fetch
        """

        obj = obj_class(
            'test_type',
            'test ID',
            attributes={'hype': 'train'},
            to_one={'relation': None}
        )

        assert not obj.relation
        ds.get_to_one_relation.assert_not_called()
