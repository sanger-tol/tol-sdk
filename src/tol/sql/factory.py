# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import List, Type

from .model import Model
from .sql_datasource import SqlDataSource


def sql_datasource(models: List[Type[Model]], db_uri: str) -> SqlDataSource:
    """
    Creates an SqlDataSource instance using:

    - a list of Model classes
    - a string database URI
    """
