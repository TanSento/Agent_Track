# Sidekick pause → approve → resume flow

How a human-approval interrupt travels from `sidekick.py`'s worker graph out to the Gradio UI in `app.py`, and back in as a resumed run.

## What triggers a pause

`HumanInTheLoopMiddleware` is configured in [Sidekick.setup()](sidekick.py#L101-L103) to interrupt only two tools:

```python
HumanInTheLoopMiddleware(
    interrupt_on={"send_push_notification": True, "request_human_help": True}
)
```

Every other tool (browser, sandbox filesystem, search, Wikipedia) runs immediately. Only when the worker calls one of these two does LangGraph halt the graph *before* running it, and add a `"__interrupt__"` key to the streamed state.

## Reading the pending actions

In [_advance()](sidekick.py#L154-L188):

```python
if "__interrupt__" in result:
    actions = result["__interrupt__"][0].value["action_requests"]
    self.paused = True
    self.pending_actions = len(actions)
    described = "\n".join(action["description"] for action in actions)
    return history + [{"role": "assistant", "content": f"Waiting for your approval:\n{described}"}]
```

- `result["__interrupt__"]` — a list of `Interrupt` objects; `[0]` is the first (sidekick.py only ever looks at one).
- `.value` — the interrupt's payload dict: `{"action_requests": [...], "review_configs": [...]}`.
- `["action_requests"]` — one entry per pending tool call, each shaped roughly like `{"action": <tool name>, "args": {...}, "description": <human-readable string>}`.

The loop returns immediately here — it does not keep streaming — so the turn stops mid-task until something calls `resume()`.

## Example trace

```python
history = await sidekick.run_turn(
    "Remind me to call the dentist tomorrow at 9am — send me a push notification",
    "I should receive a push notification confirming the reminder",
    []
)
```

1. **run_turn()** builds the initial payload and calls `_advance()`.
2. Worker decides to call `send_push_notification(message="Reminder: call the dentist tomorrow at 9am")`. Because that tool is gated, LangGraph pauses before running it.
3. `_advance()` sets `self.paused = True`, `self.pending_actions = 1`, and returns:
   ```python
   [
       {"role": "user", "content": "Remind me to call the dentist..."},
       {"role": "assistant", "content": "Waiting for your approval:\nTool execution requires approval: send_push_notification with message='Reminder: call the dentist tomorrow at 9am'"},
   ]
   ```
4. UI shows this message and, because `sidekick.paused` is `True`, reveals the Approve button.
5. User clicks Approve → UI calls `await sidekick.resume(history)`.
6. **resume()** sends `Command(resume={"decisions": [{"type": "approve"}] * 1})` into the *same* `thread_id`, so LangGraph resumes the exact paused graph rather than starting over.
7. The tool actually runs, the worker produces a final reply, no `"__interrupt__"` this time, so `_advance()` proceeds to the evaluator and returns the final answer + feedback.

## UI wiring (app.py)

Three pieces connect the mechanism above to a button click, all in [app.py](app.py):

**1. Pause becomes visible** — [process_message()](app.py#L38-L42):
```python
async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_turn(message, success_criteria, history)
    return results, gr.update(visible=sidekick.paused), sidekick
```
Reads `sidekick.paused` right after `run_turn()` returns and uses it to show/hide the Approve button.

**2. The button** — [app.py:85](app.py#L85), [app.py:98](app.py#L98):
```python
approve_button = gr.Button("Approve and continue", visible=False, elem_id="approve-button")
...
approve_button.click(approve, [sidekick, chatbot], [chatbot, approve_button, sidekick])
```
Starts hidden; only shown when step 1 sets `visible=True`.

**3. Click calls resume()** — [approve()](app.py#L45-L47):
```python
async def approve(sidekick, history):
    results = await sidekick.resume(history)
    return results, gr.update(visible=sidekick.paused), sidekick
```
Reads `sidekick.paused` again afterward, since a resumed run can hit *another* interrupt (e.g. two gated tool calls back to back) and needs the button to stay visible.

**Division of responsibility:** `sidekick.py` owns the pause/resume *mechanism* (`paused`, `pending_actions`, `resume()`); `app.py` owns the *UI trigger* — reading `paused` to show the button, and calling `resume()` when it's clicked.
