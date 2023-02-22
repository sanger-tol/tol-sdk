# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Tuple

from ..error import BadParameterStringException


def parse_filters(filter_string: str) -> Tuple[Dict, Dict]:
    if filter_string is None or filter_string == '':
        return None, None
    try:
        json_dict = json.loads(filter_string)
        return json_dict.get('exact'), json_dict.get('wildcard')
    except (json.JSONDecodeError, AttributeError):
        raise BadParameterStringException(
            'The filter parameter string is not a valid JSON object.'
        )
