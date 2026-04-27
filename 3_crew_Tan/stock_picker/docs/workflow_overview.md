# Stock Picker — Workflow Overview

## Diagram

```
Manager (gpt-4o) — orchestrates everything via Process.hierarchical
     │
     ├──► Task 1: find_trending_companies
     │         Agent: trending_company_finder (gpt-4o-mini)
     │         Tool:  SerperDevTool (web search)
     │         Out:   TrendingCompanyList (Pydantic) → output/trending_companies.json
     │
     ├──► Task 2: research_trending_companies
     │         Agent: financial_researcher (gpt-4o-mini)
     │         Tool:  SerperDevTool (web search)
     │         Context: ← Task 1 output (company list)
     │         Out:   TrendingCompanyResearchList (Pydantic) → output/research_report.json
     │
     └──► Task 3: pick_best_company
               Agent: stock_picker (gpt-4o-mini)
               Tool:  PushNotificationTool (Pushover API)
               Context: ← Task 2 output (research report)
               Out:   Free text → output/decision.md
```

---

## How data flows

1. **Task 1 → Task 2** via `context: [find_trending_companies]` — the researcher receives
   the full company list as input context.
2. **Task 2 → Task 3** via `context: [research_trending_companies]` — the stock picker
   receives the research report as input context.
3. Tasks are **structured by Pydantic models** for Tasks 1 & 2 (`output_pydantic=`),
   enforcing a schema. Task 3 is free-form markdown.

---

## Manager's role

Since `process=Process.hierarchical`, the **Manager** (`gpt-4o`) doesn't do any research
itself — it acts as a supervisor that delegates each task to the right agent, checks the
output quality, and can re-delegate if needed. It uses the stronger `gpt-4o` specifically
because delegation decisions require higher reasoning than the sub-tasks.

---

## Memory's role (`memory=True`)

Each agent can **recall past runs** — this is why both `trending_company_finder` and
`stock_picker` have the instruction *"Don't pick the same company twice."* Memory is what
makes that stick across multiple `crewai run` executions.

> See `docs/crewai_memory_notes.md` for how to customise memory scoring weights.

---

## Context wiring — YAML vs Python

You never need to declare `context=` in `crew.py` when using YAML configs.
When you do `config=self.tasks_config['task_name']`, CrewAI reads **all fields** from
the YAML into the Task — including `context`. The string task names are resolved to actual
Task objects at runtime.

For example, in `tasks.yaml`:

```yaml
research_trending_companies:
  context:
    - find_trending_companies   # resolved by CrewAI to the actual Task object at runtime
```

### When would you declare `context=` in Python?

Only if you are **not** using a YAML config for that task, or want to **override/extend**
what the YAML already declares:

```python
# Pure Python approach (no YAML for this task)
@task
def research_trending_companies(self) -> Task:
    return Task(
        description="...",
        expected_output="...",
        agent=self.financial_researcher(),
        context=[self.find_trending_companies()],  # must be explicit here
    )

# Or to ADD context on top of what the YAML already defines
@task
def pick_best_company(self) -> Task:
    return Task(
        config=self.tasks_config['pick_best_company'],
        context=[self.some_extra_task()],  # merges with yaml context
    )
```

**TL;DR:** `config=self.tasks_config[...]` loads everything from YAML — description,
agent assignment, context wiring, output file — all in one shot. No need to repeat it
in Python.
