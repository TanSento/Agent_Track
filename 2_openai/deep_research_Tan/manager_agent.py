from agents import Agent
from planner_agent import planner_tool
from search_agent import search_tool
from writer_agent import writer_tool
from email_agent import email_agent

INSTRUCTIONS = """You are a research manager orchestrating a full research pipeline.

Given a research query and optional user clarifications, follow these steps in order:

1. Call plan_searches with the query and clarifications to get a list of web searches.
   The result is a JSON object with a "searches" array. Each item has a "query" field.

2. Call search_web once for each search query from the plan. Collect all the summaries.

3. Call write_report with the original query and all the search summaries combined.
   The result is a JSON object — extract the "markdown_report" field.

4. Hand off to the Email agent with the markdown report so it can send the email.

Be thorough: run every search from the plan before writing the report."""

manager_agent = Agent(
    name="ManagerAgent",
    instructions=INSTRUCTIONS,
    tools=[planner_tool, search_tool, writer_tool],
    handoffs=[email_agent],
    model="gpt-4o",
)
