# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import redis

from .config import get_redis_settings


def get_redis_client() -> redis.Redis:
    _redis_settings = get_redis_settings()
    return redis.Redis.from_url(
        _redis_settings.get_redis_url(),
        decode_responses=True,
        socket_timeout=1
    )
