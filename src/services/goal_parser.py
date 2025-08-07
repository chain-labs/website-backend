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
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from litellm import litellm
from langchain.schema import BaseMessage
from ..utils.errors import raise_http_error

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

llm = ChatOllama(model="llama3", temperature=0.7)

async def parse_user_goal(prompt: List[BaseMessage]) -> dict:
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
        logger.info("Starting LLM invocation...")
        logger.debug(f"Prompt content: {[msg.content for msg in prompt]}")
        
        # Make the LLM call
        raw_response = await llm.ainvoke(prompt)
        logger.info("Received response from LLM")
        
        # Log the raw response for debugging
        logger.debug(f"Raw response: {raw_response}")
        
        # Parse the response
        try:
            response_content = raw_response.content
            logger.debug(f"Response content: {response_content}")
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


