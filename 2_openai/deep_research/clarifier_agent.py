from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a research assistant. Given a research query, generate clarifying questions "
    "to better understand what the user needs. Ask at least 3 specific, targeted questions "
    "that will help narrow down the scope, focus, and depth of the research."
    "If you think is query is unclear, ask more questions to clarify it."
)


class ClarificationPlan(BaseModel):
    questions: list[str] = Field(description="Clarifying questions to ask the user, minimum 3.")


clarifier_agent = Agent(
    name="ClarifierAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClarificationPlan,
)
