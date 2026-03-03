# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    REDIS_HOST: str = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT: str = os.environ.get('REDIS_PORT', '6379')
    REDIS_DB: str = os.environ.get('REDIS_DB', '')
    REDIS_TTL_DEFAULT: int = int(os.environ.get('REDIS_TTL_DEFAULT', 3600))
    REDIS_TTL_NAV: int = int(os.environ.get('REDIS_TTL_NAV', 86400))

    def get_redis_url(self) -> str:
        return f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


@lru_cache()
def get_redis_settings() -> RedisSettings:
    return RedisSettings()
