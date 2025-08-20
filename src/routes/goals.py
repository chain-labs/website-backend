"""Goal and personalization routes."""

import json
import traceback
from fastapi import APIRouter, Depends
from datetime import datetime
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
from ..utils.errors import raise_http_error
from ..services.goal_parser import parse_user_clarification, parse_user_goal
from ..services import cms
from ..utils.json_utils import extract_json_from_fenced_block

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

    except Exception:
        print("LLM Exception:", traceback.format_exc())
        raise_http_error(500, "LLM parse error")


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

        # Parse the JSON response using utility
        try:
            response_data = extract_json_from_fenced_block(clarification_response)

            # Populate case studies from CMS
            case_ids = response_data.get("caseStudies", []) or ["case-1"]
            if isinstance(case_ids, list) and all(isinstance(cid, str) for cid in case_ids):
                case_studies = await cms.get_case_studies_by_ids(case_ids)
                response_data["caseStudies"] = case_studies
            else:
                response_data["caseStudies"] = []

            # Validate and fix mission data to ensure required fields
            if response_data.get("missions"):
                validated_missions = []
                for mission in response_data["missions"]:
                    validated_mission = {
                        "id": mission.get("id", "default_mission"),
                        "title": mission.get("title", mission.get("name", "Untitled Mission")),
                        "description": mission.get(
                            "description", 
                            mission.get("desc", "Mission description")
                        ),
                        "points": mission.get("points", mission.get("base_points", 10)),
                        "icon": mission.get(
                            "icon", 
                            mission.get("icons", "https://lucide.dev/icons/briefcase")
                        ),
                        "input": mission.get(
                            "input", 
                            {"required": False, "type": "N/A", "placeholder": "N/A" }
                        ),
                        "missionType": mission.get(
                            "missionType", 
                            mission.get("mission-type", "default")
                        ), 
                        "options": mission.get(
                            "options", {
                                "targetCaseStudyId": 'N/A'
                            }
                        ),
                        "status": mission.get("status", "pending")
                    }
                    validated_missions.append(validated_mission)
                response_data["missions"] = validated_missions


            # Ensure required fields exist
            if "fallbackToGenericData" not in response_data:
                response_data["fallbackToGenericData"] = False

            # Store session_progress immediately after LLM response
            try:
                case_ids_for_storage = [cs.get("id") for cs in response_data.get("caseStudies", []) if cs.get("id")]
                missions_full = []
                if response_data.get("missions"):
                    for m in response_data.get("missions", []):
                        if all(k in m for k in ("id", "title", "description", "points")):
                            missions_full.append({
                                "id": m["id"],
                                "title": m["title"],
                                "description": m["description"],
                                "points": m["points"],
                                "status": m.get("status", "pending"),
                                "icon": m["icon"],
                                "input": m["input"],
                                "missionType": m["missionType"],
                                "options": m["options"]
                            })
                await session_manager.upsert_session_progress(
                    session_id,
                    {
                        "session_id": session_id,
                        "goal": response_data.get("goal", ""),
                        "hero": response_data.get("hero", {}),
                        "process": response_data.get("process", []),
                        "missions": missions_full,
                        "case_studies": case_ids_for_storage,
                        "why_this_case_studies_were_selected": response_data.get("whyThisCaseStudiesWereSelected", ""),
                        "why": response_data.get("why", ""),
                        "points_total": 0,
                        "call_unlocked": False,
                    }
                )
                print("Session progress stored successfully in clarify route")
            except Exception as e:
                print(f"Warning: Failed to store session progress: {e}")

            return ClarifyResponse(**response_data)

        except json.JSONDecodeError as e:
            print("JSON decoding failed:", e)
            raise_http_error(500, "Invalid response format from AI service")
        except ValueError:
            raise_http_error(500, "Invalid response format from AI service")
    except Exception as e:
        print("LLM Exception:", traceback.format_exc())
        raise_http_error(500, f"LLM parse error: {str(e)}")

