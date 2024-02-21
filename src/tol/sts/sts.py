# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# DO NOT WRITE ANYTHING NEW THAT USES THESE FUNCTIONS AS THEY WILL BE DELETED AT SOME POINT


from dateutil.parser import parse as dateutil_parse

from . import sts_requests


def get_setting(setting_key):
    r = sts_requests.get(f'/settings/{setting_key}')
    if r.status_code != 200:
        print(r.status_code)
        return None
    return r.json()['data']['value']


def update_setting(setting_key, new_value):
    r = sts_requests.put(
        '/settings',
        json={
            'key': setting_key,
            'value': new_value
        }
    )
    return r.status_code == 200


def get_datetime_setting(setting_key):
    value = get_setting(setting_key)
    if value is None:
        return None
    return dateutil_parse(value)


def update_datetime_setting(setting_key, new_value, fmt=None):
    string_datetime = str(new_value) if fmt is None else new_value.strftime(fmt)
    return update_setting(
        setting_key,
        string_datetime
    )
