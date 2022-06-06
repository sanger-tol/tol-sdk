# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

def _heading(heading_number, title):
    hashes = '#' * heading_number
    return f'{hashes} {title}'


def h1(title):
    return _heading(1, title)


def h2(title):
    return _heading(2, title)


def h3(title):
    return _heading(3, title)


def h4(title):
    return _heading(4, title)


def h5(title):
    return _heading(5, title)


def h6(title):
    return _heading(6, title)


def h7(title):
    return _heading(7, title)


def link(url, text):
    return f'[{text}]({url})'
