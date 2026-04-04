from typing import Dict, Any
from google.adk.tools import FunctionTool

def log_feedback(ride_id: str, user_id: str, feedback_score: int, feedback_text: str) -> Dict[str, Any]:
    """
    Logs user feedback for a completed ride.
    """
    print(f"Logging feedback for ride {ride_id} from user {user_id}: {feedback_score}/5 - {feedback_text}")
    return {
        "status": "success",
        "message": f"Feedback for ride {ride_id} has been logged successfully.",
        "feedback_id": "feedback_12345"
    }

log_feedback_tool = FunctionTool(func=log_feedback)