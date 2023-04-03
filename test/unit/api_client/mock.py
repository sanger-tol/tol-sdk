# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Any, Callable

import responses

from tol.api_client import ApiDataSource


TEST_URL = 'http://testing.lan'
TEST_KEY = 'just-testing :)'


api_ds = ApiDataSource(
    {
        'url': TEST_URL,
        'key': TEST_KEY
    }
)


def assert_upsert_body(request_body: Any) -> None:
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.url == f'{TEST_URL}/upsert'
    assert call.request is False  # change this!!!!


def mock_upsert(function: Callable) -> Callable:

    @responses.activate
    @wraps(function)
    def wrapper(self, *args, **kwargs) -> Any:
        return function(self, *args, **kwargs)
    return wrapper
