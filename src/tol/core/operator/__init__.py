# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Union

from .aggregator import Aggregator
from .counter import Counter
from .deleter import Deleter
from .detail_getter import DetailGetter
from .group_counter import GroupCounter
from .list_getter import ListGetter
from .page_getter import PageGetter
from .relational import Relational
from .updater import Updater
from .upserter import Upserter


Operator = Union[
    Aggregator,
    Counter,
    Deleter,
    DetailGetter,
    GroupCounter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
]
"""
A type hint, indicating that any number of operators are implemented
"""
