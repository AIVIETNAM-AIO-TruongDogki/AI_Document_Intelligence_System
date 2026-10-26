import logging
from arq.connections import ArqRedis, RedisSettings, create_pool
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Connection pool dùng cho direct key-value operations / cache / locks
redis_pool = ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,          # Giới hạn số connection tối đa trong pool để tránh cạn kiệt socket file descriptors
    decode_responses=True,       # Tự động decode bytes -> str (UTF-8)
    socket_timeout=5.0,          # Timeout khi đọc/ghi dữ liệu
    socket_connect_timeout=5.0,  # Timeout khi bắt tay kết nối TCP
    retry_on_timeout=True,       # Tự động retry khi xảy ra timeout socket ở tầng transport
    health_check_interval=30,    # Ping định kỳ giữ kết nối không bị firewall/NAT ngắt âm thầm
)


def get_redis_client() -> Redis:
    """Khởi tạo redis client dùng chung pool."""
    return Redis(connection_pool=redis_pool)


async def close_redis_pool() -> None:
    """Giải phóng tài nguyên kết nối Redis khi ứng dụng dừng."""
    await redis_pool.disconnect()


# --- ARQ (Async Redis Queue) Connection Management ---

def get_arq_redis_settings() -> RedisSettings:
    """Tạo cấu hình kết nối Redis dành riêng cho ARQ Worker."""
    return RedisSettings.from_dsn(settings.redis_url)


_arq_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    """Lấy hoặc khởi tạo ArqRedis pool (Singleton instance dùng cho producer)."""
    global _arq_pool
    if _arq_pool is None:
        _arq_pool = await create_pool(get_arq_redis_settings())
    return _arq_pool


async def close_arq_pool() -> None:
    """Đóng pool ARQ khi tắt server."""
    global _arq_pool
    if _arq_pool is not None:
        await _arq_pool.close()
        _arq_pool = None


async def ping_redis() -> bool:
    """Kiểm tra độ sẵn sàng của Redis (Liveness / Readiness Probe)."""
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        return False
