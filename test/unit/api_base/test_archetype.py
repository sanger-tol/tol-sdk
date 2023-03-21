# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.archetype import Archetype


class ExampleArchetype(Archetype):
    pass


class TestArchetype:
    def test_bad(self):
        ExampleArchetype(None)
