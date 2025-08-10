import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin:admin123@localhost:5432/chainlabs")

engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

from src.models.db.db_models import *

async def get_db() -> AsyncSession:
    """Dependency that provides a database session"""

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    
    


