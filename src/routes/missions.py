"""Mission and progress routes."""

import traceback
from fastapi import APIRouter, Depends

from ..models.mission import (
    ProgressResponse,
    CompleteMissionRequest,
    CompleteMissionResponse,
    UnlockStatusResponse
)
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..services.mock_data import mock_data_service
from ..utils.errors import raise_http_error

router = APIRouter(prefix="/api", tags=["Missions & Progress"])


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(session_id: str = Depends(get_current_session)):
    """
    Get current mission progress, points, and unlock status.
    
    **Description:**
    Retrieves the complete progress overview for your session, including 
    individual mission statuses (pending/completed), total points earned, 
    and whether special features like the free call are unlocked.
    
    **When to use:**
    - To display a progress dashboard or overview
    - After completing missions to see updated totals
    - To check current unlock status
    - For progress tracking and gamification UI
    - When resuming a session to see where you left off
    
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
        "points_total": 45,
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
        "call_unlocked": true
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('/api/progress', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    const progress = await response.json();
    
    // Update progress UI
    document.getElementById('total-points').textContent = progress.points_total;
    document.getElementById('unlock-status').textContent = 
        progress.call_unlocked ? 'Call Unlocked!' : 'Complete more missions to unlock call';
    
    // Show mission progress
    const completedCount = progress.missions.filter(m => m.status === 'completed').length;
    const totalCount = progress.missions.length;
    document.getElementById('progress-bar').style.width = 
        `${(completedCount / totalCount) * 100}%`;
    ```
    
    **Error Cases:**
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found (invalid session ID in token)
    - **500 Internal Server Error**: Progress calculation failed
    
    **Response Fields:**
    - **points_total**: Total points earned across all completed missions
    - **missions**: Array of all missions with current status and point values
    - **call_unlocked**: Boolean indicating if free call feature is available
    
    **Mission Status Values:**
    - **"pending"**: Mission is available but not yet completed
    - **"completed"**: Mission has been finished and points awarded
    
    **Unlock Logic:**
    - Call feature unlocks after completing 2 or more missions
    - Points accumulate with each completed mission
    - Unlock status persists throughout the session
    
    **Integration Notes:**
    - Use this endpoint to build progress dashboards
    - Combine with `/api/mission/complete` for mission completion flow
    - Check unlock status before showing premium features
    - Cache progress data and refresh after mission completions
    """
    try:
        # First try to get progress from database
        progress = await session_manager.get_session_progress(session_id)
        
        if progress and progress.get("missions"):
            # Convert stored missions to MissionStatus format
            missions = progress.get("missions", [])
            mission_statuses = []
            
            for mission in missions:
                mission_statuses.append({
                    "id": mission.get("id"),
                    "status": mission.get("status", "pending"),
                    "points": mission.get("points", 0)
                })
            
            return ProgressResponse(
                points_total=progress.get("points_total", 0),
                missions=mission_statuses,
                call_unlocked=progress.get("call_unlocked", False)
            )
        
        # Fallback to in-memory session data
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise_http_error(404, "Session not found")
        
        mission_statuses = session_data.get_mission_statuses()
        
        return ProgressResponse(
            points_total=session_data.points_total,
            missions=mission_statuses,
            call_unlocked=session_data.is_call_unlocked()
        )
        
    except Exception as e:
        raise_http_error(500, "Scoring engine error")


