# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import prefect


def get_prefect_logger():
    return prefect.context.get("logger")
