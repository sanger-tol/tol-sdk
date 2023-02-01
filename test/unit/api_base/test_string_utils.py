# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.utils.string import escape_psql_like_string


def test_escape_psql_like_string_no_escape():
    invariant = 'this should not escape at all'
    assert escape_psql_like_string(invariant) == invariant


def test_escape_psql_like_string_percent_sign():
    in_ = 'I contain % a percent sign'
    expected = 'I contain \\% a percent sign'
    assert escape_psql_like_string(in_) == expected


def test_escape_psql_like_string_underscore():
    in_ = 'The truth is underscored by _'
    expected = 'The truth is underscored by \\_'
    assert escape_psql_like_string(in_) == expected


def test_escape_psql_like_string_both():
    in_ = 'There is _%_% __ ch%aos in this string!'
    expected = 'There is \\_\\%\\_\\% \\_\\_ ch\\%aos in this string!'
    assert escape_psql_like_string(in_) == expected