@router.post("/mission/complete", response_model=CompleteMissionResponse)
async def complete_mission(
    request: CompleteMissionRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Complete a mission by submitting your solution and earn points.
    
    **Description:**
    Submit your completed work for a specific mission to earn points and 
    unlock progress. This endpoint validates your submission, awards points, 
    updates your progress, and may unlock special features like the free call.
    
    **When to use:**
    - When you've finished working on a mission
    - To submit your solution/artifact for a specific mission
    - To earn points and progress through the system
    - After completing tasks like "Define Success Metrics" or "Sketch User Flow"
    
    **Prerequisites:**
    - Must have submitted a goal via `/api/goal` first
    - Mission must exist in your personalized mission list
    - Mission must not already be completed
    
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
        "mission_id": "defineMetrics",
        "artifact": {
            "answer": "Key metrics: Customer satisfaction (CSAT), table turnover rate, average order value, wait time reduction percentage, staff efficiency score"
        }
    }
    ```
    
    **Mission ID Examples:**
    - `"defineMetrics"` - Define Success Metrics
    - `"sketchFlow"` - Sketch User Flow  
    - `"buildPrototype"` - Build Initial Prototype
    - `"runDemo"` - Run the AI demo
    - `"identifyKPIs"` - Identify Key Performance Indicators
    - `"testUsability"` - Test User Experience
    
    **Artifact Guidelines:**
    - **Be specific**: Provide detailed, actionable content
    - **Show thinking**: Explain your reasoning and approach
    - **Include examples**: Give concrete examples where relevant
    - **Quality matters**: Thoughtful responses may influence future personalization
    
    **Response Example:**
    ```json
    {
        "points_awarded": 15,
        "points_total": 30,
        "call_unlocked": false,
        "next_mission": {
            "id": "sketchFlow",
            "title": "Sketch User Flow", 
            "points": 15,
            "status": "pending"
        }
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const missionData = {
        mission_id: "defineMetrics",
        artifact: {
            answer: "Key metrics: Customer satisfaction (CSAT), table turnover rate, average order value, wait time reduction percentage, staff efficiency score"
        }
    };
    
    const response = await fetch('/api/mission/complete', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(missionData)
    });
    
    if (response.ok) {
        const result = await response.json();
        
        // Update UI with progress
        console.log(`Earned ${result.points_awarded} points!`);
        console.log(`Total points: ${result.points_total}`);
        
        if (result.call_unlocked) {
            document.getElementById('call-button').disabled = false;
            showNotification('🎉 Free call unlocked!');
        }
        
        // Show next mission if available
        if (result.next_mission) {
            console.log(`Next: ${result.next_mission.title}`);
        }
    }
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Missing mission_id or empty artifact answer
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **403 Forbidden**: Mission already completed (can't complete twice)
    - **404 Not Found**: Session not found or mission doesn't exist
    - **500 Internal Server Error**: Mission completion processing failed
    
    **Response Fields:**
    - **points_awarded**: Points earned for this specific mission
    - **points_total**: Updated total points across all missions  
    - **call_unlocked**: Whether free call feature is now available
    - **next_mission**: Suggested next mission to work on (if available)
    
    **Progression Logic:**
    - Each mission can only be completed once
    - Points are awarded immediately upon completion
    - Call unlocks after completing 2+ missions
    - Next mission suggestion helps guide your journey
    
    **Integration Tips:**
    - Always check response for unlock status changes
    - Use next_mission to guide user to next step
    - Update local progress state after successful completion
    - Consider showing celebration UI for point awards
    - Refresh `/api/progress` to get complete updated status
    """
    print(f"Completing mission: {request.mission_id} for Session: {session_id}")
    if not request.mission_id:
        raise_http_error(400, "Mission ID is required")
    
    if not request.artifact or not request.artifact.answer:
        raise_http_error(400, "Artifact answer is required")
    
    # Get session data - try to load from DB if not in memory
    print(f"DEBUG: Loading session data for session_id: {session_id}")
    session_data = await session_manager.get_or_create_session_from_db(session_id)
    print(f"DEBUG: Session data loaded: {session_data is not None}")
    
    if not session_data:
        print(f"DEBUG: No session data found for session_id: {session_id}")
        raise_http_error(404, "Session not found. Please submit a goal first via /api/goal")
    
    # Check if missions exist
    print(f"DEBUG: Missions count: {len(session_data.missions) if session_data.missions else 0}")
    if not session_data.missions:
        print(f"DEBUG: No missions found in session data")
        raise_http_error(404, "No missions found. Please submit a goal first via /api/goal")
    
    # Check if mission exists
    print(f"DEBUG: Looking for mission_id: {request.mission_id}")
    print(f"DEBUG: Available mission IDs: {[m.id for m in session_data.missions]}")
    mission = next((m for m in session_data.missions if m.id == request.mission_id), None)
    if not mission:
        print(f"DEBUG: Mission not found: {request.mission_id}")
        raise_http_error(404, f"Mission '{request.mission_id}' not found. Available missions: {[m.id for m in session_data.missions]}")
    
    print(f"DEBUG: Mission found: {mission}")
    
    # Check if already completed
    if request.mission_id in session_data.completed_missions:
        raise_http_error(403, "Mission already completed")
    
    try:
        # Complete the mission
        points_awarded = session_data.complete_mission(request.mission_id)
        print(f"Points awarded: {points_awarded}")
        if points_awarded is None:
            raise_http_error(500, "Failed to complete mission")
        
        # Update mission status in the database and persist the artifact answer
        await session_manager.update_mission_status(
            session_id,
            request.mission_id,
            "completed",
            session_data.points_total,
            artifact_answer=request.artifact.answer,
        )

        print(f"Completed mission: {request.mission_id}")
        
        # Get next mission from actual session data
        next_mission = None
        if len(session_data.completed_missions) < len(session_data.missions):
            # Find the first incomplete mission
            for mission in session_data.missions:
                if mission.id not in session_data.completed_missions:
                    next_mission = {
                        "id": mission.id,
                        "title": mission.title,
                        "points": mission.points,
                        "category": mission.category,
                        "status": mission.status
                    }
                    break
        
        return CompleteMissionResponse(
            points_awarded=points_awarded,
            points_total=session_data.points_total,
            call_unlocked=session_data.is_call_unlocked(),
            next_mission=next_mission
        )
    except Exception as e:
        print(f"Error in complete_mission: {e}", traceback.format_exc())
        raise_http_error(500, "Scoring update failure")


@router.get("/unlock-status", response_model=UnlockStatusResponse)
async def check_unlock_status(session_id: str = Depends(get_current_session)):
    """
    Quick check whether premium features are unlocked.
    
    **Description:**
    A lightweight endpoint to quickly check if the user has unlocked 
    premium features (specifically the free call feature) without 
    fetching full progress data. Useful for UI state management and 
    feature gating.
    
    **When to use:**
    - Before showing/hiding premium feature buttons
    - In UI components that need to check unlock status
    - When you only need unlock status, not full progress
    - For feature gating in navigation or menus
    - To conditionally enable/disable premium actions
    
    **Authentication Required:**
    Requires a valid Bearer token in the Authorization header.
    
    **Request Headers:**
    ```
    Authorization: Bearer <access_token>
    ```
    
    **No Request Body Required:**
    This is a GET request - no request body needed.
    
    **Response Example (Unlocked):**
    ```json
    {
        "call_unlocked": true
    }
    ```
    
    **Response Example (Still Locked):**
    ```json
    {
        "call_unlocked": false
    }
    ```
    
    **Usage Example:**
    ```javascript
    const accessToken = localStorage.getItem('access_token');
    
    const response = await fetch('/api/unlock-status', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    const { call_unlocked } = await response.json();
    
    // Update UI based on unlock status
    const callButton = document.getElementById('schedule-call-btn');
    const lockIcon = document.getElementById('call-lock-icon');
    
    if (call_unlocked) {
        callButton.disabled = false;
        callButton.textContent = 'Schedule Free Call';
        lockIcon.style.display = 'none';
    } else {
        callButton.disabled = true;
        callButton.textContent = 'Complete missions to unlock';
        lockIcon.style.display = 'inline';
    }
    ```
    
    **React Component Example:**
    ```javascript
    const [callUnlocked, setCallUnlocked] = useState(false);
    
    useEffect(() => {
        const checkUnlockStatus = async () => {
            try {
                const response = await fetch('/api/unlock-status', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const { call_unlocked } = await response.json();
                setCallUnlocked(call_unlocked);
            } catch (error) {
                console.error('Failed to check unlock status:', error);
            }
        };
        
        checkUnlockStatus();
    }, [token]);
    
    return (
        <button 
            disabled={!callUnlocked}
            className={callUnlocked ? 'btn-primary' : 'btn-disabled'}
        >
            {callUnlocked ? '📞 Schedule Call' : '🔒 Complete 2+ missions'}
        </button>
    );
    ```
    
    **Error Cases:**
    - **401 Unauthorized**: Missing or invalid Authorization header
    - **404 Not Found**: Session not found (invalid session ID in token)
    
    **Unlock Logic:**
    - **Free call unlocks** after completing **2 or more missions**
    - Status persists throughout the session
    - Completing additional missions keeps it unlocked
    - Status resets only when starting a new session
    
    **Performance Notes:**
    - This is a lightweight endpoint (faster than `/api/progress`)
    - Safe to call frequently for UI updates
    - Consider caching the result and refreshing after mission completions
    - No need to call on every page load if result is cached
    
    **Integration Patterns:**
    - Use with `/api/mission/complete` responses to avoid extra calls
    - Cache unlock status in local state management (Redux, Zustand, etc.)
    - Refresh after any mission completion
    - Use for conditional rendering of premium features
    
    **Related Endpoints:**
    - Use `/api/progress` for complete mission status and points
    - Use `/api/mission/complete` to actually unlock features
    - Response `call_unlocked` field matches `/api/progress` response
    """
    try:
        # First try to get progress from database
        progress = await session_manager.get_session_progress(session_id)
        
        if progress:
            return UnlockStatusResponse(
                call_unlocked=progress.get("call_unlocked", False)
            )
        
        # Fallback to in-memory session data
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise_http_error(404, "Session not found")
        
        return UnlockStatusResponse(
            call_unlocked=session_data.is_call_unlocked()
        )
        
    except Exception as e:
        print(f"Error in check_unlock_status: {e}", traceback.format_exc())
        raise_http_error(500, "Failed to check unlock status")
