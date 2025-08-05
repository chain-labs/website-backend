"""Chat service with dummy AI assistant logic."""

import random
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.chat import (
    ChatRequest, ChatResponse, ChatMessage, ChatProgress, 
    ChatNavigation, ChatContext
)
from ..models.goal import Mission, CaseStudy
from ..models.mission import MissionStatus
from .session_manager import SessionData
from .mock_data import mock_data_service


class ChatService:
    """Handles chat interactions with dummy AI logic."""
    
    def __init__(self):
        self.context_responses = {
            "micro-landing": [
                "Welcome! I see you're on the landing page. Ready to dive into your AI agent project?",
                "Great to have you here! What specific aspect of your AI agent would you like to explore?",
                "I'm here to help guide you through building your AI agent. What questions do you have?"
            ],
            "mission-dashboard": [
                "I see you're working on your missions. Which one would you like to focus on next?",
                "You're making great progress! Let me help you with your current mission.",
                "The mission dashboard is perfect for tracking your progress. How can I assist?"
            ],
            "case-study": [
                "This case study shows how other companies have succeeded. What insights interest you most?",
                "Case studies are great for learning patterns. Would you like to see how this applies to your project?",
                "I can help you connect these case study insights to your own AI agent goals."
            ]
        }
        
        self.mission_advice = {
            "defineMetrics": "Start by defining what success looks like for your AI agent. Think about key performance indicators like accuracy, response time, or user satisfaction.",
            "sketchFlow": "Map out your agent's decision-making process. What inputs does it receive? What steps does it take? What outputs does it provide?",
            "gatherData": "Data is the foundation of any AI system. Consider what data sources you'll need and how to ensure data quality.",
            "testPrototype": "Testing early and often helps catch issues before they become major problems. Start with simple test cases.",
            "deployAgent": "Deployment is where your agent meets real users. Consider scalability, monitoring, and gradual rollout strategies."
        }

    async def generate_response(self, request: ChatRequest, session_data: SessionData) -> ChatResponse:
        """Generate a contextual chat response with dummy business logic."""
        
        # Add user message to history
        session_data.add_chat_message("user", request.message)
        
        # Generate contextual reply
        reply = self._generate_contextual_reply(request, session_data)
        
        # Add assistant reply to history
        session_data.add_chat_message("assistant", reply)
        
        # Generate optional response components based on context and message
        follow_up_missions = self._maybe_generate_missions(request, session_data)
        updated_progress = self._maybe_generate_progress(request, session_data)
        suggested_read = self._maybe_suggest_reading(request, session_data)
        navigate = self._maybe_generate_navigation(request, session_data)
        
        return ChatResponse(
            reply=reply,
            history=session_data.get_chat_history(),
            followUpMissions=follow_up_missions,
            updatedProgress=updated_progress,
            suggestedRead=suggested_read,
            navigate=navigate
        )

    def _generate_contextual_reply(self, request: ChatRequest, session_data: SessionData) -> str:
        """Generate a contextual reply based on the user's message and context."""
        message = request.message.lower()
        context = request.context
        
        # Check for mission-specific advice
        if context.metadata and "missionId" in context.metadata:
            mission_id = context.metadata["missionId"]
            if mission_id in self.mission_advice:
                if any(word in message for word in ["help", "how", "what", "next", "stuck", "advice"]):
                    return f"For {mission_id}: {self.mission_advice[mission_id]}"
        
        # Context-based responses
        if context.page in self.context_responses:
            base_responses = self.context_responses[context.page]
            base_reply = random.choice(base_responses)
        else:
            base_reply = "I'm here to help you with your AI agent project. What would you like to know?"
        
        # Message-specific modifications
        if any(word in message for word in ["mission", "next", "what should i do"]):
            if session_data.missions:
                pending_missions = [m for m in session_data.missions if m.id not in session_data.completed_missions]
                if pending_missions:
                    next_mission = pending_missions[0]
                    return f"I'd recommend focusing on '{next_mission.title}' next. {self.mission_advice.get(next_mission.id, 'This will help advance your AI agent project.')}"
            return "Let's start by defining your success metrics. This foundation will guide all other decisions."
        
        elif any(word in message for word in ["progress", "points", "completed"]):
            return f"You've earned {session_data.points_total} points so far and completed {len(session_data.completed_missions)} missions. {"Your call is now unlocked!" if session_data.is_call_unlocked() else "Complete 2 missions to unlock your free consultation call."}"
        
        elif any(word in message for word in ["case study", "example", "learn"]):
            return "Case studies are invaluable for understanding real-world applications. I can recommend specific ones based on your goals and current progress."
        
        elif any(word in message for word in ["stuck", "confused", "help"]):
            return "No worries! Building an AI agent can seem overwhelming. Let's break it down into manageable steps. What specific area would you like clarification on?"
        
        return base_reply

    def _maybe_generate_missions(self, request: ChatRequest, session_data: SessionData) -> Optional[List[Mission]]:
        """Conditionally generate new missions based on context."""
        if any(word in request.message.lower() for word in ["mission", "next", "what should i do"]):
            # Get some mock missions that aren't already assigned
            all_missions = mock_data_service.get_random_missions(5)
            existing_ids = {m.id for m in session_data.missions}
            new_missions = [m for m in all_missions if m.id not in existing_ids]
            
            if new_missions:
                return new_missions[:2]  # Return up to 2 new missions
        return None

    def _maybe_generate_progress(self, request: ChatRequest, session_data: SessionData) -> Optional[ChatProgress]:
        """Conditionally generate progress update."""
        if any(word in request.message.lower() for word in ["progress", "points", "status", "completed"]):
            return ChatProgress(
                pointsTotal=session_data.points_total,
                missions=session_data.get_mission_statuses(),
                callUnlocked=session_data.is_call_unlocked()
            )
        return None

    def _maybe_suggest_reading(self, request: ChatRequest, session_data: SessionData) -> Optional[List[CaseStudy]]:
        """Conditionally suggest case studies."""
        if any(word in request.message.lower() for word in ["case study", "example", "learn", "read", "similar"]):
            return mock_data_service.get_random_case_studies(2)
        return None

    def _maybe_generate_navigation(self, request: ChatRequest, session_data: SessionData) -> Optional[ChatNavigation]:
        """Conditionally generate navigation instructions."""
        message = request.message.lower()
        
        # Navigate to missions if user asks about next steps
        if any(word in message for word in ["mission", "next", "what should i do"]):
            if session_data.missions:
                pending_missions = [m for m in session_data.missions if m.id not in session_data.completed_missions]
                if pending_missions:
                    next_mission = pending_missions[0]
                    return ChatNavigation(
                        page="mission-dashboard",
                        section=f"mission-{next_mission.id}",
                        metadata={"missionId": next_mission.id}
                    )
        
        # Navigate to progress if user asks about status
        elif any(word in message for word in ["progress", "points", "status"]):
            return ChatNavigation(
                page="mission-dashboard",
                section="progress-widget",
                metadata={}
            )
        
        # Navigate to case studies if user wants examples
        elif any(word in message for word in ["case study", "example", "learn"]):
            case_studies = mock_data_service.get_random_case_studies(1)
            if case_studies:
                return ChatNavigation(
                    page="case-study",
                    section="hero",
                    metadata={"caseStudyId": case_studies[0].id}
                )
        
        return None


# Global chat service instance
chat_service = ChatService()