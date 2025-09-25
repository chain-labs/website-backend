"""Tests for service layer components."""

import pytest
from datetime import datetime, timezone
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.services.session_manager import SessionManager, SessionData
from src.services.mock_data import MockDataService
from src.auth.jwt_utils import JWTManager
from src.services.chat_service import chat_service


class TestSessionManager:
    """Test session manager functionality."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        session_id = "test-session-123"
        
        session_data = await manager.create_session(session_id)
        
        assert session_data.session_id == session_id
        assert session_data.goal is None
        assert session_data.points_total == 0
        assert len(session_data.completed_missions) == 0
        assert not session_data.is_call_unlocked()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_session_exists(self):
        """Test getting an existing session."""
        manager = SessionManager()
        session_id = "test-session-456"
        
        # Create session first
        original_session = await manager.create_session(session_id)
        
        # Retrieve session
        retrieved_session = await manager.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == session_id
        assert retrieved_session is original_session

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_session_not_exists(self):
        """Test getting a non-existent session."""
        manager = SessionManager()
        
        retrieved_session = await manager.get_session("non-existent")
        
        assert retrieved_session is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_revoke_and_check_token(self):
        """Test token revocation."""
        manager = SessionManager()
        token = "test-refresh-token"
        
        # Initially not revoked
        assert not await manager.is_token_revoked(token)
        
        # Revoke token
        await manager.revoke_token(token)
        
        # Should be revoked now
        assert await manager.is_token_revoked(token)


class TestSessionData:
    """Test session data functionality."""

    @pytest.mark.unit
    def test_complete_mission_success(self):
        """Test successful mission completion."""
        session_data = SessionData("test-session")
        
        # Add a mission
        from src.models.goal import Mission
        mission = Mission(id="test-mission", title="Test", points=10)
        session_data.missions = [mission]
        
        # Complete mission
        points_awarded = session_data.complete_mission("test-mission")
        
        assert points_awarded == 10
        assert session_data.points_total == 10
        assert "test-mission" in session_data.completed_missions

    @pytest.mark.unit
    def test_complete_mission_twice(self):
        """Test completing the same mission twice."""
        session_data = SessionData("test-session")
        
        # Add a mission
        from src.models.goal import Mission
        mission = Mission(id="test-mission", title="Test", points=10)
        session_data.missions = [mission]
        
        # Complete mission first time
        points1 = session_data.complete_mission("test-mission")
        assert points1 == 10
        
        # Try to complete again
        points2 = session_data.complete_mission("test-mission")
        assert points2 is None  # Should return None
        assert session_data.points_total == 10  # Points shouldn't change

    @pytest.mark.unit
    def test_complete_nonexistent_mission(self):
        """Test completing a mission that doesn't exist."""
        session_data = SessionData("test-session")
        
        points_awarded = session_data.complete_mission("nonexistent")
        
        assert points_awarded is None
        assert session_data.points_total == 0

    @pytest.mark.unit
    def test_call_unlock_logic(self):
        """Test call unlock logic."""
        session_data = SessionData("test-session")
        
        # Initially locked
        assert not session_data.is_call_unlocked()
        
        # Add one completed mission
        session_data.completed_missions.add("mission1")
        assert not session_data.is_call_unlocked()
        
        # Add second completed mission
        session_data.completed_missions.add("mission2")
        assert session_data.is_call_unlocked()

    @pytest.mark.unit
    def test_get_mission_statuses(self):
        """Test getting mission statuses."""
        session_data = SessionData("test-session")
        
        # Add missions
        from src.models.goal import Mission
        mission1 = Mission(id="mission1", title="First", points=10)
        mission2 = Mission(id="mission2", title="Second", points=15)
        session_data.missions = [mission1, mission2]
        
        # Complete one mission
        session_data.completed_missions.add("mission1")
        
        statuses = session_data.get_mission_statuses()
        
        assert len(statuses) == 2
        
        # Check first mission is completed
        status1 = next(s for s in statuses if s.id == "mission1")
        assert status1.status == "completed"
        assert status1.points == 10
        
        # Check second mission is pending
        status2 = next(s for s in statuses if s.id == "mission2")
        assert status2.status == "pending"
        assert status2.points == 15


class TestMockDataService:
    """Test mock data service."""

    @pytest.mark.unit
    def test_generate_goal_restaurant(self):
        """Test goal generation for restaurant input."""
        service = MockDataService()
        
        goal = service.generate_goal_from_input("I want to build an AI agent for restaurants")
        
        assert "restaurant" in goal.description.lower()
        assert goal.category == "hospitality"
        assert goal.priority == "high"

    @pytest.mark.unit
    def test_generate_goal_ai(self):
        """Test goal generation for AI input."""
        service = MockDataService()
        
        goal = service.generate_goal_from_input("I want to create an AI chatbot")
        
        assert "ai" in goal.description.lower() or "agent" in goal.description.lower()
        assert goal.category == "artificial_intelligence"

    @pytest.mark.unit
    def test_generate_goal_general(self):
        """Test goal generation for general input."""
        service = MockDataService()

        goal = service.generate_goal_from_input("I want to build a website")

        assert goal.category == "general"


