#!/usr/bin/env python3
"""Initialize the database with required tables."""
import asyncio
import psycopg
from src.database import DATABASE_URL

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY,
    user_agent TEXT,
    ip_address TEXT,
    created_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ,
    is_active BOOLEAN
);
"""

CREATE_MESSAGE_STORE_TABLE = """
CREATE TABLE IF NOT EXISTS message_store (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL
);
"""

CREATE_SESSION_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS session_progress (
    session_id VARCHAR(255) PRIMARY KEY,
    goal TEXT NULL,
    hero JSONB NULL,
    process JSONB NULL,
    why_this_case_studies_were_selected TEXT NULL,
    why TEXT NULL,
    missions JSONB NULL,
    case_studies JSONB NULL,
    points_total INTEGER NULL,
    call_unlocked BOOLEAN NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""

CREATE_SESSION_TRANSFER_TABLE = """
CREATE TABLE IF NOT EXISTS session_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    old_session_id UUID NOT NULL REFERENCES sessions(id),
    new_session_id UUID NOT NULL REFERENCES sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

async def create_tables():
    """Create all tables defined in models."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        async with conn.cursor() as cur:
            await cur.execute(CREATE_SESSIONS_TABLE)
            await cur.execute(CREATE_MESSAGE_STORE_TABLE)
            await cur.execute(CREATE_SESSION_PROGRESS_TABLE)
            await cur.execute(CREATE_SESSION_TRANSFER_TABLE)
            await conn.commit()
            print("Database tables created or already exist.")
        

if __name__ == "__main__":
    asyncio.run(create_tables())
