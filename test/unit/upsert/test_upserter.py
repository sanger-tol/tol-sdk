# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.upsert import SingleTypeUpserter, Upserter
from tol.upsert.upserter import ObjectTypeUnspecifiedError


class TestUpserter:
    def test_upserter(self):
        """
        A regular Upserter instance does not throw an Exception at all.
        """
        class _TestRegularUpserter(Upserter):
            def upsert(self, *args, **kwargs) -> None:
                pass

        test_upserter = _TestRegularUpserter()

        # with object type
        test_upserter.upsert_session(object_type='test')
        # without object type
        test_upserter.upsert_session()

    def test_single_type_upserter(self):
        """
        A SingleTypeUpserter instance only throws an exception without a type
        """
        class _TestSingleTypeUpserter(SingleTypeUpserter):
            def upsert(self, *args, **kwargs) -> None:
                pass

        test_upserter = _TestSingleTypeUpserter()

        # with object type
        test_upserter.upsert_session(object_type='test')
        # without object type
        with pytest.raises(ObjectTypeUnspecifiedError):
            test_upserter.upsert_session()
