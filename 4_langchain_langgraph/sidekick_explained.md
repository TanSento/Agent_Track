# sidekick.py — Details and Workflow

## Purpose

`Sidekick` is a personal-assistant agent built on LangGraph's `create_agent`, wrapped in a hand-rolled evaluator loop. Instead of trusting the worker's first answer, the class re-checks the answer against user-supplied success criteria and retries with feedback before handing control back to the user.

## Key pieces

**[EvaluatorOutput](sidekick.py#L38-L43)** — a Pydantic schema (`feedback`, `success_criteria_met`, `user_input_needed`) that a second LLM call returns, used to judge the worker's output.

**[TolerateToolErrors](sidekick.py#L59-L70)** — custom middleware that wraps tool execution; if a tool throws (e.g. browser flakes), it converts the exception into a `ToolMessage` fed back to the model instead of crashing the run.

**[Sidekick.setup()](sidekick.py#L88-L107)** builds two models:
- `self.worker` — a `create_agent` (gpt-5.4-mini) with tools from `get_all_tools` and a stack of middleware:
  - `TolerateToolErrors` — resilience to flaky tools
  - `TodoListMiddleware` — lets the worker maintain/share a plan (`self.todos`)
  - `PIIMiddleware("email")` and `PIIMiddleware("credit_card", apply_to_tool_results=True)` — redact PII in messages/tool results
  - `ModelCallLimitMiddleware(run_limit=30)` — cost/runaway guard
  - `HumanInTheLoopMiddleware` — pauses for approval before `send_push_notification` or `request_human_help`
  - `checkpointer=self.memory` (an `InMemorySaver`) — gives the graph persistent state keyed by `thread_id`
- `self.evaluator` — a plain `ChatOpenAI` with structured output bound to `EvaluatorOutput`, used only to judge, never to act.

## Workflow

**1. [run_turn()](sidekick.py#L131-L147)** — entry point for a new user message. Sets `self.task`/`self.success_criteria`, resets `attempts`/`todos`, builds the initial payload embedding the success criteria into the user message, then delegates to `_advance()`.

**2. [_advance()](sidekick.py#L154-L188)** — the core loop:
- Streams the worker graph via `astream(..., stream_mode="values")`, tracking `todos` from each intermediate state.
- If the stream ends in `__interrupt__` (the `HumanInTheLoopMiddleware` firing), it stores the pending action count, sets `self.paused = True`, and returns immediately with a message asking the user to approve.
- Otherwise it takes the worker's last message as `reply`, collects every tool name called (`tools_used`) by scanning all messages' `tool_calls`, increments `attempts`, and calls `self.evaluate(...)`.
- If the evaluator says success criteria are met, OR the worker needs user input, OR `attempts >= MAX_ATTEMPTS` (3) — it stops and returns both the reply and the evaluator's feedback to the caller.
- Otherwise, it builds a new payload telling the worker its last response fell short (with the evaluator's feedback) and loops back to `astream` again — same `thread_id`, so the checkpointer preserves conversation state across retries.

**3. [evaluate()](sidekick.py#L109-L129)** — builds a prompt containing the original task, success criteria, the ordered list of tools the worker actually called (as evidence, not just its claim), and its latest reply, then asks the structured-output evaluator LLM to judge it.

**4. [resume()](sidekick.py#L149-L152)** — called after a pause; it sends a `Command(resume={"decisions": [{"type": "approve"}] * self.pending_actions})` to approve every pending human-in-the-loop action, then re-enters `_advance()` to continue the same turn from where the graph left off.

**5. [cleanup()](sidekick.py#L190-L193)** — stops the MCP tool sessions (closing the browser, etc.) when the Sidekick is torn down.

## Notable design details

- The worker prompt ([WORKER_PROMPT](sidekick.py#L46-L56)) instructs the agent on browser etiquette (snapshot instead of clicking blindly, dismiss cookie banners itself, use `request_human_help` for logins/captchas/2FA) and gives a concrete Google Flights URL pattern for flight searches.
- The evaluator is deliberately decoupled from the worker's own self-report — it only trusts the tool-call list as evidence, guarding against the worker just claiming success without doing the work.
- Retry loop is capped by `MAX_ATTEMPTS = 3` to avoid infinite retries when the evaluator keeps rejecting.
- State persistence is entirely via `thread_id` = `self.sidekick_id`, so a single `Sidekick` instance maintains one continuous LangGraph thread across multiple turns and resumes.
