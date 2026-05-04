# sidekick_Tan

A LangGraph-based AI sidekick with a multi-agent worker/evaluator loop, browser automation, web search, file management, Python execution, and push notifications.

## Structure

- `app.py` — Gradio UI entry point. Run this to launch the sidekick.
- `sidekick_tan.py` — Core `Sidekick` class. Defines the LangGraph graph, worker node, evaluator node, and session management.
- `sidekick_tools_tan.py` — Tool definitions: Playwright browser, file management, web search (Serper), Wikipedia, Python REPL, push notifications.

## Running

```bash
uv run app.py
```

Run from anywhere — sandbox path is resolved absolutely to `4_langgraph/sandbox/`.

## Key Design Decisions

- **State** uses `TypedDict` (not Pydantic) — required by LangGraph for dict-based state merging and reducer support.
- **EvaluatorOutput** uses Pydantic `BaseModel` — for structured LLM output parsing via `.with_structured_output()`.
- **Sandbox path** is absolute (`__file__`-relative) so file tools always write to `4_langgraph/sandbox/` regardless of launch directory.
- **Sidekick instance** is stored in `gr.State` with a `delete_callback` to clean up Playwright on session end.
- **Worker/evaluator loop** — worker executes tasks, evaluator judges output against success criteria, retries with feedback if criteria not met.

## Tools Available to the Agent

| Tool | Purpose |
|---|---|
| Playwright browser | Navigate and retrieve web pages |
| File management | Read/write/list/delete files in `sandbox/` |
| Web search (Serper) | Google search via Serper API |
| Wikipedia | Look up reference information |
| Python REPL | Execute Python code and capture output |
| Push notification | Send alerts to user via Pushover |

## Environment Variables Required

- `OPENROUTER_API_KEY`
- `SERPER_API_KEY`
- `PUSHOVER_TOKEN`
- `PUSHOVER_USER`

## Planned Improvements

See `sidekick_improvements.md` for the full list. Key items:
1. Planning agent for task decomposition
2. Clarification questions before starting
3. Specialist sub-agents by task type
4. Verification agent to validate output before evaluation
5. Persistent memory across sessions (`SqliteSaver`)
6. MD to PDF conversion tool
