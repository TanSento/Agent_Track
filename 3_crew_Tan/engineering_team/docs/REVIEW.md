# Engineering Team — Implementation Review

## What Was Built

The original system was a single CrewAI crew that took a fixed module name and class name from `main.py` and generated one Python module, one Gradio UI, and one test file per run. Every agent worked on the same single module.

The refactored system replaces that with a three-phase pipeline driven by Pydantic structured output and task callbacks. The engineering lead now designs an entire multi-module system from requirements alone. `main.py` reads that design and loops over each module, building and testing them one at a time. The frontend engineer receives the full source code of all generated modules before writing the UI.

---

## Files Changed

| File | Action | Summary |
|------|--------|---------|
| `src/engineering_team/models.py` | Created | Pydantic models for structured design output |
| `src/engineering_team/config/design_agents.yaml` | Created | `engineering_lead` config (split from monolithic agents.yaml) |
| `src/engineering_team/config/design_tasks.yaml` | Created | `design_task` config |
| `src/engineering_team/config/module_agents.yaml` | Created | `backend_engineer` + `test_engineer` configs |
| `src/engineering_team/config/module_tasks.yaml` | Created | `code_task` + `test_task` configs |
| `src/engineering_team/config/frontend_agents.yaml` | Created | `frontend_engineer` config |
| `src/engineering_team/config/frontend_tasks.yaml` | Created | `frontend_task` config |
| `src/engineering_team/crew.py` | Rewritten | Three `@CrewBase` classes, each pointing to its own YAML pair |
| `src/engineering_team/main.py` | Rewritten | Three-phase orchestration with module loop |
| `CLAUDE.md` | Updated | Reflects new architecture |
| `PLAN.md` | Created | Step-by-step implementation checklist |

---

## Pydantic Models — `models.py`

Two models drive the entire pipeline:

```python
class ModuleSpec(BaseModel):
    module_name: str        # filename, e.g. "accounts.py"
    class_name: str         # primary class, e.g. "Account"
    description: str        # what this module does
    dependencies: list[str] # other module filenames it imports from

class SystemDesign(BaseModel):
    system_overview: str    # high-level description of the full system
    modules: list[ModuleSpec]
```

`SystemDesign` is what the engineering lead produces. It is the single source of truth that `main.py` uses to decide what modules to build, in what order, and with what context. Without this structured output, `main.py` would have no machine-readable way to loop over the design.

`ModuleSpec.dependencies` is particularly important — it tells the backend engineer exactly which other modules to import from, ensuring inter-module imports are correct rather than guessed.

---

## Agents — `agents.yaml`

### `engineering_lead` (Claude Sonnet 4.6)
Redesigned to think at the system level. Its goal instructs it to decompose requirements into well-defined modules with single responsibilities and minimal coupling. The old language ("1 python module", "self-contained") was removed entirely since those constraints no longer apply.

Only receives `{requirements}`. Produces the `SystemDesign` JSON.

### `backend_engineer` (Claude Sonnet 4.6 — all agents)
Now explicitly builds *one piece of a larger system*. Its goal includes:
- `{module_name}` / `{class_name}` — what to build
- `{description}` — the module's specific responsibility
- `{dependencies}` — which modules to import from
- `{system_overview}` — full system context so it understands how this module fits in
- `{requirements}` — original requirements for reference

The old "completely self-contained" language was removed — modules are expected to import from each other.

### `frontend_engineer` (Claude Sonnet 4.6)
Now receives the full picture of the system:
- `{system_overview}` — what the system does overall
- `{module_list}` — a formatted list of all modules with class names and descriptions
- `{modules_code}` — the actual source code of every generated module
- `{requirements}` — original requirements

Receiving `{modules_code}` is the key improvement: the frontend engineer can now read real method signatures and class APIs rather than inferring them from descriptions alone.

### `test_engineer` (Claude Sonnet 4.6)
Receives the same module-level context as `backend_engineer`, plus sees the actual code via `context: - code_task` within the same `ModuleCrew` run. The backstory instructs it to mock dependencies appropriately so tests remain isolated. The task description explicitly instructs it to run the tests with pytest after writing them and fix any failures — made possible by `allow_code_execution=True` on the agent.

---

## Tasks — `tasks.yaml`

### `design_task`
Instructs the engineering lead to output a JSON object matching `SystemDesign` exactly. The schema is embedded directly in the task description so the LLM knows the precise field names and structure required. Output is saved to `output/system_design.json` via `output_file` for inspection, and simultaneously parsed into a `SystemDesign` Pydantic object via `output_pydantic` for use by `main.py`. Both can coexist — `output_file` writes the raw text to disk while `output_pydantic` structures it in memory.

### `code_task`
Receives all six context variables. Critically, no `context:` dependency on `design_task` — because `code_task` now lives in `ModuleCrew`, a completely separate crew from `DesignCrew`. The design context is passed in as plain input variables instead. Output written to `output/{module_name}` as raw Python.

### `test_task`
Has `context: - code_task` because both live in `ModuleCrew` — so the test engineer's prompt is automatically augmented with the backend engineer's code output. This is why the tests are grounded in the real implementation rather than just the description.

### `frontend_task`
No `context:` (different crew from `ModuleCrew`). Instead, `main.py` reads the generated files from disk after the module loop and passes the combined source as `{modules_code}`. This achieves the same effect — the frontend engineer sees real code — without requiring task-level context wiring across separate crews.

