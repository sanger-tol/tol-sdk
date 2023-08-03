# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

from .client import ApiClient, DefaultApiClient
from .dumper import Dumper, DefaultDumper
from .parser import Parser, DefaultParser
from ..core import DataObjectFactory, DataSource
from ..core.operator import (
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
)


ClientFactory = Callable[[str, str], ApiClient]
"""Takes a URL and token, returns an instance of `ApiClient`"""


DumperFactory = Callable[[], Dumper]
"""Returns a `Dumper` instance"""


ParserFactory = Callable[[DataObjectFactory], Parser]
"""Takes a `DataObjectFactory` callable, returns a `Parser`"""


class ApiDataSource(
    DataSource,
    Deleter,
    DetailGetter,
    ListGetter,
    PageGetter,
    Relational,
    Updater,
    Upserter
):
    """
    Communicates with a remote API.
    """

    def __init__(
        self,
        url: str,
        key: str,
        client_factory: ClientFactory = lambda u, k: DefaultApiClient(u, k),
        dumper_factory: DumperFactory = lambda: DefaultDumper(),
        parser_factory: ParserFactory = lambda f: DefaultParser(f)
    ) -> None:

        self.__url = url
        self.__key = key
        self.__client_factory = client_factory
        self.__dumper_factory = dumper_factory
        self.__parser_factory = parser_factory
