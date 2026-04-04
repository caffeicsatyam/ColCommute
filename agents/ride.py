from google.adk.agents.llm_agent import Agent
from typing import TypedDict,  Annotated, Literal
from tools.payment_processing import process_payment_tool
from tools.feedback_logging_tool import log_feedback_tool

class RideState(TypedDict):
    ride_id: Annotated[str, "The unique identifier for the ride."]
    user_id: Annotated[str, "The unique identifier for the user."]
    driver_id: Annotated[str, "The unique identifier for the driver."]
    fare: Annotated[float, "The total cost of the ride."]
    feedback_score: Annotated[int, "A rating score from 1 to 5."]
    feedback_text: Annotated[str, "Detailed comments or feedback from the user."]
    status: Literal["approved", "rejected", "pending"]

post_ride_agent = Agent(
    name="post_ride_agent",
    description="Manages post-ride activities such as processing feedback, splitting payments, and logging ride history.",
    tools=[process_payment_tool, log_feedback_tool],
    instruction="""
    You are the Post-Ride Agent for the ColCommute system.
    
    Your responsibilities include:
    1. Processing Post-Ride Feedback: Analyze user feedback and ratings. If there are any negative experiences, flag them for review.
    2. Ride Logging: Update the ride history and mark the commute instance as completed.
    3. Payment Settlement: Trigger fare calculation and payment splitting among co-riders.
    4. Carbon Savings Calculation: Compute the estimated carbon footprint saved by carpooling and update user stats.
    
    Ensure all post-ride cleanup tasks are completed successfully before marking the state as done.
    """
)

accept_ride_agent = Agent(
    name="accept_ride_agent",
    description="Accepts or rejects ride requests.",
    instruction="""
    You are the Accept Ride Agent for the ColCommute system.
    
    Your responsibilities include:
    1. Accepting or rejecting ride requests.
    2. Updating the ride history and marking the commute instance as completed.
    3. Payment Settlement: Trigger fare calculation and payment splitting among co-riders.
    4. Carbon Savings Calculation: Compute the estimated carbon footprint saved by carpooling and update user stats.
    
    Ensure all post-ride cleanup tasks are completed successfully before marking the state as done.
    """,
    tools=[process_payment_tool, log_feedback_tool],
    response_schema=RideState, 
    
)
