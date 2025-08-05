"""Session management routes."""

from fastapi import APIRouter, Depends

from ..models.session import SessionResponse as SessionHydrationResponse
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..utils.errors import raise_http_error

router = APIRouter(prefix="/api", tags=["Session Management"])


@router.get("/session", response_model=SessionHydrationResponse)
async def get_full_session(session_id: str = Depends(get_current_session)):
    """
    Retrieve complete session state for frontend hydration.
    
    **Description:**
    Fetches the complete session state in a single request, including goal 
    information, mission statuses with progress, total points earned, and 
    unlock status. This is the primary endpoint for hydrating your frontend 
    application state when users return to the platform.
    
    **When to use:**
    - When user refreshes the page or returns to the app
    - For initial app load after authentication
    - To restore complete application state from server
    - When you need both goal data AND progress data together
    - For building a comprehensive dashboard view
    
    **Prerequisites:**
    - Must have submitted a goal via `/api/goal` first
    - Session must contain goal and mission data
    
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
        "goal": {
            "description": "Build an AI solution for restaurant operations: I want to build an AI agent for restaurants",
            "category": "hospitality",
            "priority": "high"
        },
        "missions": [
            {
                "id": "defineMetrics",
                "status": "completed",
                "points": 15
            },
            {
                "id": "sketchFlow",
                "status": "completed", 
                "points": 15
            },
            {
                "id": "buildPrototype",
                "status": "pending",
                "points": 25
            },
            {
                "id": "runDemo",
                "status": "pending",
                "points": 20
            }
        ],
        "points_total": 30,
        "call_unlocked": true
    }
    ```
    
    **Usage Example (Frontend Hydration):**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const hydrateApp = async () => {
        try {
            const response = await fetch('/api/session', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
            
            if (response.ok) {
                const sessionState = await response.json();
                
                // Hydrate goal information
                setGoal(sessionState.goal);
                
                // Hydrate mission progress
                setMissions(sessionState.missions);
                setTotalPoints(sessionState.points_total);
                
                // Update unlock status
                setCallUnlocked(sessionState.call_unlocked);
                
                // Calculate progress percentage
                const completedMissions = sessionState.missions.filter(m => m.status === 'completed');
                const progressPercent = (completedMissions.length / sessionState.missions.length) * 100;
                setProgress(progressPercent);
                
                console.log('App hydrated successfully');
            } else {
                // Handle cases where user hasn't submitted goal yet
                redirectToGoalSubmission();
            }
        } catch (error) {
            console.error('Failed to hydrate app:', error);
            handleHydrationError(error);
        }
    };
    
    // Call on app initialization
    useEffect(() => {
        if (accessToken) {
            hydrateApp();
        }
    }, [accessToken]);
    ```
    
    **React State Management Example:**
    ```javascript
    const [appState, setAppState] = useState({
        goal: null,
        missions: [],
        points_total: 0,
        call_unlocked: false,
        isHydrated: false
    });
    
    const hydrateFromSession = async () => {
        try {
            const response = await fetch('/api/session', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            const sessionData = await response.json();
            
            setAppState({
                ...sessionData,
                isHydrated: true
            });
        } catch (error) {
            setAppState(prev => ({ ...prev, isHydrated: true }));
            // Handle error appropriately
        }
    };
    ```
    
    **Error Cases:**
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found (invalid session ID in token)
    - **404 Not Found**: No session content (user hasn't submitted goal yet)
    - **500 Internal Server Error**: Session data retrieval failed
    
    **Response Fields:**
    - **goal**: Complete goal object with description, category, priority
    - **missions**: Array of missions with current status and point values
    - **points_total**: Total points earned across all completed missions
    - **call_unlocked**: Boolean indicating if premium features are available
    
    **Comparison with Other Endpoints:**
    - **vs `/api/personalised`**: This includes progress data (mission statuses, points)
    - **vs `/api/progress`**: This includes goal data and case studies
    - **vs `/api/unlock-status`**: This includes complete session context
    
    **Performance Considerations:**
    - This endpoint returns more data than specialized endpoints
    - Use sparingly - primarily for initial app hydration
    - Consider caching the result and using specific endpoints for updates
    - Avoid calling on every page navigation
    
    **Integration Patterns:**
    ```javascript
    // Good: Use for initial hydration
    await hydrateFromSession();
    
    // Good: Then use specific endpoints for updates
    await completeMission(missionId);  // Updates mission status
    await checkProgress();             // Gets updated progress
    
    // Avoid: Calling session endpoint repeatedly
    // Instead cache session data and use specific endpoints
    ```
    
    **Error Handling Best Practices:**
    - **404 "No session content"**: Redirect to goal submission
    - **401 Unauthorized**: Refresh tokens or redirect to login
    - **500 errors**: Show error message and retry mechanism
    - **Network errors**: Show offline state and retry when online
    
    **State Management Integration:**
    - Perfect for Redux/Zustand store hydration
    - Use as single source of truth for initial app state
    - Update individual pieces with specific endpoint responses
    - Consider this the "bootstrap" data for your application
    """
    # Get session data
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise_http_error(404, "Session not found")
    
    if not session_data.goal:
        raise_http_error(404, "No session content found. Please submit a goal first.")
    
    try:
        mission_statuses = session_data.get_mission_statuses()
        
        return SessionHydrationResponse(
            goal=session_data.goal,
            missions=mission_statuses,
            points_total=session_data.points_total,
            call_unlocked=session_data.is_call_unlocked()
        )
    except Exception as e:
        raise_http_error(500, "Session retrieval error")