# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import hashlib
import json
import logging

import redis as redis_lib

from tol.core.redis.config import get_redis_settings
from tol.core.redis.redis_client import get_redis_client

settings = get_redis_settings()
logger = logging.getLogger(__name__)


class CacheService:
    """A service for caching data using Redis, with support for TTL and tag-based invalidation."""

    def __init__(self):
        self._redis = None

    @property
    def redis(self):
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def _hash(self, data: dict) -> str:
        """Generate a hash for the given data to use as a cache key."""
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def build_cache_key(self, *parts: str) -> str:
        """Build a cache key from the given parts."""
        return ':'.join(parts)

    def get(self, key: str) -> dict | None:
        """Retrieve a value from the cache by its key."""
        try:
            value = self.redis.get(key)
        except redis_lib.RedisError as e:
            logger.warning(f'Redis unavailable during get for key {key}: {e}')
            return None

        if value is not None:
            logger.debug(f'Cache hit for key: {key}')
        else:
            logger.debug(f'Cache miss for key: {key}')

        return json.loads(value) if value else None

    def set(self, key: str, value: dict,  # noqa: A003
            ttl: int = settings.REDIS_TTL_DEFAULT, tags: list[str] | None = None) -> None:
        """Store a value in the cache with an optional TTL (time-to-live) and tags."""
        try:
            self.redis.setex(key, ttl, json.dumps(value))
            for tag in tags or []:
                self.redis.sadd(f'tag:{tag}', key)
                self.redis.expire(f'tag:{tag}', ttl)
        except redis_lib.RedisError as e:
            logger.warning(f'Redis unavailable during set for key {key}: {e}')

    def invalidate_by_tag(self, tag: str) -> None:
        """Invalidate all cache entries associated with a specific tag."""
        try:
            keys = self.redis.smembers(f'tag:{tag}')
            if keys:
                self.redis.delete(*keys)
                self.redis.delete(f'tag:{tag}')
        except redis_lib.RedisError as e:
            logger.warning(f'Redis unavailable during invalidate_by_tag for tag {tag}: {e}')

    def invalidate_by_key(self, key: str) -> None:
        """Invalidate a cache entry by its key."""
        try:
            self.redis.delete(key)
        except redis_lib.RedisError as e:
            logger.warning(f'Redis unavailable during invalidate_by_key for key {key}: {e}')


cache = CacheService()
