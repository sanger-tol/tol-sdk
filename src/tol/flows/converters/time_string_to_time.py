# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import re
from datetime import time

from tol.core import DataObject


class Converter:
    def convert(self, obj):
        raise NotImplementedError()


class TimeStringToTimeConverter(Converter):
    """
    Converts string fields representing time in HH:MM (24-hour) format to Python time objects.
    If the string is not in HH:MM, tries to append ':00' and parse as HH:MM:SS.
    """
    def __init__(self, field: str):
        self.field = field

    def convert(self, obj: DataObject) -> DataObject:
        value = obj.attributes.get(self.field)
        if isinstance(value, str):
            match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', value)
            if match:
                h, m = int(match.group(1)), int(match.group(2))
                s = int(match.group(3)) if match.group(3) else 0
                try:
                    obj.attributes[self.field] = time(h, m, s)
                except ValueError:
                    pass
        return obj
