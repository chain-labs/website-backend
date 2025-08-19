"""Chat service for the chat endpoint"""

import json
import traceback
from typing import List
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.models.chat import ChatResponse
from src.prompt.chat_prompt import FOLLOWUP_PROMPT, USER_MESSAGE_CONTEXT, WELCOME_PROMPT
from src.services.llm_services import get_history, llm
from src.services.session_manager import session_manager
from src.utils.errors import raise_http_error
from src.utils.json_utils import extract_json_from_fenced_block


class ChatService:
    """Handles chat interaction with the LLM"""

    def __init__(self):
        pass

    async def init_chat(self, *, session_id: str, page: str, section: str):
        """Initialize a chat session"""
        progress = await session_manager.get_session_progress(session_id)
        history = await get_history(session_id)
        messages = await history.aget_messages()

        if (len(messages) <= 1):
            raise_http_error(404, "Session does not have a goal")

        prompt_template = ChatPromptTemplate.from_messages(
            messages=[
                ("system", WELCOME_PROMPT),
            ])
        
        sys_prompt = prompt_template.format(
            page=page,
            section=section,
            progress_json=progress.get("missions", [])
        )

        messages.append(SystemMessage(content=sys_prompt))


        try:
            llm_response = await llm.ainvoke(messages)
            response = llm_response.content
            # await history.aadd_messages(messages=[SystemMessage(content=sys_prompt), AIMessage(content=response)])
            return response
        except Exception as e:
            print(f"LLM Parse Error: {e}", traceback.format_exc())



        


    async def ask(self, *, session_id: str, message: str, page: str, section: str):
        """Generate a response to an ask message"""
        progress = await session_manager.get_session_progress(session_id)
        history = await get_history(session_id)
        messages = await history.aget_messages()

        if (len(messages) <= 1):
            raise_http_error(404, "Session does not have a goal")

        if (len(messages) == 5):
            print("Adding follow up system prompt")
            messages.append(SystemMessage(content=FOLLOWUP_PROMPT))
            await history.aadd_messages(messages=[SystemMessage(content=FOLLOWUP_PROMPT)])
        
        context_template = ChatPromptTemplate.from_messages(
            messages=[("system", USER_MESSAGE_CONTEXT)]
        )

        context_prompt = context_template.format(
            page=page, 
            section=section, 
            progress_json=progress.get("missions", []), 
        )

        user_message_template = ChatPromptTemplate.from_messages(messages=[("user", """{user_input}""")])

        user_prompt = user_message_template.format(
            user_input=message
        )
        messages.append(context_prompt)
        messages.append(user_prompt)

        try:
            llm_response = await llm.ainvoke(messages)
            response = llm_response.content
            json_response = extract_json_from_fenced_block(response)

            await history.aadd_messages(
                messages=[
                    SystemMessage(content=context_prompt), 
                    HumanMessage(content=message), 
                    AIMessage(content=response)
                ]
            )


            messages_list = await history.aget_messages()

            message_history_unchanged = [m for m in messages_list[6:] if m.type != "system"]

            message_history: List[BaseMessage] = []



            for m in message_history_unchanged:
                if m.type == "ai":
                    c = m.content
                    reply = None

                    if isinstance(c, str):
                        content = extract_json_from_fenced_block(c)
                        reply = content.get("reply")
                
                    if reply is not None:
                        message_history.append(AIMessage(content=reply))
                if m.type == "human":
                    message_history.append(HumanMessage(content=m.content))

            return ChatResponse(
                reply=json_response.get("reply"),
                history=message_history[:-2],
                updatedProgress={
                    "pointsTotal": progress.get("points_total"),
                    "missions": progress.get("missions"),
                    "callUnlocked": progress.get("call_unlocked")
                },
                followUpMissions=json_response.get("followUpMissions"),
                suggestedRead=[],
                navigate=json_response.get("navigate")
            )
        except Exception as e:
            print(f"LLM Parse Error: {e}", traceback.format_exc())

        return ""



chat_service = ChatService()