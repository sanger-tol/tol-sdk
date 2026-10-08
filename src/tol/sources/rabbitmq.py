# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    core_data_object
)
from ..rabbitmq import (
    RabbitmqConfig,
    RabbitmqDataSource,
    create_rabbitmq_datasource
)


def rabbitmq(**kwargs) -> RabbitmqDataSource:
    rabbitmq_ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())

    core_data_object(rabbitmq_ds)
    return rabbitmq_ds
