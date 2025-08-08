#!/usr/bin/env python3
"""Initialize the database with required tables."""
import asyncio
from src.database import engine, Base
from sqlalchemy import inspect

async def create_tables():
    """Create all tables defined in models."""
    async with engine.begin() as conn:
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = await conn.run_sync(
            lambda sync_conn: inspector.get_table_names()
        )
        
        if 'sessions' not in existing_tables:
            print("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully!")
        else:
            print("Database tables already exist.")

if __name__ == "__main__":
    asyncio.run(create_tables())
