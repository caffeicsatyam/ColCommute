from google.adk.agents.llm_agent import Agent

from core.llm import MODEL_NAME
from tools.pricing import calculate_fare_split


pricing_agent = Agent(
    model=MODEL_NAME,
    name="pricing_agent",
    description="Splits cab or ride fare among the driver and co-riders.",
    instruction="""
    You are the pricing specialist for ColCommute.

    When a user provides a real fare amount:
    1. Extract total_fare and the number of additional riders from context.
    2. Prefer co_rider_count when the rider count is explicit.
    3. If the user phrases it as seats_needed or vacant_seats being filled, use that same count.
    4. Call calculate_fare_split.
    5. Respond clearly, for example: "Each person pays Rs.X and the riders together cover Rs.Y."

    Never invent prices. Only calculate pricing when the user gives an actual fare.
    """,
    tools=[calculate_fare_split],
)
