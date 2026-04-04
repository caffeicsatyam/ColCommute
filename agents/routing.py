from google.adk.agents.llm_agent import Agent
from core.llm import MODEL_NAME

routing_agent = Agent(
	model=MODEL_NAME,
	name="routing_agent",
	description="Optimizes pickup and dropoff routes for shared rides.",
	instruction="""
	You are the routing specialist for ColCommute.
	Generate optimized pickup sequences and route maps given origin/destination points.
	""",
)