@router.get("/personalised", response_model=PersonalisedResponse)
async def get_personalized_content(session_id: str = Depends(get_current_session)):
    """
    Get all personalized content for the current session.

    **Description:**
    Returns the latest personalized content for the authenticated session, including the structured goal, missions, case studies, and related metadata. The endpoint reflects the most recent state, which may be either the initial goal or a clarified version if the user has refined their goal.

    **How it works:**
    - If the user has only submitted an initial goal, the response will include the initial personalized data.
    - If the user has clarified their goal (via `/api/clarify`), the response will reflect the clarified content.
    - The endpoint always returns the current state, including all assistant/user messages for the session.

    **When to use:**
    - To reload or refresh the personalized content in the UI
    - After a session break or reconnect
    - To display the current goal, missions, and recommendations
    - For offline/caching scenarios

    **Authentication:**
    - Requires a valid Bearer token in the `Authorization` header.

    **Request:**
    - Method: `GET`
    - URL: `/api/personalised`
    - No request body required.

    **Response:**
    - `status`: `"INITIAL"` if only the initial goal is present, `"CLARIFIED"` if the user has clarified their goal.
    - `messages`: List of all assistant/user messages for the session (may be empty if no messages yet).
    - `personalisation`: The current personalized data, including:
        - `hero`: `{ "title": str, "description": str }`
        - `process`: List of process steps (may be empty)
        - `goal`: The current goal description (str)
        - `caseStudies`: List of case study objects (may be empty if none found)
        - `whyThisCaseStudiesWereSelected`: Explanation for the case study selection (str, may be empty)
        - `missions`: List of mission objects (may be empty)
        - `why`: Reasoning for the personalized plan (str, may be empty)
        - `fallbackToGenericData`: Boolean indicating if generic data was used

    **Response Example:**
    ```json
    {
        "status": "CLARIFIED",
        "messages": [
            {
                "type": "user",
                "content": "I want to build an AI agent for restaurants",
                "timestamp": "2024-06-01T12:00:00Z"
            },
            {
                "type": "assistant",
                "content": "Great! Let's get started...",
                "timestamp": "2024-06-01T12:00:01Z"
            }
            // ... more messages
        ],
        "personalisation": {
            "hero": {"title": "AI Agent for Restaurants", "description": "A solution to optimize restaurant operations."},
            "process": [
                {"name": "Define Success Metrics", "description": "Identify KPIs for your restaurant AI agent."}
            ],
            "goal": "Build an AI agent for restaurants",
            "caseStudies": [
                {
                    "id": "case-1",
                    "title": "Smart Table Management",
                    "description": "...",
                    "shortDescription": "...",
                    "thumbnail": "..."
                }
            ],
            "whyThisCaseStudiesWereSelected": "These case studies are relevant to your goal.",
            "missions": [
                {"id": "defineMetrics", "title": "Define Success Metrics", "category": "planning", "points": 15, "status": "pending"}
            ],
            "why": "Personalized plan based on your input.",
            "fallbackToGenericData": false
        }
    }
    ```

    **Error Responses:**
    - `401 Unauthorized`: Missing or invalid Authorization header.
    - `404 Not Found`: Session not found or no personalized content available (e.g., if the user hasn't submitted a goal yet).
    - `500 Internal Server Error`: Unexpected error during personalization retrieval.
    """

    try:
        # 1) Try to serve from persisted SessionProgress first
        progress = await session_manager.get_session_progress(session_id)
        if progress is not None:
                # Build PersonalisedData from stored progress snapshot
                # Fetch case studies if we have stored IDs
            case_ids = progress.get("case_studies", []) or []
            case_studies = await cms.get_case_studies_by_ids(case_ids) if case_ids else []

                # Ensure missions are full objects; filter out any legacy status-only entries
            raw_missions = progress.get("missions", []) or []
            missions_full = []
            for m in raw_missions:
                try:
                    if all(k in m for k in ("id", "title", "description", "points")):
                        mission_entry = {
                            "id": m["id"],
                            "title": m["title"],
                            "description": m["description"],
                            "points": m["points"],
                            "status": m.get("status", "pending"),
                            "icon": m["icon"],
                            "input": m["input"],
                            "missionType": m["missionType"],
                            "options": m["options"]
                        }
                        # If artifact is present (e.g., from mission completion), propagate it
                        if isinstance(m.get("artifact"), dict):
                            mission_entry["artifact"] = m.get("artifact")
                        missions_full.append(mission_entry)
                except Exception:
                    continue

            personalised_data = PersonalisedData(
                hero=progress.get("hero", {"title": "", "description": ""}) or {"title": "", "description": ""},
                process=progress.get("process", []) or [],
                goal=progress.get("goal", "") or "",
                caseStudies=case_studies,
                whyThisCaseStudiesWereSelected=progress.get("why_this_case_studies_were_selected", "") or "",
                missions=missions_full,
                why=progress.get("why", "") or "",
                fallbackToGenericData=False,
                points_total=progress.get("points_total", 0) or 0,
                call_unlocked=progress.get("call_unlocked", False) or False
            )

            print("Sending Response from db storage")

            return PersonalisedResponse(
                status="CLARIFIED",
                messages=[],
                personalisation=personalised_data
            )

        # 2) Otherwise compute from history (first-time flow)
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
                
                # Parse JSON from the clarification message using utility
                try:
                    response_data = extract_json_from_fenced_block(clarification_message.content)

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

                    # Add missing required fields
                    if "points_total" not in response_data:
                        response_data["points_total"] = 0
                    if "call_unlocked" not in response_data:
                        response_data["call_unlocked"] = False

                    # Create PersonalisedData object
                    personalised_data = PersonalisedData(**response_data)
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"JSON extraction/decoding failed: {e}")
                    # Fallback to generic data if JSON parsing fails
                    personalised_data = PersonalisedData(
                        hero={"title": "Personalized Solution", "description": "Custom solution for your needs"},
                        process=[],
                        goal="Custom solution",
                        caseStudies=[],
                        whyThisCaseStudiesWereSelected="",
                        missions=[],
                        why="",
                        fallbackToGenericData=True,
                        points_total=0,
                        call_unlocked=False
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
                    points_total=0,
                    call_unlocked=False,
                    fallbackToGenericData=True
                )
        else:
            # INITIAL status: User has just started, return basic data
            status = "INITIAL"
            messages = messages_list if messages_list else []
            personalised_data = PersonalisedData(
                hero={"title": "Welcome to Chain Labs", "description": "Let's get started with your AI project"},
                process=[],
                goal="No goal submitted yet",
                caseStudies=[],
                whyThisCaseStudiesWereSelected="",
                missions=[],
                why="",
                points_total=0,
                call_unlocked=False,
                fallbackToGenericData=True
            )


        # Safety check: ensure personalised_data is never None
        if personalised_data is None:
            raise_http_error(500, "Failed to generate personalization data")

        return PersonalisedResponse(
            status=status,
            messages=messages,
            personalisation=personalised_data
        )

    except Exception:
        print(f"Error in get_personalized_content: {traceback.format_exc()}")
        raise_http_error(500, "Personalization engine error")