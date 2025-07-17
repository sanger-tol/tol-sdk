# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging

from .data_source.services.util import delete_aliases


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """

    try:
        delete_aliases('', ignore=[404])
    except Exception as e:
        logging.error(e)