---

## Crews — `crew.py`

### `DesignCrew`
One agent, one task. The task is configured with `output_pydantic=SystemDesign`, which instructs CrewAI to parse the LLM's JSON output into a `SystemDesign` instance. This instance is returned as `result.pydantic` and read directly by `main.py`.

### `ModuleCrew`
Two agents, two tasks, run sequentially. Both `code_task` and `test_task` are wired with the `log_module_built` callback.

The `log_module_built` callback does two things:
1. Prints a progress line with the first 80 characters of the task description
2. If the output looks like Python (starts with `def`, `class`, `import`, or `from`), writes it to a temp file and runs `py_compile.compile()` to catch syntax errors immediately — before the next task starts

`backend_engineer` and `test_engineer` both have `allow_code_execution=True` in safe/Docker mode with a 4-minute timeout and 5 retries, giving them room to run and validate their own code if needed.

### `FrontendCrew`
One agent, one task. No callback, no `output_pydantic`. Output written directly to `output/app.py` via `output_file`.

---

## Orchestration — `main.py`

```
run()
 ├─ DesignCrew().crew().kickoff({"requirements": ...})
 │    └─ returns result.pydantic → SystemDesign
 │
 ├─ for spec in system_design.modules:          # sequential
 │    └─ ModuleCrew().crew().kickoff({
 │         module_name, class_name, description,
 │         dependencies, system_overview, requirements
 │       })
 │
 ├─ _read_generated_modules(system_design)
 │    └─ reads output/{module_name} for each spec → combined source string
 │
 └─ FrontendCrew().crew().kickoff({
      requirements, system_overview, module_list, modules_code
    })
```

`OUTPUT_DIR` is resolved relative to `main.py`'s location so it works regardless of where the process is launched from.

`_read_generated_modules` warns (but does not crash) if an expected file is missing, so a partial run still produces a frontend even if one module failed.

The module loop is strictly sequential — each `ModuleCrew` completes fully (code + tests) before the next module starts. This matters when later modules depend on earlier ones, since the dependency's file will already exist on disk.

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| Per-crew YAML config files (`design_*`, `module_*`, `frontend_*`) | `@CrewBase` resolves all task agents at init time — if tasks from other crews are present, it raises `KeyError`. Each crew must only see its own agents and tasks |
| `test_engineer` runs pytest after writing tests | `allow_code_execution=True` gives the agent the ability; the task description explicitly instructs it to run and fix failures before finishing |
| All agents use `openrouter/anthropic/claude-sonnet-4.6` | Unified model choice after testing — avoids cross-provider compatibility issues |
| `output_pydantic=SystemDesign` on `design_task` | Gives `main.py` a typed, machine-readable design object to loop over — no string parsing required |
| `output_file: output/system_design.json` on `design_task` | Persists the full system design to disk for inspection; compatible with `output_pydantic` since they serve different purposes (disk vs memory) |
| Separate `DesignCrew`, `ModuleCrew`, `FrontendCrew` | Each crew has a focused, independent concern; `ModuleCrew` can be kicked off N times with different inputs |
| `context: - code_task` on `test_task` | Test engineer sees the actual implementation, not just the description |
| `{modules_code}` passed to `FrontendCrew` | Frontend engineer reads real class APIs and method signatures instead of guessing from descriptions |
| Sequential module loop | Ensures earlier modules exist on disk before later ones (which may import from them) are built |
| `log_module_built` callback with `py_compile` | Catches syntax errors immediately after generation, before the next task starts |
| `dependencies` as comma-separated string | Simple to pass as a template variable; backend and test engineers can parse it naturally in their prompts |

---

## Workflow Diagram

```
main.py
  │
  ├─ DesignCrew
  │    └─ engineering_lead
  │         input:  {requirements}
  │         output: SystemDesign (Pydantic) ──────────────────────┐
  │                                                               │
  │         ┌────────────────────────────────────────────────────┘
  │         │  for each ModuleSpec in SystemDesign.modules
  ├─ ModuleCrew × N  (sequential)
  │    ├─ backend_engineer
  │    │    input:  {module_name, class_name, description,
  │    │             dependencies, system_overview, requirements}
  │    │    output: output/{module_name}  ──────────────┐ (context)
  │    │    callback: log_module_built (syntax check)   │
  │    │                                                │
  │    └─ test_engineer                                 │
  │         input:  same + code_task output ────────────┘
  │         output: output/test_{module_name}
  │         callback: log_module_built (syntax check)
  │
  │    (main.py reads all output/{module_name} files from disk)
  │
  └─ FrontendCrew
       └─ frontend_engineer
            input:  {system_overview, module_list,
                     modules_code, requirements}
            output: output/app.py
```
---

## Verification Checklist

1. `uv run crewai run` completes without errors
2. Console prints Phase 1 / Phase 2 / Phase 3 headers with module names
3. `output/system_design.json` exists and contains valid JSON matching the `SystemDesign` schema
4. `output/` contains one `.py` file and one `test_*.py` per module listed in the design
5. `output/app.py` exists and imports from all generated modules
6. Callback lines `[callback] syntax OK` appear for each generated file
7. `uv run python output/app.py` launches the Gradio UI without import errors

