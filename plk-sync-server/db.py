from contextlib import contextmanager

from psycopg_pool import ConnectionPool

from config import settings

_pool: ConnectionPool | None = None


def init_connection_pool() -> None:
    global _pool
    if _pool is not None:
        return

    _pool = ConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        timeout=settings.db_pool_timeout,
        open=False,
    )
    _pool.open(wait=True)


def close_connection_pool() -> None:
    global _pool
    if _pool is None:
        return

    _pool.close()
    _pool = None


@contextmanager
def get_connection():
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")

    with _pool.connection() as conn:
        yield conn
