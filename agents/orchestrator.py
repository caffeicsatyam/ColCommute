from mcp import Notification
from google.adk.flows.llm_flows import instructions
from google.adk.agents.llm_agent import Agent
from agents.routing import routing_agent
from agents.pricing import pricing_agent
from core.llm import get_model_config
from google.adk.agents.parallel_agent import ParallelAgent
from agents.ride_matching import ride_matching_agent
from agents.demand_prediction import demand_prediction_agent
from agents.notification import notification_agent
from google.adk.agents import LlmAgent
from typing import TypedDict, List, Dict, Any






orchestrator = Agent(
    name="commute_orchestrator",
    description="Coordinates ride matching, routing, pricing, and notifications for student commute",
    
    tools=[
        ride_matching_tool,
        routing_tool,
        pricing_tool,
        notification_tool,
    ],
    
    instruction="""
    You are a commute orchestrator agent.

    Your job is to:
    1. Match users with similar rides
    2. Optimize pickup routes
    3. Estimate fair pricing
    4. Notify users with relevant updates

    Always follow this sequence:
    ride_matching → routing → pricing → notification
    """,
)





class RideState(TypedDict):
    user_id: str
    pickup: str
    destination: str
    time: str
    
    matches: List[Dict[str, Any]]
    route: Dict[str, Any]
    pricing: Dict[str, Any]
    
    notifications: List[str]