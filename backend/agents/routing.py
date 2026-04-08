from google.adk.agents.llm_agent import Agent
from core.llm import MODEL_NAME
from tools.routing import get_route

routing_agent = Agent(
    model=MODEL_NAME,
    name="routing_agent",
    description="Gets real route, distance and duration between two places using Google Maps.",
    instruction="""
    You are the routing specialist for ColCommute.
    
    When given an origin and destination:
    1. Call get_route to fetch the real route from Google Maps.
    2. Summarize the distance, duration, and key steps in plain language.
    3. Never make up distances or directions.
    
    Example response: "Route from Meerut to ABESIT Ghaziabad: 38 km, ~55 mins via NH-58."
    """,
    tools=[get_route]
)