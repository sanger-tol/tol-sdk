# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Dict, Tuple

from ..error import BadParameterStringException


def parse_filters(filter_string: str) -> Tuple[Dict, Dict, Dict]:
    if filter_string is None or filter_string == '':
        return None, None, None
    try:
        json_dict = json.loads(filter_string)

        return json_dict.get('exact'), json_dict.get('contains'), json_dict.get('range')
    except (json.JSONDecodeError, AttributeError):
        raise BadParameterStringException(
            'The filter parameter string is not a valid JSON object.'
        )

def parse_relationship_filter_key(key: str) -> Tuple:
    
    pass

def parse_range_filters(range_dict: dict) -> Tuple[str, str]:
    if len(range_dict) != 2 or 'from' not in range_dict or 'to' not in range_dict:
        raise BadParameterStringException(
            "The range filter JSON should only contain 2 entries: 'from' and 'to'."
        )
    try:
        return range_dict.get('from'), range_dict.get('to')
    except (AttributeError):
        raise BadParameterStringException(
            'The filter parameter string is not a valid JSON object.'
        )
