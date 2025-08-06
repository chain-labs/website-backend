"""Goal and personalization routes."""

from fastapi import APIRouter, Depends

from ..models.goal import (
    GoalRequest,
    GoalResponse, 
    ClarifyRequest,
    ClarifyResponse,
    PersonalizedResponse
)
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..services.mock_data import mock_data_service
from ..utils.errors import raise_http_error
from ..prompt.goal_prompt import generate_goal_prompt
from ..services.goal_parser import parse_user_goal

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
        "session_id": "abc123-def456",
        "goal": {
            "description": "Build an AI solution for restaurant operations: I want to build an AI agent for restaurants",
            "category": "hospitality",
            "priority": "high"
        },
        "missions": [
            {
                "id": "defineMetrics",
                "title": "Define Success Metrics",
                "points": 15,
                "status": "pending"
            }
        ],
        "headline": "AI Agent for Restaurants: Increase Table Turnover with Contextual Suggestions",
        "recommended_case_studies": [
            {
                "id": "cs1",
                "title": "Booking Optimizer",
                "summary": "Reduced booking latency by 80% with AI-powered recommendations"
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
    if not request.input or not request.input.strip():
        raise_http_error(400, "Input cannot be empty")
    
    # Get session data
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise_http_error(404, "Session not found")
    
    try:
        goal_prompt = generate_goal_prompt(request.input)
        goal = parse_user_goal(goal_prompt)
        structured_goal = GoalResponse(session_id=session_id, **goal.dict(exclude={"session_id"}))

        return structured_goal
        
    except Exception as e:
        raise_http_error(500, "LLM parse error")


@router.post("/clarify", response_model=ClarifyResponse)
async def clarify_goal(
    request: ClarifyRequest,
    session_id: str = Depends(get_current_session)
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
        "goal": {
            "description": "Build an AI solution for restaurant operations: I want to build an AI agent for restaurants - Clarified: Focus on customer satisfaction and reducing wait times",
            "category": "hospitality",
            "priority": "high"
        },
        "missions": [
            {
                "id": "identifyKPIs",
                "title": "Identify Key Performance Indicators",
                "points": 10,
                "status": "pending"
            }
        ],
        "headline": "Customer Experience AI: Personalize Dining with Advanced Analytics",
        "recommended_case_studies": [
            {
                "id": "cs4",
                "title": "Customer Insights",
                "summary": "Enhanced customer satisfaction by 40% using sentiment analysis"
            }
        ]
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
    
    # Get session data
    session_data = await session_manager.get_session(session_id)
    if not session_data or not session_data.goal:
        raise_http_error(404, "Session or goal not found")
    
    try:
        # Update goal based on clarification (mock implementation)
        updated_goal = session_data.goal.model_copy()
        updated_goal.description += f" - Clarified: {request.clarification}"
        
        # Regenerate personalized content
        missions = mock_data_service.get_random_missions(4)
        case_studies = mock_data_service.get_random_case_studies(3)
        headline = mock_data_service.get_random_headline()
        
        # Update session
        session_data.goal = updated_goal
        session_data.missions = missions
        session_data.recommended_case_studies = case_studies
        session_data.headline = headline
        
        return ClarifyResponse(
            goal=updated_goal,
            missions=missions,
            headline=headline,
            recommended_case_studies=case_studies
        )
    except Exception as e:
        raise_http_error(500, "Clarification parse failure")


@router.get("/personalised", response_model=PersonalizedResponse)
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
        "headline": "AI Agent for Restaurants: Increase Table Turnover with Contextual Suggestions",
        "goal": {
            "description": "Build an AI solution for restaurant operations: I want to build an AI agent for restaurants",
            "category": "hospitality",
            "priority": "high"
        },
        "missions": [
            {
                "id": "defineMetrics",
                "title": "Define Success Metrics",
                "points": 15,
                "status": "pending"
            },
            {
                "id": "sketchFlow",
                "title": "Sketch User Flow",
                "points": 15,
                "status": "pending"
            }
        ],
        "recommended_case_studies": [
            {
                "id": "cs1",
                "title": "Booking Optimizer",
                "summary": "Reduced booking latency by 80% with AI-powered recommendations"
            },
            {
                "id": "cs2",
                "title": "Menu Intelligence",
                "summary": "Increased revenue 30% through personalized menu suggestions"
            }
        ]
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('/api/personalised', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    if (response.ok) {
        const personalization = await response.json();
        
        // Update UI with personalized content
        document.getElementById('headline').textContent = personalization.headline;
        document.getElementById('goal-desc').textContent = personalization.goal.description;
        
        // Render missions
        const missionsList = personalization.missions.map(mission => 
            `<li>${mission.title} (${mission.points} points)</li>`
        ).join('');
        document.getElementById('missions').innerHTML = missionsList;
    }
    ```
    
    **Error Cases:**
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found
    - **404 Not Found**: No personalized content found (haven't submitted goal yet)
    - **500 Internal Server Error**: Personalization retrieval failed
    
    **Response Data Structure:**
    - **headline**: Catchy title for your project/goal
    - **goal**: Structured goal object with description, category, priority
    - **missions**: Array of available missions with IDs, titles, points, status
    - **recommended_case_studies**: Relevant case studies for inspiration
    
    **Integration Tips:**
    - Cache this data in your frontend for offline access
    - Use mission IDs for completion tracking
    - Display case studies as inspiration/examples
    - Show progress by comparing mission statuses with `/api/progress`
    
    **Workflow Context:**
    1. User submits goal via `/api/goal` → personalization created
    2. User can clarify via `/api/clarify` → personalization updated  
    3. Use this endpoint → retrieve current personalization
    4. Complete missions via `/api/mission/complete`
    5. Check progress via `/api/progress`
    """
    # Get session data
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise_http_error(404, "Session not found")
    
    if not session_data.goal:
        raise_http_error(404, "No personalized content found. Please submit a goal first.")
    
    try:
        return PersonalizedResponse(
            headline=session_data.headline,
            goal=session_data.goal,
            missions=session_data.missions,
            recommended_case_studies=session_data.recommended_case_studies
        )
    except Exception as e:
        raise_http_error(500, "Personalization engine error")