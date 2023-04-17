# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.api_client.api_data_object import ApiResponseDataObject


class TestApiResponseDataObject:
    def test_no_relationship_access_no_get(self):
        """
        Not accessing any relationships -> no get methods
        are called on the provided datasource
        """

    def test_to_one_relationship(self):
        """
        Accessing one to-one relationship -> one get method
        call
        """

    def test_repeated_to_one_relationship(self):
        """
        Repeated access of to-one relationship -> just
        one get method call (should be cached)
        """

    def test_several_different_to_one_relationships(self):
        """
        N access to N different to-one relationships -> N
        method calls, one for each
        """
