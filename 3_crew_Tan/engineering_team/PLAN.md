# Engineering Team — Multi-Module Improvement Plan

## Context

Currently the crew generates a single Python module per run. The goal is to let the engineering lead design a full system broken into multiple modules/classes, then build each module one at a time, and finally assemble a frontend that ties them together.

Key mechanisms:
- **Pydantic structured output** (`output_pydantic`) on the design task so `main.py` can read a machine-readable list of modules to build
- **Task callbacks** on code/test tasks for progress tracking and optional post-processing (e.g. syntax validation)
- **Python loop** in `main.py` to drive per-module builds using the structured design output

---

## Architecture Overview

Three crew classes replace the current single crew:

```
DesignCrew       → SystemDesign (Pydantic)
  └─ for each module:
       ModuleCrew  → output/{module_name}  (via output_file + callback)
                  → output/test_{module_name}
FrontendCrew     → output/app.py
```

---

## Implementation Steps

- [x] **Step 1** — Create `src/engineering_team/models.py` with `ModuleSpec` and `SystemDesign` Pydantic models
- [x] **Step 2** — Update `src/engineering_team/config/agents.yaml`: revise ALL four agents
  - `engineering_lead` ✓ done
  - `backend_engineer` ✓ done — removed "self-contained"/"1 python module"; added `{description}`, `{dependencies}`, `{system_overview}`
  - `frontend_engineer` ✓ done — added `{module_list}`, `{system_overview}`
  - `test_engineer` ✓ done — added `{description}`, `{dependencies}`, `{system_overview}`
- [x] **Step 3** — Update `src/engineering_team/config/tasks.yaml`: revise all four tasks for multi-module context and add new template variables
- [x] **Step 4** — Rewrite `src/engineering_team/crew.py`: replace `EngineeringTeam` with `DesignCrew`, `ModuleCrew`, `FrontendCrew`; add `log_module_built` callback
- [x] **Step 5** — Rewrite `src/engineering_team/main.py`: orchestrate the three crews sequentially with a loop over `SystemDesign.modules`
- [x] **Step 6** — Update `CLAUDE.md` to reflect the new three-crew architecture

---

## Files to Create

### `src/engineering_team/models.py`
```python
from pydantic import BaseModel

class ModuleSpec(BaseModel):
    module_name: str        # e.g. "accounts.py"
    class_name: str         # e.g. "Account"
    description: str        # what this module does
    dependencies: list[str] # other module filenames it imports from

class SystemDesign(BaseModel):
    system_overview: str
    modules: list[ModuleSpec]
```

---

## Files to Modify

### `src/engineering_team/config/agents.yaml`

Update all four agents:
- `engineering_lead` — designs the whole system; remove single-module variables
- `backend_engineer` — remove "self-contained"/"1 python module" language; add `{description}`, `{dependencies}`, `{system_overview}` to goal so it knows what it's building and what to import
- `frontend_engineer` — reference `{module_list}` and `{system_overview}` in goal
- `test_engineer` — reference `{description}`, `{dependencies}`, `{system_overview}` in goal

### `src/engineering_team/config/tasks.yaml`

**`design_task`** — instruct engineering_lead to decompose requirements into a list of modules. Add to description:
> "Break the system into self-contained modules, each with one primary class. Identify dependencies between modules."

Remove `output_file` from design_task (output_pydantic handles it in Python).

**`code_task`** — add new template variables to description: `{description}`, `{dependencies}`, `{system_overview}`. These give the backend_engineer context about the module it's building and what to import.

**`test_task`** — same additions: `{description}`, `{dependencies}`, `{system_overview}`.

**`frontend_task`** — replace `{module_name}` with `{module_list}` (a formatted list of all modules) and add `{system_overview}`.

### `src/engineering_team/crew.py`

Replace single `EngineeringTeam` class with three `@CrewBase` classes:

**`DesignCrew`**
- Agents: `engineering_lead`
- Tasks: `design_task` with `output_pydantic=SystemDesign`
- No callback needed; structured output flows directly to `main.py`

**`ModuleCrew`**
- Agents: `backend_engineer`, `test_engineer`
- Tasks: `code_task`, `test_task`
- Both tasks get `callback=log_module_built` — a simple function that prints progress and optionally runs `py_compile` to validate syntax
- `output_file` stays in YAML (raw Python written directly to disk)

**`FrontendCrew`**
- Agents: `frontend_engineer`
- Tasks: `frontend_task`
- No change to output mechanism

Callback shape (in `crew.py`):
```python
from crewai.tasks import TaskOutput
import py_compile, tempfile, pathlib

def log_module_built(output: TaskOutput):
    print(f"[callback] module written: {output.description[:60]}")
    # optional: write to tmp file and py_compile for syntax check
```

### `src/engineering_team/main.py`

New orchestration:
```python
def run():
    # 1. Design
    design_result = DesignCrew().crew().kickoff(inputs={"requirements": requirements})
    system_design: SystemDesign = design_result.pydantic

    # 2. Build each module
    for spec in system_design.modules:
        ModuleCrew().crew().kickoff(inputs={
            "requirements": requirements,
            "module_name": spec.module_name,
            "class_name": spec.class_name,
            "description": spec.description,
            "dependencies": ", ".join(spec.dependencies) or "none",
            "system_overview": system_design.system_overview,
        })

    # 3. Frontend
    module_list = "\n".join(
        f"- {s.module_name} ({s.class_name}): {s.description}"
        for s in system_design.modules
    )
    FrontendCrew().crew().kickoff(inputs={
        "requirements": requirements,
        "system_overview": system_design.system_overview,
        "module_list": module_list,
    })
```

---

## Verification

1. Run `uv run crewai run` from `engineering_team/`
2. Check that console output lists multiple modules from the design phase
3. Confirm one file per module appears in `output/`
4. Confirm `output/app.py` imports from all generated modules
5. Confirm `output/test_*.py` files exist for each module
6. Run `uv run python output/app.py` to validate the Gradio UI launches
