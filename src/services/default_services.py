"""Services that corresponds to default values"""

from src.services import cms


DEFAULT_MISSIONS = [
    {
        "id": "input_mission_goal",
        "title": "Enter your primary goal.",
        "description": "Get started with the best description of what you really want to get done.",
        "points": 10,
        "icon": "goal",
        "input": {
            "required": True,
            "type": "text",
            "placeholder": "I want to build a ..."
        },
        "missionType": "GOAL_INPUT",
        "options": {
            "targetCaseStudyId": 'N/A',
        },
        "status": "completed"
    },
    {
        "id": "input_mission_clarify",
        "title": "Clarify your goal",
        "description": "Add more details or context to your goal to help personalize your experience.",
        "points": 20,
        "icon": "edit-3",
        "input": {
            "required": True,
            "type": "text",
            "placeholder": "Add clarification, e.g. 'Focus on customer satisfaction'"
        },
        "missionType": "GOAL_CLARIFICATION",
        "options": {
            "targetCaseStudyId": 'N/A',
        },
        "status": "completed"
    },
    {
        "id": "vapi_web_call_mission",
        "title": "Make a Vapi Web Call",
        "description": "Initiate a Vapi web call to connect with an expert or service.",
        "points": 20,
        "icon": "phone-call",
        "input": {
            "required": False,
            "type": "N/A",
            "placeholder": "Start Vapi Call"
        },
        "missionType": "VAPI_WEB_CALL",
        "options": {
            "targetCaseStudyId": 'N/A',
        },
        "status": "pending"
    },
    
]


DEFAULT_HERO = {
    "title": "Build trusted AI-powered solutions with Chain Labs",
    "description": "We help you define, prototype, and deliver secure digital systems"
  }

DEFAULT_PROCESS = [
    {
        "name": "Problem Framing (Understand Why)", 
        "description": "We collaborate with you to identify general business pain points and outline how technology can add measurable efficiency and trust." 
    },
    { 
        "name": "Discovery", 
        "description": "We explore potential technical requirements broadly, ensuring flexibility whether you need blockchain, AI, or secure data infrastructure." 
    },
    { 
        "name": "Solution Prototyping", 
        "description": "We provide quick proofs of concept tailored to common enterprise needs, helping you validate potential before full investment." 
    },
    { 
        "name": "Agile Development and Pilot", 
        "description": "We iteratively design, develop, and test your solution, refining based on feedback to ensure practical deployment readiness." 
    },
    { 
        "name": "Delivery", 
        "description": "We manage the final deployment and handoff smoothly, providing support and documentation for a reliable long-term system." 
    }
  ],


def get_default_case_studies() -> list:
    """
    Returns a list of default case studies.

    This function retrieves the default set of case studies by their IDs.
    It is typically used to provide example or fallback case studies when
    personalized or user-specific case studies are not available.

    Returns:
        list: A list of case study dictionaries.
    """
    case_study_ids = ["case-1", "case-2", "case-3"]
    case_studies = cms.get_case_studies_by_ids(case_study_ids)

    return case_studies


def add_default_missions(missions_list: list) -> list:
    """
    Adds the default missions to the provided missions_list if they are not already present (by id).
    Returns the updated missions_list.
    """

    # Get existing mission ids for deduplication
    existing_ids = {m.get("id") for m in missions_list if isinstance(m, dict) and "id" in m}

    # Add any default mission not already present
    for default_mission in DEFAULT_MISSIONS:
        if default_mission["id"] not in existing_ids:
            missions_list.append(default_mission)

    return missions_list
