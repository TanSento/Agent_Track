# Deep Research — Project Notes

## What this is
A multi-agent deep research tool. User submits a query, agents plan searches, run them in parallel, write a report, and email it. Built with the OpenAI Agents SDK and a Gradio UI.

## Run
```bash
uv run deep_research.py
```

## Architecture

```
User query
  → ClarifierAgent     # asks 3+ clarifying questions, user answers in UI
  → PlannerAgent       # plans 5 web searches, informed by clarifications
  → SearchAgent x5     # parallel web searches, each returns a summary
  → WriterAgent        # synthesizes into a detailed markdown report
  → EmailAgent         # converts to HTML and sends via SendGrid
```

## Files

| File | Purpose |
|---|---|
| `deep_research.py` | Gradio UI entry point |
| `research_manager.py` | Async orchestrator, yields status strings to UI |
| `planner_agent.py` | Outputs `WebSearchPlan` (list of `WebSearchItem`) |
| `search_agent.py` | Runs one web search, returns 2-3 paragraph summary |
| `writer_agent.py` | Outputs `ReportData` (summary, markdown report, follow-up questions) |
| `email_agent.py` | Sends HTML email via SendGrid |

## Key types

- `WebSearchItem` — `{reason: str, query: str}`
- `WebSearchPlan` — `{searches: list[WebSearchItem]}`
- `ReportData` — `{short_summary, markdown_report, follow_up_questions}`

## Target architecture

The final `ResearchManager` becomes a **manager agent** that drives the pipeline using:
- **Agents-as-tools**: PlannerAgent, SearchAgent, WriterAgent, EmailAgent are each wrapped as tools the manager can call
- **Handoffs**: manager hands off to ClarifierAgent to collect user clarifications, then resumes with enriched context

```
User query
  → ManagerAgent
      ├─ handoff → ClarifierAgent   # asks 3+ questions, returns answers
      ├─ tool    → PlannerAgent     # plans searches using query + answers
      ├─ tool    → SearchAgent x N  # parallel searches
      ├─ tool    → WriterAgent      # writes report
      └─ tool    → EmailAgent       # sends email
```

## Step-by-step implementation plan

Do one step at a time. Validate each before moving on.

**Step 1 — ClarifierAgent**
- Add `clarifier_agent.py`: takes a query, outputs `ClarificationPlan` (min 3 questions)
- Update `deep_research.py`: after query submit, show questions and collect answers before running pipeline
- Update `research_manager.py`: pass clarifications into `plan_searches`

**Step 2 — Agents-as-tools**
- Wrap PlannerAgent, SearchAgent, WriterAgent, EmailAgent as tools using the Agents SDK `as_tool()` pattern
- Manager calls them via tool use instead of direct `Runner.run()` calls

**Step 3 — Manager agent with handoffs**
- Replace `ResearchManager` orchestration logic with a `ManagerAgent`
- Manager hands off to ClarifierAgent for the clarification step
- Manager uses the wrapped agent-tools for all other steps

## Env vars required
- `OPENAI_API_KEY`
- `SENDGRID_API_KEY`

## Models
All agents use `gpt-4o-mini`.

## Notes
- Email: from `minhtanbuinguyen@gmail.com` → `tan.m.bui96@outlook.com`
- Traces visible at `https://platform.openai.com/traces/trace?trace_id=<id>`
- `search_context_size="low"` on `WebSearchTool` for cost efficiency
