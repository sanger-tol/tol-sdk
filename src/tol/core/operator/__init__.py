# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Union

from .aggregator import Aggregator
from .counter import Counter
from .cursor import Cursor
from .declare import get_operator_member_names  # noqa
from .deleter import Deleter
from .detail_getter import DetailGetter
from .enricher import Enricher
from .enum import OperatorMethod, RelationWriteMode, ReturnMode  # noqa
from .group_statter import GroupStatter
from .inserter import Inserter
from .list_getter import ListGetter
from .operator_config import OperatorDict  # noqa
from .page_getter import PageGetter
from .relational import Relational
from .statter import Statter
from .summariser import Summariser
from .updater import Updater
from .upserter import Upserter


ALL_OPERATORS = (
    Aggregator,
    Counter,
    Cursor,
    Deleter,
    Relational,
    DetailGetter,
    Summariser,
    Enricher,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Statter,
    Updater,
    Upserter,
)


class AllOperatorType(
    Aggregator,
    Counter,
    Cursor,
    Deleter,
    # The below 2 are covered by Summariser
    #
    # Relational,
    # DetailGetter,
    Summariser,
    Enricher,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Statter,
    Updater,
    Upserter,
):
    """
    A maximal, type-hint class that implements
    all classes in `ALL_OPERATORS`.
    """


# TODO - deduplicate using python 3.11
#
# Operator = Union[*ALL_OPERATORS]
Operator = Union[
    Aggregator,
    Counter,
    Cursor,
    Deleter,
    DetailGetter,
    Enricher,
    GroupStatter,
    Inserter,
    ListGetter,
    PageGetter,
    Relational,
    Statter,
    Summariser,
    Updater,
    Upserter,
]
"""
A type hint, indicating that any number of operators are implemented
"""
