from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings


redis_pool = ConnectionPool.from_url(
    settings.redis_url if hasattr(settings, "redis_url") else "redis://localhost:6379/0",
    max_connections=20,          # Giới hạn số connection tối đa trong pool
    decode_responses=True,       # Tự động decode bytes -> str
    socket_timeout=5.0,          # Timeout khi đọc/ghi
    socket_connect_timeout=5.0,  # Timeout khi bắt tay kết nối
    retry_on_timeout=True,       # Tự động retry khi timeout socket
)


def get_redis_client() -> Redis:
    return Redis(connection_pool=redis_pool)

async def close_redis_pool():
    await redis_pool.disconnect()
