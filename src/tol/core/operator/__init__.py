# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Union

from .aggregator import Aggregator
from .deleter import Deleter
from .detail_getter import DetailGetter
from .list_getter import ListGetter
from .page_getter import PageGetter
from .relational import Relational
from .updater import Updater
from .upserter import Upserter


Operator = Union[
    Aggregator,
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
]
"""
A type hint, indicating that any number of operators are implemented
"""
