# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from enum import Enum


class OperatorMethod(str, Enum):
    DETAIL = 'detail GET'
    PAGE = 'list GET'
    EXPORT = 'list POST'
    COUNT = 'count GET'
    CURSOR = 'cursor GET'
    STATS = 'stats GET'
    GROUP_STATS = 'group-stat GET'
    DELETE = 'detail DELETE'
    INSERT = 'inserts POST'
    UPDATE = 'update PATCH'
    UPSERT = 'upserts POST'
    AGGREGATE = 'aggregations POST'
    TO_ONE = 'recursive to-one relation GET'
    TO_MANY = 'to-many relations GET'


class ReturnMode(str, Enum):
    """
    Describes what is returned by an instance
    of `DataSource` on write methods.
    """

    NONE = 'none'
    """
    All write methods return `None`.
    """

    PARTIAL = 'partial'
    """
    Write methods return instances of
    `DataObject`, but that may lack
    certain attributes (e.g. those
    that were not modified).
    """

    POPULATED = 'populated'
    """
    Write methods return instances of
    `DataObject` with all attributes
    populated.
    """


class RelationWriteMode(str, Enum):
    """
    Defines how a `Relational` instance
    expects relation objects during
    a write operation.
    """

    NOT_APPLICABLE = 'not applicable'
    """
    The `DataSource` does not implement
    `Relational`, or this is N/A in some
    other capacity.
    """

    FUSED = 'fused'
    """
    Relation objects should be specified
    as `to_one` without previously writing
    separately
    """

    SEPARATE = 'separate'
    """
    Relation objects must have been written
    separately before specifying in `to_one`
    """
