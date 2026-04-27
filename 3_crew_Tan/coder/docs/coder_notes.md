# Coder Agent — Notes

## Does the coder agent use Docker?

**No — not in CrewAI 1.x.**

`code_execution_mode` and Docker support are **fully deprecated and no-ops** in CrewAI 1.x.
The source confirms:

```
Deprecated. CodeInterpreterTool is no longer available.
Use dedicated sandbox services instead.
```

So `code_execution_mode="safe"` in `crew.py` **does nothing** and can be safely removed.

---

## What actually executes the code now?

Without an explicit sandbox tool, the agent will either:

- Have the **LLM simulate** the output (reason through what the code would produce), or
- Run code **directly on your local machine** depending on what tools are attached

If you want **true isolated execution**, you need to explicitly add a sandbox service:

| Service | Notes |
|---|---|
| **E2B** | Cloud sandbox, integrates with CrewAI tools |
| **Modal** | Serverless compute, good for heavier workloads |

---

## Dead code to clean up

The following parameters are deprecated in CrewAI 1.x and have no effect:

```python
# These do nothing — safe to remove
code_execution_mode="safe",
```

`allow_code_execution=True`, `max_execution_time`, and `max_retry_limit` may still be
respected depending on which tools are attached, but `code_execution_mode` specifically
is a no-op.

---

## VIRTUAL_ENV warning

```
warning: `VIRTUAL_ENV=.../agents/.venv` does not match the project environment path `.venv`
and will be ignored
```

**This is harmless.** It means:

- You have a **parent** venv activated (`agents/.venv`)
- But `uv` detects the sub-project has its **own** `.venv` and uses that instead

`uv` does the right thing automatically. Your crew runs with the correct environment.

**To suppress the warning**, deactivate the parent venv first:

```bash
deactivate
crewai run
```

Or to force using the currently active venv:

```bash
uv run --active crewai run
```
