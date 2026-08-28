# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class RabbitmqConfig:
    host: str
    port: int
    username: str
    password: str
    vhost: str
    exchange: str
    queue: str
    routing_key: str
    management_url: str
    use_ssl: bool = False
    write_batch_size: int = 100

    @classmethod
    def from_env(cls, prefix: str = 'RABBITMQ_') -> 'RabbitmqConfig':
        return cls(
            host=os.getenv(f'{prefix}HOST', '127.0.0.1'),
            port=int(os.getenv(f'{prefix}PORT', '5672')),
            username=os.getenv(f'{prefix}USERNAME', 'guest'),
            password=os.getenv(f'{prefix}PASSWORD', 'guest'),
            vhost=os.getenv(f'{prefix}VHOST', '/'),
            exchange=os.getenv(f'{prefix}EXCHANGE', 'notification'),
            queue=os.getenv(f'{prefix}QUEUE', 'notification'),
            routing_key=os.getenv(f'{prefix}ROUTING_KEY', 'notification'),
            management_url=os.getenv(f'{prefix}MANAGEMENT_URL', 'http://127.0.0.1:15672'),
            use_ssl=os.getenv(f'{prefix}USE_SSL', 'false').lower() == 'true',
            write_batch_size=int(os.getenv(f'{prefix}WRITE_BATCH_SIZE', 100)),
        )
