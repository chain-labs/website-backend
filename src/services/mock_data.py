"""Mock data service for dummy responses."""

import random
from typing import List

from ..models.goal import Goal, Mission, CaseStudy


class MockDataService:
    """Service for generating mock data."""
    
    def __init__(self):
        self.sample_missions = [
            Mission(id="defineMetrics", title="Define Success Metrics", category="planning", points=15),
            Mission(id="sketchFlow", title="Sketch User Flow", category="design", points=15),
            Mission(id="runDemo", title="Run the AI demo", category="development", points=20),
            Mission(id="identifyKPIs", title="Identify Key Performance Indicators", category="planning", points=10),
            Mission(id="buildPrototype", title="Build Initial Prototype", category="development", points=25),
            Mission(id="testUsability", title="Test User Experience", category="testing", points=15),
        ]
        
        self.sample_headlines = [
            "AI Agent for Restaurants: Increase Table Turnover with Contextual Suggestions",
            "Smart Restaurant Assistant: Boost Efficiency with Intelligent Automation", 
            "Customer Experience AI: Personalize Dining with Advanced Analytics",
            "Revenue Optimization Bot: Maximize Profits with Data-Driven Insights",
        ]
    
    def generate_goal_from_input(self, user_input: str) -> Goal:
        """Generate a mock goal based on user input."""
        # Extract keywords for more realistic responses
        input_lower = user_input.lower()
        
        if "restaurant" in input_lower:
            category = "hospitality"
            description = f"Build an AI solution for restaurant operations: {user_input}"
        elif "ai" in input_lower or "agent" in input_lower:
            category = "artificial_intelligence"
            description = f"Develop an intelligent agent: {user_input}"
        else:
            category = "general"
            description = f"Create a solution for: {user_input}"
        
        return Goal(
            description=description,
            category=category,
            priority="high"
        )
    
    def get_random_missions(self, count: int = 4) -> List[Mission]:
        """Get random missions for personalization."""
        return random.sample(self.sample_missions, min(count, len(self.sample_missions)))

    def get_all_case_studies(self) -> List[CaseStudy]:
        """Get all case studies."""
        return self.sample_case_studies
    
    def get_random_case_studies(self, count: int = 3) -> List[CaseStudy]:
        """Get random case studies."""
        return random.sample(self.sample_case_studies, min(count, len(self.sample_case_studies)))
    
    def get_random_headline(self) -> str:
        """Get a random headline."""
        return random.choice(self.sample_headlines)
    
    def get_next_mission(self, completed_missions: set) -> Mission:
        """Get the next available mission."""
        available = [m for m in self.sample_missions if m.id not in completed_missions]
        return random.choice(available) if available else self.sample_missions[0]


# Global mock data service
mock_data_service = MockDataService()