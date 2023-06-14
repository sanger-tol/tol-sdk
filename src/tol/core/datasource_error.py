# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


class DataSourceError(Exception):
    """Raise to indicate that an error has occured with a DataSource."""

    def __init__(self, title: str = None, detail: str = None,
                 status_code: int = 500):
        self.title = title
        self.detail = detail
        self.status_code = status_code

    def __str__(self) -> str:
        return f'{self.title} - "{self.detail}"'
