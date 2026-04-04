from google.adk.agents.llm_agent import Agent
from agents import root_orchestrator
from core.llm import get_model_config

MODEL = get_model_config()


root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description="ColCommute — a helpful assistant that helps students with daily commutes and ride-sharing.",
    instruction="""You are ColCommute, a helpful Assistant that helps students with their daily commute and ride-sharing.
Your job is:
1. Find the best rides and fares for daily or scheduled trips.
2. Match users with similar rides.
3. Optimize pickup routes.
4. Estimate fair pricing.
5. Notify users with relevant updates.
""",
    tools=[root_orchestrator],
)
