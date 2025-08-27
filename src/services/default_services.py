"""Services that corresponds to default values"""

from src.models.goal import Process
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

DEFAULT_PROCESS: list[Process] = [
    Process(
        name="Problem Framing (Understand Why)", 
        description="We collaborate with you to identify general business pain points and outline how technology can add measurable efficiency and trust." 
    ),
    Process(
        name="Discovery",
        description="We explore potential technical requirements broadly, ensuring flexibility whether you need blockchain, AI, or secure data infrastructure."
    ),
    Process(
        name="Solution Prototyping",
        description="We provide quick proofs of concept tailored to common enterprise needs, helping you validate potential before full investment."
    ),
    Process(
        name="Agile Development and Pilot",
        description="We iteratively design, develop, and test your solution, refining based on feedback to ensure practical deployment readiness."
    ),
    Process(
        name="Delivery",
        description="We manage the final deployment and handoff smoothly, providing support and documentation for a reliable long-term system."
    )
]


async def get_default_case_studies() -> list:
    """
    Returns a list of default case studies.

    This function retrieves the default set of case studies by their IDs.
    It is typically used to provide example or fallback case studies when
    personalized or user-specific case studies are not available.

    Returns:
        list: A list of case study dictionaries.
    """
    case_study_ids = ["case-1", "case-2", "case-3"]
    case_studies = await cms.get_case_studies_by_ids(case_study_ids)

    return case_studies


# src/services/default_services.py
def normalize_process_list(proc):
    # unwrap ( [ ... ], ) shape
    if isinstance(proc, tuple) and len(proc) == 1 and isinstance(proc[0], list):
        proc = proc[0]
    if isinstance(proc, list):
        # already dicts
        if all(isinstance(x, dict) for x in proc):
            return proc
        # pydantic Process instances
        try:
            from src.models.goal import Process as ProcessModel
            if all(isinstance(x, ProcessModel) for x in proc):
                return [x.model_dump() for x in proc]
        except Exception:
            pass
        # list/tuple pairs
        if all(isinstance(x, (list, tuple)) and len(x) >= 2 for x in proc):
            return [{"name": x[0], "description": x[1]} for x in proc]
    return []


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
