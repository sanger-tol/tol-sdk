# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

import requests


STS_URL = os.getenv('STS_URL')
STS_API_KEY = os.getenv('STS_API_KEY')


def __override_method(method, relative_url, headers=None, **kwargs):
    if headers is None:
        new_headers = {
            'Authorization': STS_API_KEY
        }
    else:
        new_headers = {
            'Authorization': STS_API_KEY,
            **headers
        }
    return method(
        f'{STS_URL}/api/v1/{relative_url}',
        headers=new_headers,
        **kwargs
    )


def get(relative_url, **kwargs):
    return __override_method(
        requests.get,
        relative_url,
        **kwargs
    )


def post(relative_url, **kwargs):
    return __override_method(
        requests.post,
        relative_url,
        **kwargs
    )


def put(relative_url, **kwargs):
    return __override_method(
        requests.put,
        relative_url,
        **kwargs
    )


def patch(relative_url, **kwargs):
    return __override_method(
        requests.patch,
        relative_url,
        **kwargs
    )


def delete(relative_url, **kwargs):
    return __override_method(
        requests.delete,
        relative_url,
        **kwargs
    )
