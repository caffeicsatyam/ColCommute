from google.adk.agents.llm_agent import Agent
from core.llm import MODEL_NAME

pricing_agent = Agent(
	model=MODEL_NAME,
	name="pricing_agent",
	description="Estimates fares and suggested pricing for rides.",
	instruction="""
	You are the pricing specialist for ColCommute.
	Calculate fair fares given distance, demand, and number of passengers.
	""",
)
