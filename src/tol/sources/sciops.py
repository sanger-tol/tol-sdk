# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from ..core import (
    core_data_object
)
from ..sciops import (
    SequencingDataSource
)


def sciops(**kwargs) -> SequencingDataSource:
    sciops = SequencingDataSource({
        'redpanda_url': os.getenv('REDPANDA_URL'),
        'redpanda_api_key': os.getenv('REDPANDA_API_KEY'),
        'rabbitmq_host': os.getenv('RABBITMQ_HOST'),
        'rabbitmq_port': os.getenv('RABBITMQ_PORT'),
        'rabbitmq_username': os.getenv('RABBITMQ_USERNAME'),
        'rabbitmq_password': os.getenv('RABBITMQ_PASSWORD'),
        'rabbitmq_vhost': os.getenv('RABBITMQ_VHOST'),
        'rabbitmq_exchange': os.getenv('RABBITMQ_EXCHANGE'),
        'rabbitmq_routing_key': os.getenv('RABBITMQ_ROUTING_KEY'),
        'rabbitmq_use_ssl': os.getenv('RABBITMQ_USE_SSL'),
        'rabbitmq_publish_retry_delay': os.getenv('RABBITMQ_PUBLISH_RETRY_DELAY'),
        'rabbitmq_publish_retries': os.getenv('RABBITMQ_PUBLISH_RETRIES'),
        'tol_feedback_queue': os.getenv('TOL_FEEDBACK_QUEUE')
    })
    core_data_object(sciops)
    return sciops
