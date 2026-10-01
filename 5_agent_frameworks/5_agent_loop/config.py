"""The two models the agent loop uses, kept in one place so they are easy to swap.

Both the Google ADK orchestrator (look, hub, QA) and the five workers talk to
OpenRouter. The demo uses the bigger models. To run cheaply, change the two
defaults below to the commented alternatives (or set the matching env var
for a one-off run). OpenRouter model ids include the provider prefix
(google/..., openai/...).
"""

import os

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "google/gemini-3.5-flash")  # cheaper: google/gemini-3.1-flash-lite
WORKER_MODEL = os.environ.get("WORKER_MODEL", "openai/gpt-5.5")  # cheaper: openai/gpt-5.4-mini


def orchestrator_llm():
    """ADK model: the same Gemini model, routed through OpenRouter via LiteLLM."""
    from google.adk.models.lite_llm import LiteLlm

    slug = ORCHESTRATOR_MODEL if ORCHESTRATOR_MODEL.startswith("openrouter/") else f"openrouter/{ORCHESTRATOR_MODEL}"
    return LiteLlm(
        model=slug,
        api_base=OPENROUTER_BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
