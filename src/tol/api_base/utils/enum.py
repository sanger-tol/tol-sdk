# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


from enum import Enum


class _StrEnum(str, Enum):
    pass


class Methods(_StrEnum):
    """
    An enum containing all of the methods possible
    on a type.
    """

    GET = 'GET'
    BULK_GET = 'BULK_GET'
    CREATE = 'CREATE'
    BULK_CREATE = 'BULK_CREATE'
    UPDATE = 'UPDATE'
    BULK_UPDATE = 'BULK_UPDATE'
    DELETE = 'DELETE'
    BULK_DELETE = 'BULK_DELETE'
    UPSERT = 'UPSERT'
    BULK_UPSERT = 'UPSERT'


class Sources(_StrEnum):
    """
    An enum containing all possible
    sources of data
    """

    DATABASE = 'DATABASE'
    ELASTIC = 'ELASTIC'
    JIRA = 'JIRA'
