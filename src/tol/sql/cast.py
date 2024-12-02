# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from sqlalchemy import cast
from sqlalchemy.types import BigInteger, Float, String, TypeDecorator


class CastToBigIntegerType(TypeDecorator):
    impl = String
    python_type = int

    def column_expression(self, col):
        return cast(col, BigInteger)

    def process_bind_param(self, value, dialect):
        return str(value)


class CastToFloatType(TypeDecorator):
    impl = String
    python_type = float

    def column_expression(self, col):
        return cast(col, Float)

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None
