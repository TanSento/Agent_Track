from agents import Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent, ClarificationPlan
from manager_agent import manager_agent


class ResearchManager:

    async def get_clarifications(self, query: str) -> list[str]:
        """Run the clarifier agent and return its questions."""
        result = await Runner.run(clarifier_agent, f"Query: {query}")
        return result.final_output_as(ClarificationPlan).questions

    async def run(self, query: str, clarifications: str = ""):
        """Run the research pipeline via the manager agent, yielding status and the final report."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            yield "Starting research..."

            input_text = f"Query: {query}"
            if clarifications:
                input_text += f"\nUser clarifications: {clarifications}"

            result = await Runner.run(manager_agent, input_text)

            yield "Research complete."
            yield result.final_output
