# sidekick_Tan

A LangGraph-based AI sidekick with a multi-agent pipeline: clarifier → planner → task classifier → worker → verifier → evaluator.

## Structure

- `app.py` — Gradio UI entry point. Run this to launch the sidekick.
- `sidekick_tan.py` — Core `Sidekick` class. Defines all graph nodes, routing logic, and session management.
- `sidekick_tools_tan.py` — Tool definitions: Playwright browser, file management, web search (Serper), Wikipedia, Python REPL, sandbox inspection tools, push notifications.

## Running

```bash
uv run app.py
```

Run from anywhere — sandbox path is resolved absolutely to `4_langgraph/sandbox/`.

## Agent Graph

```
START
  │
  ▼
clarifier ──(ambiguous?)──▶ END (question shown to user)
  │ (clear request)
  ▼
planner
  │
  ▼
task_classifier  ("research" | "coding" | "writing" | "general")
  │
  ▼
worker (specialist prompt based on task_type)
  │
  ├──(tool calls?)──▶ tools ──▶ worker
  │
  ▼
verifier (reads sandbox files + runs .py scripts to get real stdout)
  │
  ├──(issues found?)──▶ worker (retry with verification_feedback)
  │
  ▼
evaluator ──(criteria not met?)──▶ worker (retry with feedback)
  │ (criteria met or user input needed)
  ▼
END
```

| Node | Role |
|---|---|
| clarifier | Asks one question if request is ambiguous, stops graph |
| planner | Breaks request into ordered subtasks |
| task_classifier | Labels task as research/coding/writing/general |
| worker | Executes using tools + specialist prompt |
| verifier | Runs sandbox scripts, compares actual output vs results files, flags inconsistencies |
| evaluator | Judges output against success criteria, retries or ends |

## Key Design Decisions

- **State** uses `TypedDict` (not Pydantic) — required by LangGraph for dict-based state merging and reducer support.
- **Structured outputs** use Pydantic `BaseModel` with `.with_structured_output()` — used by evaluator, planner, clarifier, task classifier, and verifier.
- **Sandbox path** is absolute (`__file__`-relative) so file tools always write to `4_langgraph/sandbox/` regardless of launch directory.
- **Sidekick instance** is stored in `gr.State` with a `delete_callback` to clean up Playwright on session end.
- **Clarifier loop prevention** — checks message history for prior `Question:` messages instead of relying on state fields (which reset between `run_superstep` calls).
- **Coding specialist** — instructs worker to use `print()` for output and the file writing tool to save results, not `open()` inside scripts (avoids REPL working directory mismatch).
- **Verifier ground truth** — verifier calls `read_sandbox_files()` and `run_sandbox_script()` directly (not via LLM tool call) to get real file contents and actual script stdout before asking LLM to compare against worker claims.
- **Verifier router** — routes directly back to worker when `verification_feedback` is set (issues found), bypassing evaluator; routes to evaluator only when sandbox checks pass. This prevents the evaluator's leniency from swallowing verified failures.
- **Recursion limit** is set to 50 in `run_superstep` config.

## Tools Available to the Agent

| Tool | Purpose |
|---|---|
| Playwright browser | Navigate and retrieve web pages |
| File management | Read/write/list/delete files in `sandbox/` |
| Web search (Serper) | Google search via Serper API |
| Wikipedia | Look up reference information |
| Python REPL | Execute Python code and capture output |
| `read_sandbox_files` | List and read all files currently in sandbox |
| `run_sandbox_script` | Run a Python script from sandbox and return its stdout |
| Push notification | Send alerts to user via Pushover |

## Environment Variables Required

- `OPENROUTER_API_KEY`
- `SERPER_API_KEY`
- `PUSHOVER_TOKEN`
- `PUSHOVER_USER`

## Planned Improvements

See `plans/2026-05-04-sidekick-improvements-1-4.md` for the full plan. Status:
1. Planning agent — done
2. Clarification agent — done
3. Task classifier — done
4. Verification agent — done
