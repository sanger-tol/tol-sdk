# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from time import sleep
from typing import Dict, Iterable

import pytest

from tol.core import (
    OperableDataSource,
)

from ..dec import against
from ..fixtures import all_fixtures, api_elastic, api_sql, elastic, sql


class TestAttributeTypes:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(elastic, api_elastic)
    def test_attribute_types(self, data_source: OperableDataSource, ds_sleep):
        """
        Tests that the attribute types are correctly reported for each object type.
        """

        attribute_types = data_source.attribute_types
        expected = {
            'root': {
                'str_column': 'str',
                'int_column': 'int',
                'datetime_column': 'datetime',
                'bool_column': 'bool',
                'list_column': 'str',
                'runtime_column': 'bool',
            },
            'related': {
                'str_column': 'str',
                'int_column': 'int',
                'datetime_column': 'datetime',
                'bool_column': 'bool',
                'list_column': 'str',
                'root_int_column_min': 'double',
                'root_int_column_max': 'double',
            }
        }
        assert attribute_types == expected
