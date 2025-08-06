from langchain_litellm import ChatLiteLLM
from litellm import litellm
from ..models.goal import GoalResponse
from langchain.schema import BaseMessage
from typing import List

llm = ChatLiteLLM(model="openai/llama3", api_base="http://localhost:4000", api_key="not-needed")

def parse_user_goal(prompt: List[BaseMessage]) -> dict:
    structured_llm = llm.with_structured_output(GoalResponse)
    try:
        response = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Error parsing user goal: {e}")
        raise_http_error(500, "Error parsing user goal, please try rephrasing")

    return response


