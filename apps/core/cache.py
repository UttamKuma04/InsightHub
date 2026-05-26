import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def tenant_cache_key(tenant_id, namespace, detail="default"):
    version = get_tenant_cache_version(tenant_id)
    return f"tenant:{tenant_id}:v{version}:{namespace}:{detail}"


def get_cached(key):
    try:
        return cache.get(key)
    except Exception as exc:
        logger.warning("Cache get failed for %s: %s", key, exc)
        return None


def set_cached(key, value, timeout=None):
    try:
        cache.set(key, value, timeout or settings.CACHE_TTL_SECONDS)
    except Exception as exc:
        logger.warning("Cache set failed for %s: %s", key, exc)


def get_tenant_cache_version(tenant_id):
    version_key = _tenant_version_key(tenant_id)
    try:
        version = cache.get(version_key)
        if version is None:
            cache.set(version_key, 1, None)
            return 1
        return version
    except Exception as exc:
        logger.warning("Cache version read failed for tenant %s: %s", tenant_id, exc)
        return 0


def bump_tenant_cache_version(tenant_id):
    version_key = _tenant_version_key(tenant_id)
    try:
        try:
            cache.incr(version_key)
        except ValueError:
            cache.set(version_key, 2, None)
    except Exception as exc:
        logger.warning("Cache version bump failed for tenant %s: %s", tenant_id, exc)


def _tenant_version_key(tenant_id):
    return f"tenant:{tenant_id}:cache-version"
