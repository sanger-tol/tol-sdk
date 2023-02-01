# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


def escape_psql_like_string(value: str):
    return (
        value.replace('\\', '\\\\')
             .replace('_', '\\_')
             .replace('%', '\\%')
    )
