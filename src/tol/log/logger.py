# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


class Logger:
    """
    Logs access requests using a given `DataSource` instance.

    To prevent infinite recursion, `Logger().log()` must not
    have been previously called on this `DataSource` instance.
    """
