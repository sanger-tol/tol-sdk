# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re


def sanitise_value(value):
    value = re.sub(r'\\n', '\n', value)
    value = re.sub(r'\\t', '\t', value)
    value = value.strip()
    return value
