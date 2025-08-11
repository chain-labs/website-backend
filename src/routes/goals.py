"""Goal and personalization routes."""

from email import message
import json
import re
import traceback
from fastapi import APIRouter, Depends
from datetime import datetime

import psycopg

from src.database import DATABASE_URL
from src.services.llm_services import get_history

from ..models.goal import (
    GoalRequest,
    GoalResponse, 
    ClarifyRequest,
    ClarifyResponse,
    PersonalisedData,
    PersonalisedResponse,
)
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..services.mock_data import mock_data_service
from ..utils.errors import raise_http_error
from ..services.goal_parser import parse_user_clarification, parse_user_goal
from ..services import cms

router = APIRouter(prefix="/api", tags=["Goals & Personalization"])


@router.post("/goal", response_model=GoalResponse)
async def submit_goal(
    request: GoalRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Parse raw user input into a structured goal and return personalized content.
    
    **Description:**
    This is the core endpoint that transforms a user's raw input into a structured 
    goal and generates personalized missions, case studies, and headlines. This 
    creates the foundation for the user's journey through the platform.
    
    **When to use:**
    - When a user first describes what they want to build/achieve
    - At the start of the goal-setting process
    - When user wants to start a new project or objective
    
    **Authentication Required:**
    Requires a valid Bearer token in the Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    Content-Type: application/json
    ```
    
    **Request Body:**
    ```json
    {
        "input": "I want to build an AI agent for restaurants"
    }
    ```
    
    **Input Guidelines:**
    - Be specific about what you want to build or achieve
    - Include context about your domain (e.g., "restaurants", "e-commerce")
    - Mention your primary objective or problem to solve
    - Examples: "Build a chatbot for customer service", "Create a recommendation system"
    
    **Response Example:**
    ```json
    {
        "assistantMessage": {
            "message": "I have received your goal. What is your primary objective?",
            "datetime": "2023-10-27T10:00:00Z"
        },
        "history": [
            {
                "role": "user",
                "message": "I want to build an AI agent for restaurants",
                "datetime": "2023-10-27T09:59:00Z"
            }
        ]
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('/api/goal', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            input: "I want to build an AI agent for restaurants"
        })
    });
    
    const goalData = await response.json();
    console.log('Generated missions:', goalData.missions.length);
    console.log('Headline:', goalData.headline);
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Empty or whitespace-only input
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found (invalid session ID in token)
    - **500 Internal Server Error**: Goal parsing or generation failed
    
    **What happens next:**
    1. Goal is stored in your session
    2. Missions become available for completion
    3. Use `/api/progress` to track mission completion
    4. Use `/api/mission/complete` to complete missions and earn points
    
    **Notes:**
    - This endpoint can only be called once per session
    - Subsequent calls will overwrite the previous goal
    - Use `/api/clarify` if you need to refine the goal
    - The generated missions are tailored to your specific input
    """

    # Validate input
    if not request.input or not request.input.strip():
        raise_http_error(400, "Input cannot be empty")

    user_message = {"role": "user", "message": request.input, "datetime": datetime.now().isoformat()}
    
    try:
        # Run async LLM parse
        goal_response = await parse_user_goal(request.input, session_id)
        
        # Merge session_id into final response
        structured_goal = GoalResponse(assistantMessage={"message": goal_response, "datetime": datetime.now().isoformat()}, history=[user_message, {"role": "assistant", "message": goal_response, "datetime": datetime.now().isoformat()}])
        return structured_goal

    except Exception as e:
        print("LLM Exception:", traceback.format_exc())
        raise_http_error(500, f"LLM parse error: {str(e)}")


@router.post("/clarify", response_model=ClarifyResponse)
async def clarify_goal(
    request: ClarifyRequest,
    session_id: str = Depends(get_current_session),
):
    """
    Refine and clarify an existing goal with additional context.
    
    **Description:**
    Allows users to provide additional clarification or refinement to their 
    previously submitted goal. This endpoint updates the goal description and 
    regenerates personalized content (missions, case studies, headlines) based 
    on the new context.
    
    **When to use:**
    - After submitting a goal via `/api/goal`
    - When you want to add more specific details to your goal
    - To pivot or refine the direction of your project
    - When the initial personalization needs adjustment
    
    **Prerequisites:**
    - Must have already submitted a goal via `/api/goal`
    - Session must contain an existing goal
    
    **Authentication Required:**
    Requires a valid Bearer token in the Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    Content-Type: application/json
    ```
    
    **Request Body:**
    ```json
    {
        "clarification": "Focus on customer satisfaction and reducing wait times"
    }
    ```
    
    **Clarification Examples:**
    - "Focus on customer satisfaction"
    - "Specifically for fine dining restaurants"
    - "Must integrate with existing POS systems"
    - "Primary goal is cost reduction"
    - "Target small restaurants with limited tech experience"
    
    **Response Example:**
    ```json
        {
            hero={"title": "AI Agent for Restaurants: Increase Table Turnover with Contextual Suggestions", "description": "Build an AI solution for restaurant operations: I want to build an AI agent for restaurants"},
            process=[{"name": "Define Success Metrics", "description": "Define success metrics for your AI agent for restaurants"}, {"name": "Sketch User Flow", "description": "Sketch user flow for your AI agent for restaurants"}],
            goal=session_data.goal,
            caseStudies=[{"id": "cs1", "title": "Booking Optimizer", "summary": "Reduced booking latency by 80% with AI-powered recommendations"}, {"id": "cs2", "title": "Menu Intelligence", "summary": "Increased revenue 30% through personalized menu suggestions"}],
            whyThisCaseStudiesWereSelected="",
            missions=[{"id": "defineMetrics", "title": "Define Success Metrics", "points": 15}, {"id": "sketchFlow", "title": "Sketch User Flow", "points": 15}],
            why=""
        }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('/api/clarify', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            clarification: "Focus on customer satisfaction and reducing wait times"
        })
    });
    
    const updatedGoal = await response.json();
    console.log('Updated goal:', updatedGoal.goal.description);
    console.log('New missions:', updatedGoal.missions.length);
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Empty or whitespace-only clarification
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found or no existing goal in session
    - **500 Internal Server Error**: Clarification processing failed
    
    **Important Notes:**
    - This updates your existing goal, not creates a new one
    - Previous mission progress is **reset** when clarifying
    - New missions are generated based on the updated goal
    - You can call this endpoint multiple times to further refine
    - The clarification is appended to the original goal description
    
    **Workflow Integration:**
    1. Submit initial goal via `/api/goal`
    2. Review generated missions and content
    3. Use `/api/clarify` to refine if needed
    4. Proceed with mission completion via `/api/mission/complete`
    """
    if not request.clarification or not request.clarification.strip():
        raise_http_error(400, "Clarification cannot be empty")
    
    try:

        clarification_response = await parse_user_clarification(request.clarification, session_id)
        # print(f"Clarification Response: {clarification_response}")
        match = re.search(r'```json\n(.*?)\n```', clarification_response, re.DOTALL) # Template Literal
        if match:
            json_string = match.group(1)
            # Step 2: Parse the JSON
            try:
                response_data = json.loads(json_string)
                print(f"JSON response:{response_data}")

                # Populate case studies from CMS by IDs if present
                case_ids = response_data.get("caseStudies", []) or []
                if isinstance(case_ids, list) and all(isinstance(cid, str) for cid in case_ids):
                    case_studies = await cms.get_case_studies_by_ids(case_ids)
                    response_data["caseStudies"] = case_studies
                else:
                    response_data["caseStudies"] = []

                # Ensure required flags/fields exist
                if "fallbackToGenericData" not in response_data:
                    response_data["fallbackToGenericData"] = False

                return ClarifyResponse(
                    **response_data
                )
            except json.JSONDecodeError as e:
                print("JSON decoding failed:", e)

    except Exception as e:
        print("LLM Exception:", traceback.format_exc())
        raise_http_error(500, f"LLM parse error: {str(e)}")

@router.get("/personalised", response_model=PersonalisedResponse)
async def get_personalized_content(session_id: str = Depends(get_current_session)):
    """
    Retrieve all personalized content for the current session.
    
    **Description:**
    Fetches all personalized content generated for your session, including 
    the structured goal, personalized missions, headline, and recommended 
    case studies. This is a read-only endpoint to retrieve existing 
    personalization data.
    
    **When to use:**
    - To refresh/reload personalized content in your UI
    - When reconnecting after a session break
    - To display goal and mission information on different pages
    - For caching and offline functionality
    - When you need to show current personalization status
    
    **Prerequisites:**
    - Must have submitted a goal via `/api/goal` first
    - Session must contain personalized content
    
    **Authentication Required:**
    Requires a valid Bearer token in the Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **No Request Body Required:**
    This is a GET request - no request body needed.
    
    **Response Example:**
    ```json
    {
        "status": "CLARIFIED",
        "messages": [...],
        "personalisation": {
            "hero": {"title": "...", "description": "..."},
            "process": [...],
            "goal": "...",
            "caseStudies": [...],
            "whyThisCaseStudiesWereSelected": "...",
            "missions": [...],
            "why": "...",
            "fallbackToGenericData": false
        }
    }
    ```
    
    **Error Cases:**
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found
    - **404 Not Found**: No personalized content found (haven't submitted goal yet)
    - **500 Internal Server Error**: Personalization retrieval failed
    """

    try:
        history = await get_history(session_id)
        messages_list = await history.aget_messages()

        # Determine status and extract personalisation data
        status = "INITIAL"
        messages_count = len(messages_list)
        personalised_data = None
        messages = []  # Initialize as empty list instead of None

        if messages_count >= 3:
            if messages_count >= 5:
                status = "CLARIFIED"
                # Extract the clarification response (5th message)
                clarification_message = messages_list[4]
                
                # Parse JSON from the clarification message
                match = re.search(r'```json\n(.*?)\n```', clarification_message.content, re.DOTALL)
                if match:
                    json_string = match.group(1)
                    try:
                        response_data = json.loads(json_string)
                        
                        # Populate case studies from CMS by IDs if present
                        case_ids = response_data.get("caseStudies", []) or []
                        if isinstance(case_ids, list) and all(isinstance(cid, str) for cid in case_ids):
                            case_studies = await cms.get_case_studies_by_ids(case_ids)
                            response_data["caseStudies"] = case_studies
                        else:
                            response_data["caseStudies"] = []

                        # Ensure required flags/fields exist
                        if "fallbackToGenericData" not in response_data:
                            response_data["fallbackToGenericData"] = False

                        # Create PersonalisedData object
                        personalised_data = PersonalisedData(**response_data)
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON decoding failed: {e}")
                        # Fallback to generic data if JSON parsing fails
                        personalised_data = PersonalisedData(
                            hero={"title": "Personalized Solution", "description": "Custom solution for your needs"},
                            process=[],
                            goal="Custom solution",
                            caseStudies=[],
                            whyThisCaseStudiesWereSelected="",
                            missions=[],
                            why="",
                            fallbackToGenericData=True
                        )
                else:
                    # No JSON found, create fallback data
                    personalised_data = PersonalisedData(
                        hero={"title": "Personalized Solution", "description": "Custom solution for your needs"},
                        process=[],
                        goal="Custom solution",
                        caseStudies=[],
                        whyThisCaseStudiesWereSelected="",
                        missions=[],
                        why="",
                        fallbackToGenericData=True
                    )
                
                # For CLARIFIED status, we return structured data, so messages can be empty
                messages = []
                    
            else:
                status = "GOAL_SET"
                # Remove system message and return user messages
                messages = messages_list[1:] if len(messages_list) > 1 else []
                # For GOAL_SET status, we don't have structured data yet
                personalised_data = PersonalisedData(
                    hero={"title": "Goal Set", "description": "Your goal has been submitted and is being processed"},
                    process=[],
                    goal="Goal submitted",
                    caseStudies=[],
                    whyThisCaseStudiesWereSelected="",
                    missions=[],
                    why="",
                    fallbackToGenericData=True
                )
        else:
            # Not enough messages for personalization
            raise_http_error(404, "No personalized content found. Please submit a goal first.")

        # Safety check: ensure personalised_data is never None
        if personalised_data is None:
            raise_http_error(500, "Failed to generate personalization data")

        return PersonalisedResponse(
            status=status,
            messages=messages,
            personalisation=personalised_data
        )

    except Exception as e:
        print(f"Error in get_personalized_content: {traceback.format_exc()}")
        raise_http_error(500, "Personalization engine error")