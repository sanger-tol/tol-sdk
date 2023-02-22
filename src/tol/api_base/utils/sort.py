# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Tuple


def parse_sort_by(sort_by_string: str) -> Tuple[str, bool]:
    if not sort_by_string:
        return None
    # if starts with minus sign, descending and strip the first character
    ascending = not sort_by_string.startswith('-')
    sort_by_string = sort_by_string if ascending else sort_by_string[1:]
    return (sort_by_string, ascending)
