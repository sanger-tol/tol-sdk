# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime
import json

from tol.jira.jira_methods import parse_filter_str_to_dict


def test_parse_filter_str_to_dict_1():
    """None filter string"""
    in_ = None
    expected = {}
    assert expected == parse_filter_str_to_dict(in_)


def test_parse_filter_str_to_dict_2():
    """Empty filter string"""
    in_ = ''
    expected = {}
    assert expected == parse_filter_str_to_dict(in_)


def test_parse_filter_str_to_dict_3():
    """
    No filters, but fully specified
    """
    in_ = json.dumps({
        'exact': {}
    })
    expected = {}
    assert expected == parse_filter_str_to_dict(in_)


def test_parse_filter_str_to_dict_4():
    """
    Ignore any wildcard filters
    """
    in_ = json.dumps({
        'exact': {},
        'wildcard': {
            'fake': 'ignore'
        }
    })
    expected = {}
    assert expected == parse_filter_str_to_dict(in_)


def test_parse_filter_str_to_dict_5():
    """
    Complex test
    """
    now = str(datetime.datetime.now())
    float_ = 0.23898
    bool_ = True
    int_ = 394839
    string_ = '2390483jkdfjd+'
    in_ = json.dumps({
        'exact': {
            'date_time': now,
            'float': float_,
            'bool': bool_,
            'int': int_,
            'string': string_
        },
        'wildcard': {
            'fake': 'ignore'
        }
    })
    expected = {
        'date_time': now,
        'float': float_,
        'bool': bool_,
        'int': int_,
        'string': string_
    }
    assert expected == parse_filter_str_to_dict(in_)
