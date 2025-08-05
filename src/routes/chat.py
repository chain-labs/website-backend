"""Chat endpoint routes."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..models.chat import ChatRequest, ChatResponse
from ..auth.middleware import get_current_session
from ..services.session_manager import session_manager
from ..services.chat_service import chat_service
from ..utils.errors import raise_http_error

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(
    chat_request: ChatRequest,
    session_id: str = Depends(get_current_session)
):
    """
    Continue contextual conversation with the AI assistant.
    
    **Description:**
    This endpoint enables ongoing conversation with the AI assistant once the 
    personalized micro-site is live. The assistant maintains full context about
    the user's progress, current page, and goals to provide relevant guidance.
    
    **When to use:**
    - When users need guidance on their AI agent project
    - For contextual help based on current page/section
    - To get mission recommendations and next steps
    - When users ask questions about their progress
    - For getting personalized advice and navigation guidance
    
    **Request Body:**
    ```json
    {
      "message": "Which mission should I tackle next?",
      "context": {
        "page": "mission-dashboard",
        "section": "mission-1",
        "metadata": { "missionId": "defineMetrics" }
      }
    }
    ```
    
    **Context Parameters:**
    - **page**: Current page identifier (e.g., "micro-landing", "case-study", "mission-dashboard")
    - **section**: Specific section/component (e.g., "hero", "mission-3", "progress-widget")  
    - **metadata**: Optional extra state like mission or case study IDs
    
    **Response Example:**
    ```json
    {
      "reply": "Great—you've completed defining your metrics. Next, sketch the agent's decision flow.",
      "history": [
        { "role": "user", "message": "Done with metrics.", "timestamp": "2025-01-20T10:00:10Z" },
        { "role": "assistant", "message": "Next, sketch the decision flow...", "timestamp": "2025-01-20T10:00:12Z" }
      ],
      "updatedProgress": {
        "pointsTotal": 15,
        "missions": [
          { "id": "defineMetrics", "status": "completed", "points": 15 },
          { "id": "sketchFlow", "status": "pending", "points": 15 }
        ],
        "callUnlocked": false
      },
      "followUpMissions": [
        { "id": "sketchFlow", "title": "Sketch Agent Flow", "points": 15 }
      ],
      "suggestedRead": [
        { "id": "cs2", "title": "Menu Recommender", "summary": "How we boosted upsell by 22%" }
      ],
      "navigate": {
        "page": "mission-dashboard",
        "section": "mission-2", 
        "metadata": { "missionId": "sketchFlow" }
      }
    }
    ```
    
    **Response Features:**
    - **reply**: Contextual AI response based on message and current location
    - **history**: Complete chat conversation history
    - **updatedProgress**: Current mission status and points (when relevant)
    - **followUpMissions**: New missions to work on (when applicable)
    - **suggestedRead**: Recommended case studies (when helpful)
    - **navigate**: Frontend routing instruction (when appropriate)
    
    **Usage Examples:**
    
    **Get Mission Guidance:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "I'm stuck on defining metrics. What should I focus on?",
        context: {
          page: "mission-dashboard",
          section: "mission-1",
          metadata: { missionId: "defineMetrics" }
        }
      })
    });
    ```
    
    **Ask for Progress Update:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST', 
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "How many points have I earned so far?",
        context: {
          page: "mission-dashboard",
          section: "progress-widget"
        }
      })
    });
    ```
    
    **Get Case Study Recommendations:**
    ```javascript
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: "Can you show me examples similar to my project?", 
        context: {
          page: "micro-landing",
          section: "hero"
        }
      })
    });
    ```
    
    **Error Cases:**
    - **400 Bad Request**: Missing or invalid message/context fields
      ```json
      { "error": { "code": 400, "message": "Message cannot be empty" } }
      ```
    - **401 Unauthorized**: Missing or invalid access token
      ```json
      { "error": { "code": 401, "message": "Invalid token" } }
      ```
    - **404 Not Found**: Session not found (rare, indicates token/session mismatch)
      ```json
      { "error": { "code": 404, "message": "Session not found" } }
      ```
    - **500 Internal Server Error**: AI assistant or backend failure
      ```json
      { "error": { "code": 500, "message": "AI assistant temporarily unavailable" } }
      ```
    
    **Notes:**
    - Chat history is maintained server-side and returned in each response
    - The assistant uses context to provide relevant, personalized guidance
    - Optional response fields (followUpMissions, navigate, etc.) depend on message content
    - Navigation instructions help frontend show the most relevant page/section
    - All timestamps are in UTC ISO format
    """
    try:
        # Get session data
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise_http_error(404, "Session not found")
        
        # Validate request
        if not chat_request.message.strip():
            raise_http_error(400, "Message cannot be empty")
        
        # Generate AI response using chat service
        response = await chat_service.generate_response(chat_request, session_data)
        
        return response
        
    except Exception as e:
        if hasattr(e, 'status_code'):
            # Re-raise HTTP errors
            raise e
        else:
            # Log and return generic error for unexpected exceptions
            raise_http_error(500, "AI assistant temporarily unavailable")