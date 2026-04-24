# Deep Research — Project Notes

## What this is
A multi-agent deep research tool. User submits a query, a clarifier asks follow-up questions, agents plan and run searches, write a report, and email it. Built with the OpenAI Agents SDK and a Gradio UI.

## Run
```bash
uv run deep_research.py
```

## Current architecture (implemented)

```
User query
  → UI: ClarifierAgent asks 3+ questions, user answers (optional)
  → ManagerAgent
      ├─ tool    → PlannerAgent     # plans 5 searches using query + answers
      ├─ tool    → SearchAgent x N  # sequential web searches (see known issues)
      ├─ tool    → WriterAgent      # writes detailed markdown report
      └─ handoff → EmailAgent       # converts to HTML and sends via SendGrid
```

## Files

| File | Purpose |
|---|---|
| `deep_research.py` | Gradio UI entry point — two-step flow: clarify then run |
| `research_manager.py` | Thin async orchestrator: runs clarifier + kicks off manager agent |
| `clarifier_agent.py` | Generates 3+ clarifying questions from a query (`ClarificationPlan`) |
| `manager_agent.py` | ManagerAgent — orchestrates planner/search/writer tools, hands off to email |
| `planner_agent.py` | Outputs `WebSearchPlan` (list of `WebSearchItem`) + `planner_tool` |
| `search_agent.py` | Runs one web search, returns 2-3 paragraph summary + `search_tool` |
| `writer_agent.py` | Outputs `ReportData` (summary, markdown report, follow-ups) + `writer_tool` |
| `email_agent.py` | Sends HTML email via SendGrid (used as handoff target) |

## Key types

- `WebSearchItem` — `{reason: str, query: str}`
- `WebSearchPlan` — `{searches: list[WebSearchItem]}`
- `ReportData` — `{short_summary, markdown_report, follow_up_questions}`
- `ClarificationPlan` — `{questions: list[str]}`

## UI flow

1. User enters query → clicks **Start** → ClarifierAgent generates 3+ questions
2. Questions shown; answers textbox appears (optional — user can leave blank)
3. User clicks **Run Research** → ManagerAgent takes over
4. Final markdown report rendered in UI

## Agent tools and handoffs

Each agent exposes an `as_tool()` wrapper used by the ManagerAgent:

| Export | From | Type |
|---|---|---|
| `planner_tool` | `planner_agent.py` | tool |
| `search_tool` | `search_agent.py` | tool |
| `writer_tool` | `writer_agent.py` | tool |
| `email_agent` | `email_agent.py` | handoff target |

## Known issues / next steps

- **Searches are sequential**: the ManagerAgent calls `search_web` one at a time. The original code ran all 5 searches in parallel via `asyncio.gather`. Fix options:
  - A single `search_all` function tool that fans out with `asyncio.gather` internally
  - Keep parallel search outside the agent in `ResearchManager`

## Env vars required
- `OPENAI_API_KEY`
- `SENDGRID_API_KEY`

## Models
- All sub-agents: `gpt-4o-mini`
- `ManagerAgent`: `gpt-4o` (needs stronger reasoning for multi-step tool orchestration)

## Notes
- `.env` is one level up at `agents/.env` — `load_dotenv()` picks it up automatically
- Email: from `minhtanbuinguyen@gmail.com` → `tan.m.bui96@outlook.com`
- Traces visible at `https://platform.openai.com/traces/trace?trace_id=<id>`
- `search_context_size="low"` on `WebSearchTool` for cost efficiency
