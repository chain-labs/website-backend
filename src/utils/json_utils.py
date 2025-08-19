import json
import re
from typing import Any, Dict


FENCED_JSON_PATTERN = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_from_fenced_block(text: str) -> Dict[str, Any]:
    """
    Extract and parse the first fenced JSON block from a text string.

    Looks for a Markdown fenced block labeled as json (```json ... ```),
    parses its contents as JSON and returns the resulting dictionary.

    Raises:
        ValueError: If no fenced JSON block is found in the text.
        json.JSONDecodeError: If the fenced content is not valid JSON.
    """
    if text is None:
        raise ValueError("No text provided for JSON extraction")

    json_string = {}

    match = FENCED_JSON_PATTERN.search(text)
    if not match:
        json_string = text
    else:
        json_string = match.group(1).strip()

    return json.loads(json_string)


