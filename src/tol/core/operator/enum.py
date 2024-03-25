# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from enum import Enum


class OperatorMethod(str, Enum):
    DETAIL = 'detail GET'
    PAGE = 'list GET'
    EXPORT = 'list POST'
    COUNT = 'count GET'
    DELETE = 'detail DELETE'
    UPDATE = 'update PATCH'
    UPSERT = 'upserts POST'
    AGGREGATE = 'aggregations POST'
    TO_ONE = 'recursive to-one relation GET'
    TO_MANY = 'to-many relations GET'
