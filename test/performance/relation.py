# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from uuid import uuid4

from performance.ds import api_sql

from tol.time import benchmark


@benchmark(
    repetitions=100,
    warn=20,
    fail=30
)
def get_to_one_relation() -> None:
    """loosely checks for rogue fetches"""

    rel = api_sql.data_object_factory(
        'related',
        uuid4().hex,
        attributes={
            'str_column': 'lesser'
        }
    )

    root_id = uuid4().hex
    root = api_sql.data_object_factory(
        'root',
        root_id,
        to_one={
            'related_object': rel
        }
    )

    api_sql.insert(
        'root',
        [root]
    )

    root_fetched = api_sql.get_one(
        'root',
        root_id
    )

    # this will be slow if there is another fetch
    assert root_fetched.related_object.str_column == 'lesser'


if __name__ == '__main__':
    time_get_to_one_relation()
