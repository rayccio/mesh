from datetime import datetime
from typing import Any, Dict, List

def prepare_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert datetime objects in a dictionary to ISO format strings.
    This makes the dictionary safe for JSON serialization (e.g., for PostgreSQL JSON columns).
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = prepare_json_data(value)
        elif isinstance(value, list):
            result[key] = [
                prepare_json_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result
