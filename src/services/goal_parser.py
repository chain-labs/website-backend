import os
import logging
from typing import List, Dict, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable vector store
os.environ["LITELLM_DISABLE_VECTOR_STORE"] = "true"
os.environ['LITELLM_LOG'] = 'DEBUG'

# from langchain_litellm import ChatLiteLLM
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from litellm import litellm
from langchain.schema import BaseMessage
from ..utils.errors import raise_http_error
from src.services.llm_services import get_history, llm
from ..prompt.goal_prompt import goalPromptTemplate, template_prompt

async def parse_user_goal(user_prompt: str, session_id: str) -> dict:
    """
    Parse user goal using LLM and return structured response.
    
    Args:
        prompt: List of BaseMessage objects containing the prompt
        
    Returns:
        dict: Parsed goal response
        
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        history = await get_history(session_id)
        messages = await history.aget_messages()

        if (len(messages) != 0):
            raise_http_error(400, "Session already has a goal")

        logger.info("Starting LLM invocation...")
        
        logger.debug(f"Prompt content: {user_prompt}")


        base_chain = goalPromptTemplate | llm

        # Make the LLM call
        raw_response = await base_chain.ainvoke({"user_goal_input": user_prompt})
        logger.info("Received response from LLM")

        # Log the raw response for debugging
        logger.debug(f"Raw response: {raw_response}")

        # Parse the response
        try:
            response_content = raw_response.content
            await history.aadd_messages(messages=[SystemMessage(content=template_prompt), HumanMessage(content=user_prompt), AIMessage(content=response_content)])
            logger.debug(f"Response content: {response_content}")
            messages = await history.aget_messages()
            return response_content
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response: {je}")
            raise_http_error(500, "Invalid response format from AI service")

    except Exception as e:
        logger.error(f"Error in parse_user_goal: {str(e)}", exc_info=True)
        raise_http_error(
            500, 
            f"Error processing your request: {str(e)}. Please try again later."
        )


async def parse_user_clarification(user_prompt: str, session_id: str) -> dict:
    history = await get_history(session_id)

    messages = await history.aget_messages()

    # print(f"Messages: {messages}")

    if len(messages) == 0:
        raise_http_error(404, "No chat history found for session")
    if len(messages) > 3:
        raise_http_error(400, "Session already has a clarification")

    try:
        messages.append(HumanMessage(content=user_prompt))

        response = await llm.ainvoke(messages)

        await history.aadd_messages([HumanMessage(content=user_prompt), AIMessage(content=response.content)])

        return response.content

    except Exception as e:
        raise_http_error(500, f"Failed to clarify goal: {str(e)}")