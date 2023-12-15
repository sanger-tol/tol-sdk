# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSource

from ..dec import against
from ..fixtures import elastic, sql


class TestEndToEnd:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(elastic, sql)
    def test_fake(self, data_source: DataSource):
        pass
