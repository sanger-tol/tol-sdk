# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Union

from .aggregator import Aggregator
from .counter import Counter
from .deleter import Deleter
from .detail_getter import DetailGetter
from .enum import OperatorMethod  # noqa
from .group_statter import GroupStatter
from .inserter import Inserter
from .list_getter import ListGetter
from .operator_config import OperatorDict  # noqa
from .page_getter import PageGetter
from .relational import Relational
from .updater import Updater
from .upserter import Upserter


Operator = Union[
    Aggregator,
    Counter,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
]
"""
A type hint, indicating that any number of operators are implemented
"""
