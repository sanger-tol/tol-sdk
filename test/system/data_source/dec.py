# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import inspect
import typing
from functools import wraps
from typing import Callable

import pytest

if typing.TYPE_CHECKING:
    from .fixtures.api.util import ApiFixture
    from .fixtures.base import DataSourceFixture


def against(*fixtures: DataSourceFixture) -> Callable:
    """
    Repeats the test against each given `DataSourceFixture` instance.
    """

    params = [
        pytest.param(dsf, dsf.sleep, id=dsf.name) for dsf in fixtures
    ]

    def decorator(test_method: Callable) -> Callable:

        @wraps(test_method)
        @pytest.mark.parametrize(
            ('data_source', 'ds_sleep'),
            params
        )
        def wrapper(
            self,
            data_source: DataSourceFixture,
            ds_sleep: Callable[[float], None]
        ) -> None:

            # a little hacky, but the names must match
            fixture = data_source

            fixture.before_test()
            ds_instance = fixture.get_ds_instance()
            kwargs = {data_source: ds_instance, ds_sleep: ds_sleep}
            if 'fixture_name' in inspect.signature(test_method).parameters:
                kwargs['fixture_name'] = fixture.name
            test_method(self, **kwargs)
            fixture.after_test()

        return wrapper

    return decorator


def against_api(*fixtures: ApiFixture) -> Callable:
    """
    Repeats the test against each given `ApiFixture` instance.

    Note a URL is given as well.
    """

    params = [
        pytest.param(dsf, dsf.url, dsf.sleep, dsf.name, id=dsf.name)
        for dsf in fixtures
    ]

    def decorator(test_method: Callable) -> Callable:

        @wraps(test_method)
        @pytest.mark.parametrize(
            ('data_source', 'url', 'ds_sleep'),
            params
        )
        def wrapper(
            self,
            data_source: ApiFixture,
            url: str,
            ds_sleep: Callable[[float], None],
        ) -> None:

            # a little hacky, but the names must match
            fixture = data_source

            fixture.before_test()
            ds_instance = fixture.get_ds_instance()
            test_method(
                self,
                data_source=ds_instance,
                url=url,
                ds_sleep=ds_sleep,
            )
            fixture.after_test()

        return wrapper

    return decorator
