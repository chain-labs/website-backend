import os
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
try:
    # Load environment variables from a .env file if python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # It's fine if python-dotenv is not installed
    pass

# Database connection string is resolved at runtime to ensure latest env is used
DEFAULT_DATABASE_URL = "postgresql://admin:admin123@localhost:5432/chainlabs"

def _resolve_database_url() -> str:
    """Resolve DATABASE_URL from environment with a sensible default.

    Note: This is evaluated at runtime (not import time) so changes to
    environment variables before init are respected.
    """
    value = os.getenv("DATABASE_URL")
    return value if value and value.strip() else DEFAULT_DATABASE_URL

def get_database_url() -> str:
    """Public accessor for the resolved database URL.

    Prefer this over importing a module-level constant so that environment
    changes made before initialization are respected.
    """
    return _resolve_database_url()


_pool: Optional[AsyncConnectionPool] = None

async def init_db() -> None:
    """Initialize the database connection pool."""
    global _pool
    if _pool is None:
        database_url = _resolve_database_url()
        _pool = AsyncConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=10,
            timeout=30,
            max_idle=300,
            num_workers=3,
            kwargs={"row_factory": dict_row},
            open=False
        )
        await _pool.open()
        await _pool.wait()

async def close_db() -> None:
    """Close all connections in the pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

@asynccontextmanager
async def get_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Get a database connection from the pool."""
    if _pool is None:
        await init_db()
    
    async with _pool.connection() as conn:
        try:
            yield conn
        except Exception:
            await conn.rollback()
            raise

@asynccontextmanager
async def transaction() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Get a connection with an active transaction."""
    async with get_connection() as conn:
        async with conn.transaction():
            yield conn




    
    


