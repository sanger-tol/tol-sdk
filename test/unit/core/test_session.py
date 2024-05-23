# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import PropertyMock, create_autospec

import pytest

from tol.core import (
    DataObject,
    DataSource,
    DataSourceError
)
from tol.core.operator import (
    Deleter,
    PageGetter,
    Upserter
)
from tol.core.session import DataSourceSession


class TestDataSourceSession:
    """
    Tests member-proxying within `DataSourceSession`.
    """

    def test_getattr(self):
        """`getattr()` proxies to `._host`"""

        mock_ds = create_autospec(DataSource, spec_set=True)
        mock_property = PropertyMock(return_value='lol')
        type(mock_ds).lol_max = mock_property

        session = DataSourceSession(mock_ds)

        observed = session.lol_max

        mock_property.assert_called_once()
        assert observed == 'lol'

    def test_operator_not_implemented(self):
        """
        call an operation method/`property` for an
        unimplemented `Operator` -> raise
        `DataSourceError`
        """

        mixed_class = type(
            '',
            (DataSource, Deleter, PageGetter, Upserter),
            {}
        )
        mock_ds = create_autospec(mixed_class, spec_set=True)

        session = DataSourceSession(mock_ds)

        # Operation method
        with pytest.raises(DataSourceError):
            mock_obj = create_autospec(
                DataObject,
                spec_set=True
            )
            session.get_to_one_relation(
                mock_obj,
                'random_relationship'
            )

        # property on Operator
        with pytest.raises(DataSourceError):
            session.relationship_config
