# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSource

from ..dec import against
from ..fixtures import all_fixtures, elastic, sql


class TestEndToEnd:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(elastic, sql)
    def test_fake(self, data_source: DataSource):
        """
        Tests against specific `DataSource` fixtures.

        Use sparingly - there needs to be a justification not
        to test against all (e.g. don't test relationship
        operations on a `DataSource` that is not `Relational`).
        """

    @against(*all_fixtures)
    def test_fake_too(self, data_source: DataSource):
        """
        Tests against all `DataSource` fixtures.

        This should be the default in most cases.
        """
