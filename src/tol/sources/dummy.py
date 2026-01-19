# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..dummy import (
    DummyDataSource,
    create_dummy_datasource
)


def dummy(**kwargs) -> DummyDataSource:
    dummy = create_dummy_datasource()
    core_data_object(dummy)
    return dummy
