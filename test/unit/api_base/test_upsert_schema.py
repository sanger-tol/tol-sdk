# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.datasource.schema import UpsertSchema


class TestUpsertSchema:
    """
    Tests UpsertSchema, specifically the UUID consistency
    validations
    """

    def test_to_one_undefined_uuid():
        """
        A to-one UUID reference that points nowhere.
        """

    def test_to_many_undefined_uuid():
        """
        A to-many UUID reference that points nowhere.
        """

    def test_both_undefined_several_uuids():
        """
        Several UUID references point nowhere, on both
        to-one and to-many relationships
        """

    def test_consistent_data():
        """
        Entirely consistent data
        """
