# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Any, Dict, Tuple

from ..error import BadParameterStringException


def __map_filter_name(filter_name: str, name_map: Dict[str, str]) -> str:
    return name_map.get(filter_name, filter_name)


def __load_filter_string(filter_string: str, name_map: Dict[str, str]) -> Dict[str, Any]:
    json_dict = json.loads(filter_string)
    if name_map is None:
        return json_dict
    return {
        __map_filter_name(filter_name): filter_value
        for filter_name, filter_value in json_dict.items()
    }


def parse_filters(
    filter_string: str,
    name_map: Dict[str, str] = None
) -> Tuple[Dict, Dict, Dict]:
    if filter_string is None or filter_string == '':
        return None, None, None
    try:
        json_dict = __load_filter_string(filter_string, name_map)
        return json_dict.get('exact'), json_dict.get('contains'), json_dict.get('range')
    except (json.JSONDecodeError, AttributeError):
        raise BadParameterStringException(
            'The filter parameter string is not a valid JSON object.'
        )


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
