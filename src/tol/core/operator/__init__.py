# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Union

from .aggregator import Aggregator
from .counter import Counter
from .declare import get_operator_member_names  # noqa
from .deleter import Deleter
from .detail_getter import DetailGetter
from .enum import OperatorMethod  # noqa
from .group_statter import GroupStatter
from .inserter import Inserter
from .list_getter import ListGetter
from .operator_config import OperatorDict  # noqa
from .page_getter import PageGetter
from .relational import Relational
from .statter import Statter
from .updater import Updater
from .upserter import Upserter


ALL_OPERATORS = (
    Aggregator,
    Counter,
    Deleter,
    DetailGetter,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Relational,
    Statter,
    Updater,
    Upserter,
)


# TODO - deduplicate using python 3.11
#
# Operator = Union[*ALL_OPERATORS]
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
    Statter,
    Updater,
    Upserter
]
"""
A type hint, indicating that any number of operators are implemented
"""
