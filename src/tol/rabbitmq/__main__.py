# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

"""
Example consumer: `RABBITMQ_APP_NAME=<app> python -m tol.rabbitmq`.

Apps copy this into their own entrypoint with their own handlers.
Run under the restarting supervisor - the process exits on connection loss.
"""

import logging

from .config import RabbitmqConfig
from .factory import create_consumer
from .handlers import notification_handler
from .schema import NotificationChannel

LOGGER = logging.getLogger(__name__)


def main() -> None:
    """Consume notifications and log each delivery."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    # Log only dispatchers until real ones exist
    # Create dispatchers: <key>: <fn>
    dispatchers = {
        NotificationChannel.EMAIL: lambda d: LOGGER.info('EMAIL: %s', d),
        NotificationChannel.SLACK: lambda d: LOGGER.info('SLACK: %s', d)
    }

    # Create the consumer and pass in config & handlers
    consumer = create_consumer(
        RabbitmqConfig.from_env(),
        handlers={'notification': notification_handler(dispatchers)}
    )
    consumer.start()


if __name__ == '__main__':
    main()