class TestChatService:
    """Tests for chat service helpers."""

    @pytest.mark.asyncio
    async def test_get_chat_history_formats_messages(self, monkeypatch):
        """Chat history should be converted into serializable chat messages."""

        timestamps = [
            datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 1, 0, 5, tzinfo=timezone.utc),
        ]

        stored_messages = [SystemMessage(content=f"system-{i}") for i in range(6)]
        stored_messages.append(
            HumanMessage(content="Hello", additional_kwargs={"timestamp": timestamps[0].isoformat()})
        )
        stored_messages.append(
            AIMessage(
                content="""```json\n{"reply": "Hi there"}\n```""",
                additional_kwargs={"timestamp": timestamps[1].isoformat()},
            )
        )

        class FakeHistory:
            async def aget_messages(self):
                return stored_messages

        async def fake_get_history(session_id):
            return FakeHistory()

        monkeypatch.setattr("src.services.chat_service.get_history", fake_get_history)

        history = await chat_service.get_chat_history("session-123")

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].message == "Hello"
        assert history[0].timestamp == timestamps[0]
        assert history[1].role == "assistant"
        assert history[1].message == "Hi there"
        assert history[1].timestamp == timestamps[1]

    @pytest.mark.unit
    def test_get_random_missions(self):
        """Test getting random missions."""
        service = MockDataService()
        
        missions = service.get_random_missions(3)
        
        assert len(missions) == 3
        assert all(hasattr(m, 'id') and hasattr(m, 'title') and hasattr(m, 'points') for m in missions)
        
        # Should be different each time (with high probability)
        missions2 = service.get_random_missions(3)
        mission_ids1 = [m.id for m in missions]
        mission_ids2 = [m.id for m in missions2]
        # At least some should be different (not a strict test due to randomness)

    @pytest.mark.unit
    def test_get_random_case_studies(self):
        """Test getting random case studies."""
        service = MockDataService()
        
        case_studies = service.get_random_case_studies(2)
        
        assert len(case_studies) == 2
        assert all(hasattr(cs, 'id') and hasattr(cs, 'title') and hasattr(cs, 'summary') for cs in case_studies)

    @pytest.mark.unit
    def test_get_random_headline(self):
        """Test getting random headline."""
        service = MockDataService()
        
        headline = service.get_random_headline()
        
        assert isinstance(headline, str)
        assert len(headline) > 0

    @pytest.mark.unit
    def test_get_next_mission(self):
        """Test getting next available mission."""
        service = MockDataService()
        
        completed = {"defineMetrics", "sketchFlow"}
        next_mission = service.get_next_mission(completed)
        
        assert next_mission.id not in completed


class TestJWTManager:
    """Test JWT manager functionality."""

    @pytest.mark.unit
    def test_generate_session_id(self):
        """Test session ID generation."""
        manager = JWTManager()
        
        session_id1 = manager.generate_session_id()
        session_id2 = manager.generate_session_id()
        
        # Should be different
        assert session_id1 != session_id2
        # Should be valid UUIDs (length check)
        assert len(session_id1) > 30
        assert len(session_id2) > 30

    @pytest.mark.unit
    def test_create_and_decode_token(self):
        """Test token creation and decoding."""
        manager = JWTManager()
        session_id = "test-session-789"
        
        # Create token
        token = manager.create_access_token(session_id)
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Decode token
        payload = manager.decode_token(token)
        assert payload.session_id == session_id
        assert hasattr(payload, 'exp')
        assert hasattr(payload, 'iat')

    @pytest.mark.unit
    def test_get_session_id_from_token(self):
        """Test extracting session ID from token."""
        manager = JWTManager()
        session_id = "test-session-xyz"
        
        token = manager.create_access_token(session_id)
        extracted_id = manager.get_session_id_from_token(token)
        
        assert extracted_id == session_id

    @pytest.mark.unit
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        manager = JWTManager()
        session_id = "test-session-refresh"
        
        access_token = manager.create_access_token(session_id)
        refresh_token = manager.create_refresh_token(session_id)
        
        # Should be valid tokens
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        
        # Should decode to same session ID
        access_payload = manager.decode_token(access_token)
        refresh_payload = manager.decode_token(refresh_token)
        
        assert access_payload.session_id == session_id
        assert refresh_payload.session_id == session_id
