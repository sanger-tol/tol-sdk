# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import time
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.flows.converters.time_string_to_time import TimeStringToTimeConverter


class TestTimeStringToTimeConverter:

    def test_hhmm_string(self):
        obj = create_autospec(DataObject)
        obj.attributes = {'TIME_OF_COLLECTION': '13:58'}
        converter = TimeStringToTimeConverter('TIME_OF_COLLECTION')
        result = converter.convert(obj)
        assert isinstance(result.attributes['TIME_OF_COLLECTION'], time)
        assert result.attributes['TIME_OF_COLLECTION'] == time(13, 58)

    def test_hhmmss_string(self):
        obj = create_autospec(DataObject)
        obj.attributes = {'TIME_OF_COLLECTION': '13:58:12'}
        converter = TimeStringToTimeConverter('TIME_OF_COLLECTION')
        result = converter.convert(obj)
        assert isinstance(result.attributes['TIME_OF_COLLECTION'], time)
        assert result.attributes['TIME_OF_COLLECTION'] == time(13, 58, 12)

    def test_invalid_string(self):
        obj = create_autospec(DataObject)
        obj.attributes = {'TIME_OF_COLLECTION': 'not_a_time'}
        converter = TimeStringToTimeConverter('TIME_OF_COLLECTION')
        result = converter.convert(obj)
        # Should remain unchanged
        assert result.attributes['TIME_OF_COLLECTION'] == 'not_a_time'

    def test_already_time(self):
        obj = create_autospec(DataObject)
        obj.attributes = {'TIME_OF_COLLECTION': time(9, 30)}
        converter = TimeStringToTimeConverter('TIME_OF_COLLECTION')
        result = converter.convert(obj)
        assert result.attributes['TIME_OF_COLLECTION'] == time(9, 30)
