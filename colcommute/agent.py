"""
ADK entry: `root_agent` is the top-level commute orchestrator (sub_agents + instructions).

Specialist agents live under `agents/`; their ADK tools are implemented under `tools/`.
"""

from typing import Any, Dict, List, TypedDict

from google.adk.agents.llm_agent import Agent

from agents.ride_matching import ride_matching_agent
from core.llm import MODEL_NAME

# Add when ready:
# from agents.routing import routing_agent
# from agents.pricing import pricing_agent
# from agents.notification import notification_agent

root_agent = Agent(
    model=MODEL_NAME,
    name="commute_orchestrator",
    description=(
        "Coordinates student commute: delegates to specialists for matching, routes, pricing, and alerts."
    ),
    instruction="""
    You are the commute orchestrator.

    Goals:
    1. Match users with similar rides (ride_matching_agent)
    2. Optimize pickup routes (not wired yet)
    3. Estimate fair pricing (not wired yet)
    4. Notify users (not wired yet)

    When the user needs to post a trip, find people to share with, or check vacant seats,
    transfer or delegate to **ride_matching_agent** so it can use its own tools.

    Preferred order when multiple steps apply: matching → routing → pricing → notification.
    Only the ride-matching specialist is available today; say others are coming soon if asked.
    """,
    sub_agents=[
        ride_matching_agent,
        # routing_agent,
        # pricing_agent,
        # notification_agent,
    ],
)

