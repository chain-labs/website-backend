"""Services that corresponds to default values"""

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
