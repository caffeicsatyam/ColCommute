from google.adk.agents.llm_agent import Agent
from typing import Literal
from pydantic import BaseModel, Field
from tools.payment_processing import process_payment_tool
from tools.feedback_logging_tool import log_feedback_tool

class NotificationState(BaseModel):
    ride_id: str = Field(..., description="The unique identifier for the ride.")
    user_id: str = Field(..., description="The unique identifier for the user.")
    driver_id: str = Field(..., description="The unique identifier for the driver.")
    fare: float = Field(..., description="The total cost of the ride.")
    feedback_score: int = Field(..., description="A rating score from 1 to 5.")
    feedback_text: str = Field(..., description="Detailed comments or feedback from the user.")
    status: Literal["approved", "rejected", "pending"]

notification_agent = Agent(
    name="notification_agent",
    description="Responsible for sending timely updates and notifications to users and drivers.",
    instruction="""
    You are the Notification Agent for the ColCommute system.
    
    Your responsibilities include:
    1. Sending status updates: Notify users when a ride is matched, accepted, or started.
    2. Alerts: Send reminders for upcoming rides.
    3. Multi-channel delivery: Determine whether to use Push, SMS, or Email based on user preferences.
    4. Feedback Prompts: Notify users to rate their ride once it's completed.
    
    Ensure clear and concise communication across all channels.
    """
)