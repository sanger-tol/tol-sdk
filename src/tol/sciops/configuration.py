# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
import os

REDPANDA_URL = os.getenv('REDPANDA_URL', '127.0.0.1')
REDPANDA_API_KEY = os.getenv('REDPANDA_API_KEY', 'test')
REDPANDA_CREATE_LABWARE_SUBJECT = 'create-labware'

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', '127.0.0.1')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', '5671')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'psd')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'psd')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', 'tol')
RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', 'tol-team.tol')
RABBITMQ_ROUTING_KEY = os.getenv('RABBITMQ_ROUTING_KEY', 'crud.1')
RABBITMQ_USE_SSL = (os.getenv('RABBITMQ_USE_SSL', 'False').lower() == 'true')
RABBITMQ_PUBLISH_RETRY_DELAY = int(os.getenv('RABBITMQ_PUBLISH_RETRY_DELAY', 5))
RABBITMQ_PUBLISH_RETRIES = int(os.getenv('RABBITMQ_PUBLISH_RETRIES', 36))

TOL_FEEDBACK_QUEUE = os.getenv('TOL_FEEDBACK_QUEUE', 'tol.feedback')

CREATE_LABWARE_MESSAGE_SCHEMA_VERSION = os.getenv('CREATE_LABWARE_MESSAGE_SCHEMA_VERSION',
                                                  'latest')
UPDATE_LABWARE_MESSAGE_SCHEMA_VERSION = os.getenv('UPDATE_LABWARE_MESSAGE_SCHEMA_VERSION',
                                                  'latest')
