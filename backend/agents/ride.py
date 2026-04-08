from google.adk.agents.llm_agent import Agent
from core.llm import MODEL_NAME
from tools.payment_processing import complete_trip, process_payment, start_trip
from tools.feedback_logging_tool import log_feedback

after_ride_agent = Agent(             
    model=MODEL_NAME,
    name="after_ride_agent",
    description="Handles after-trip tasks: payment processing and feedback logging after a ride is completed.",
    tools=[start_trip, complete_trip, process_payment, log_feedback],
    instruction="""
    You are the After-Ride Agent for the ColCommute system.
    
    Your responsibilities include:
    1. Start a confirmed ride with `start_trip` when the ride begins.
    2. Mark the ride as completed with `complete_trip` when it ends.
    3. Persist payment settlement with `process_payment` only after the ride is completed.
    4. Persist post-ride feedback with `log_feedback`.
    
    Only activate after a trip is confirmed. Respect the real trip status transitions.
    """
)

