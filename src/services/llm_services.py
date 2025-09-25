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
from src.database import get_database_url



# if "RAILWAY_DEPLOYMENT_ID" in os.environ:
llm = ChatOpenAI(model="gpt-5-nano", temperature=0.1, api_key=OPENAI_API_KEY)
# else:
    # llm = ChatOllama(model="llama3", temperature=0.7)

async def get_history(session_id: str) -> PostgresChatMessageHistory:
    # Convert SQLAlchemy URL to standard PostgreSQL connection string
    db_url = get_database_url().replace('postgresql+psycopg://', 'postgresql://')
    sync_connection = psycopg.connect(db_url)
    async_connection = await psycopg.AsyncConnection.connect(db_url)
    table_name = "message_store"
    PostgresChatMessageHistory.create_tables(sync_connection, table_name)
    history =  PostgresChatMessageHistory(table_name, session_id, async_connection=async_connection)
    return history
