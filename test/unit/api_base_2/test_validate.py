# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base2.load import LoadedDataObject
from tol.api_base2.validate import (
    DefaultUpsertValidator,
    UpsertValidationError
)


class TestDefaultUpsertValidator:
    def test_duplicate_uuid(self):
        """A UUID is duplicated across 2 dumped DataObjects"""
        data = [
            LoadedDataObject({
                'type': 'test',
                '_uuid': 'DUPLICATED',
                'id': 'match'
            }),
            LoadedDataObject({
                'type': 'test',
                '_uuid': 'DUPLICATED',
                'id': 'no_match'
            })
        ]
        with pytest.raises(UpsertValidationError) as err:
            DefaultUpsertValidator().validate(data)
        assert 'DUPLICATED' in err.value.detail

    def test_nonexistent_uuid_to_one(self):
        """A to-one relationship claims a non-existent UUID"""
        data = [
            LoadedDataObject({
                'type': 'test1',
                '_uuid': 'doesnt matter',
            }),
            LoadedDataObject({
                'type': 'test2',
                '_uuid': 'at all :)',
            }),
            LoadedDataObject({
                'type': 'test3',
                '_uuid': 'nice UUID',
                'relationships': {
                    'one': {
                        "doesn't": 'exist'
                    }
                }
            })
        ]
        with pytest.raises(UpsertValidationError) as err:
            DefaultUpsertValidator().validate(data)
        assert 'exist' in err.value.detail

    def test_nonexistent_uuid_to_many(self):
        """A to-many relationship claims a non-existent UUID"""
        data = [
            LoadedDataObject({
                'type': 'test1',
                '_uuid': 'doesnt matter',
            }),
            LoadedDataObject({
                'type': 'test2',
                '_uuid': 'at all :)',
            }),
            LoadedDataObject({
                'type': 'test3',
                '_uuid': 'nice UUID',
                'relationships': {
                    'many': {
                        "doesn't": ['exist']
                    }
                }
            })
        ]
        with pytest.raises(UpsertValidationError) as err:
            DefaultUpsertValidator().validate(data)
        assert 'exist' in err.value.detail

    def test_okay(self):
        """An OK UpsertDump passes validation"""
        data = [
            LoadedDataObject({
                'type': 'test1',
                '_uuid': 'doesnt matter',
            }),
            LoadedDataObject({
                'type': 'test2',
                '_uuid': 'completely :)',
            }),
            LoadedDataObject({
                'type': 'test3',
                '_uuid': 'nice UUID',
                'relationships': {
                    'one': {
                        'guesstimate': 'doesnt matter'
                    },
                    'many': {
                        'this will work': ['completely :)']
                    }
                }
            })
        ]
        DefaultUpsertValidator().validate(data)
