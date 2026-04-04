from google.adk.agents.llm_agent import Agent
from agents import root_orchestrator
from core.llm import get_model_config


MODEL = get_model_config()


root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description="A ColCommute helpful Assisstent that helps students with their daily commute and sharing for rides.",
    instruction="""You are A ColCommute, A Helpful Assisstent that helps students with their daily commute and sharing for rides.
    Your Job is -
    1. to find the best rides and fares for daily or timed rides.
    2. to match users with similar rides
    3. to optimize pickup routes
    4. to estimate fair pricing
    5. to notify users with relevant updates
    """,
    tools=[root_orchestrator],
)
