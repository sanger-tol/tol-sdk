# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Any, Callable

import responses
from responses import matchers

from tol.api_client import ApiDataSource


TEST_URL = 'http://testing.lan'
TEST_KEY = 'just-testing :)'


api_ds = ApiDataSource(
    {
        'url': TEST_URL,
        'key': TEST_KEY
    }
)


def mock_upsert(status_code: int = 200) -> Callable:

    def decorator(function: Callable) -> Callable:

        @responses.activate
        @wraps(function)
        def wrapper(self, *args, **kwargs) -> Any:
            upsert_mock = responses.post(
                url=TEST_URL,
                match=[
                    matchers.header_matcher({
                        'Token': TEST_KEY
                    })
                ],
                status=status_code
            )
            return function(self, upsert_mock, *args, **kwargs)
        # prevent pytest viewing the upsert_mock as a fixture
        del wrapper.__wrapped__
        return wrapper
    return decorator
