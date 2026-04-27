# Engineering Team — CrewAI Project

A multi-agent CrewAI system that simulates a software engineering team. Given high-level requirements, it designs a full multi-module Python system, builds each module one at a time, writes unit tests per module, and assembles a Gradio UI.

## How to Run

```bash
cd engineering_team
uv run crewai run
```

Edit `requirements` in `src/engineering_team/main.py` before running. The system auto-determines module structure from the requirements.

## Key Files

| File | Purpose |
|------|---------|
| `src/engineering_team/main.py` | Entry point; set `requirements` here |
| `src/engineering_team/models.py` | Pydantic models: `ModuleSpec`, `SystemDesign` |
| `src/engineering_team/crew.py` | Three crew classes: `DesignCrew`, `ModuleCrew`, `FrontendCrew` |
| `src/engineering_team/config/design_agents.yaml` | `engineering_lead` agent config |
| `src/engineering_team/config/design_tasks.yaml` | `design_task` config |
| `src/engineering_team/config/module_agents.yaml` | `backend_engineer` + `test_engineer` agent configs |
| `src/engineering_team/config/module_tasks.yaml` | `code_task` + `test_task` configs |
| `src/engineering_team/config/frontend_agents.yaml` | `frontend_engineer` agent config |
| `src/engineering_team/config/frontend_tasks.yaml` | `frontend_task` config |
| `output/` | All generated files land here |
| `knowledge/user_preference.txt` | Optional user context injected into agents |

## Agents

| Agent | LLM | Role |
|-------|-----|------|
| `engineering_lead` | `openrouter/anthropic/claude-sonnet-4.6` | Designs the full multi-module system |
| `backend_engineer` | `openrouter/anthropic/claude-sonnet-4.6` | Implements one module at a time (code execution enabled) |
| `test_engineer` | `openrouter/anthropic/claude-sonnet-4.6` | Writes unit tests per module, runs them with pytest, fixes failures |
| `frontend_engineer` | `openrouter/anthropic/claude-sonnet-4.6` | Writes the Gradio UI in `app.py` |

## Three-Crew Pipeline

### Phase 1 — `DesignCrew`
`engineering_lead` analyses requirements and outputs a `SystemDesign` Pydantic object listing all modules to build (module name, class name, description, dependencies).

### Phase 2 — `ModuleCrew` × N (sequential)
For each module in the design, `main.py` kicks off a `ModuleCrew`:
- `backend_engineer` → `output/{module_name}` (raw Python)
- `test_engineer` → `output/test_{module_name}` (writes tests, runs them with pytest, fixes failures)
- Callback `log_module_built` fires after each task: logs progress + syntax-checks with `py_compile`

### Phase 3 — `FrontendCrew`
`main.py` reads all generated module files from disk, then kicks off `FrontendCrew`:
- `frontend_engineer` → `output/app.py` (receives full module source as `{modules_code}`)

## Dependencies & Environment

- Python `>=3.10, <3.14`; package manager: `uv`
- `crewai[tools]==1.14.2`, `gradio>=6.13.0`
- `.env` must contain `OPENAI_API_KEY` and an OpenRouter key

## Conventions

- Each crew has its own YAML pair (e.g. `design_agents.yaml` + `design_tasks.yaml`) — required because `@CrewBase` loads all tasks at init time and must only see agents/tasks for its own crew
- LLMs set per-agent via `llm:` in the respective `*_agents.yaml` file using `provider/model` format
- `design_task` uses both `output_pydantic=SystemDesign` (in-memory Pydantic object for `main.py`) and `output_file: output/system_design.json` (persisted to disk for inspection)
- All other tasks write raw Python via `output_file:` in `tasks.yaml` — no markdown fences
- `backend_engineer` and `test_engineer` have `allow_code_execution=True` (safe/Docker mode)
