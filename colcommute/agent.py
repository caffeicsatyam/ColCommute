"""
ADK entry: `root_agent` is the top-level commute orchestrator (sub_agents + instructions).

Specialist agents live under `agents/`; their ADK tools are implemented under `tools/`.
"""

from typing import Any, Dict, List, TypedDict

from google.adk.agents.llm_agent import Agent
from agents import root_orchestrator
from core.llm import get_model_config


MODEL = get_model_config()


root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description="A specialist assistant for student carpooling and daily commutes.",
    instruction="""
    You are the ColCommute Root Agent. Your purpose is to help students with their daily commute.
    You delegate all specialized tasks (matching, routing, pricing, etc.) to the commute_orchestrator.
    """,
    sub_agents=[root_orchestrator],
)

