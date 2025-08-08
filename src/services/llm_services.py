# Use ChatOpenAI on Railway, otherwise use Ollama
import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage
from typing import List

import psycopg

from src.config import OPENAI_API_KEY
from src.database import DATABASE_URL



if "RAILWAY_DEPLOYMENT_ID" in os.environ:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=OPENAI_API_KEY)
else:
    llm = ChatOllama(model="llama3", temperature=0.7)

async def get_history(session_id: str) -> PostgresChatMessageHistory:
    # Convert SQLAlchemy URL to standard PostgreSQL connection string
    db_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
    async_connection = await psycopg.AsyncConnection.connect(db_url)
    return PostgresChatMessageHistory("message_store", session_id, async_connection=async_connection)

