from google.adk.agents.llm_agent import Agent
from agents.routing import routing_agent
from agents.pricing import pricing_agent
from core.llm import get_model_config
from agents.ride_matching import ride_matching_agent
from agents.demand_prediction import demand_prediction_agent
from agents.notification import notification_agent
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from agents.ride import accept_ride_agent, post_ride_agent
from tools import process_payment_tool, log_feedback_tool

orchestrator = Agent(
    model=get_model_config(),
    name="commute_orchestrator",
    description="Coordinates ride matching, routing, pricing, and notifications for student commute",

    tools=[
        process_payment_tool,
        log_feedback_tool,
    ],

    sub_agents=[
        ride_matching_agent,
        routing_agent,
        pricing_agent,
        notification_agent,
        demand_prediction_agent,
        accept_ride_agent,
        post_ride_agent,
    ],

    instruction="""
    You are the Commute Orchestrator. Your goal is to coordinate the full student commute lifecycle:
    
    1. **Matching**: Call ride_matching_agent to find potential carpool partners.
    2. **Optimization**: For matches, use routing_agent for pathing and pricing_agent for cost estimation.
    3. **Strategy**: Consult demand_prediction_agent for peak-hour pricing or availability adjustments.
    4. **Booking**: Use accept_ride_agent to confirm consensus between users.
    5. **Updates**: Use notification_agent for all real-time status changes.
    6. **Completion**: Use post_ride_agent for final payments, feedback, and history logging.
    
    Orchestration Flow:
    Request -> Matching -> Routing/Pricing/Demand -> Notify -> Accept/Book -> Post-Ride.
    """,
)