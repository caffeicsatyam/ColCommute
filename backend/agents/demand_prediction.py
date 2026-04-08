from google.adk.agents.llm_agent import Agent
from core.llm import MODEL_NAME

demand_prediction_agent = Agent(
    model=MODEL_NAME,
    name="demand_prediction_agent",
    description="Predicts short-term demand for rides to assist pricing and allocation.",
    instruction="""
    You are the demand prediction specialist for ColCommute.
    Given historical and real-time signals, predict demand in a short time window.
    """,
)
