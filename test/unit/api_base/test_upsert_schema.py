# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from uuid import uuid4

from tol.api_base.datasource.schema import UpsertSchema


class TestUpsertSchema:
    """
    Tests UpsertSchema, specifically the UUID consistency
    validations
    """

    def test_to_one_undefined_uuid(self):
        """
        A to-one UUID reference that points nowhere.
        """
        uuid_sample = uuid4().hex
        uuid_specimen = uuid4().hex
        bad_uuid = uuid4().hex
        dump = {
            'data': [
                {
                    'type': 'sample',
                    '_uuid': uuid_sample,
                    'relationships': {
                        'one': {
                            'sampled_specimen': bad_uuid
                        }
                    }
                },
                {
                    'type': 'specimen',
                    '_uuid': uuid_specimen,
                    'attributes': {
                        'port': 1337
                    }
                }
            ]
        }
        UpsertSchema().validate(dump)
        

    def test_to_many_undefined_uuid(self):
        """
        A to-many UUID reference that points nowhere.
        """

    def test_both_undefined_several_uuids(self):
        """
        Several UUID references point nowhere, on both
        to-one and to-many relationships
        """

    def test_consistent_data(self):
        """
        Entirely consistent data
        """
