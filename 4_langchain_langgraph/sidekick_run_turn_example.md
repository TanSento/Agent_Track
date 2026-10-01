# Example: run_turn() through a pause and resume

A concrete trace through `sidekick.py`, using a task that triggers the approval pause.

**Setup:** UI calls
```python
history = await sidekick.run_turn(
    "Remind me to call the dentist tomorrow at 9am — send me a push notification",
    "I should receive a push notification confirming the reminder",
    []
)
```

## 1. run_turn()

Sets `self.task`, `self.success_criteria`, resets `attempts=0`. Builds:
```python
payload = {"messages": [{"role": "user", "content":
    "Remind me to call the dentist tomorrow at 9am — send me a push notification\n\n"
    "The success criteria for this task are: I should receive a push notification..."}]}
```
Calls `self._advance(payload, history + [user turn])`.

## 2. First pass through _advance()

The worker decides to call `send_push_notification(message="Reminder: call the dentist tomorrow at 9am")`. Because that tool is in `interrupt_on` ([sidekick.py:101-103](sidekick.py#L101-L103)), LangGraph halts before running it. The streamed `result` now contains `"__interrupt__"`, so:

```python
actions = result["__interrupt__"][0].value["action_requests"]
# [{"action": "send_push_notification",
#   "args": {"message": "Reminder: call the dentist tomorrow at 9am"},
#   "description": "Tool execution requires approval: send_push_notification with message='Reminder: call the dentist tomorrow at 9am'"}]

self.paused = True
self.pending_actions = 1
```

Function returns immediately:
```python
[
    {"role": "user", "content": "Remind me to call the dentist..."},
    {"role": "assistant", "content": "Waiting for your approval:\nTool execution requires approval: send_push_notification with message='Reminder: call the dentist tomorrow at 9am'"},
]
```
`run_turn()` returns this to the UI. `sidekick.paused` is `True`, so the UI shows an Approve button instead of a text box.

## 3. User clicks Approve → UI calls

```python
history = await sidekick.resume(history)
```

## 4. resume()

```python
payload = Command(resume={"decisions": [{"type": "approve"}] * 1})
return await self._advance(payload, history)
```

## 5. Second pass through _advance()

Same `thread_id`, so LangGraph resumes the *same paused graph* exactly where it stopped — it now actually runs `send_push_notification`, the worker sees the tool result and produces a final answer. This time `result` has no `"__interrupt__"`:
```python
self.paused = False
reply = "I've sent you a push notification reminding you to call the dentist tomorrow at 9am."
tools_used = ["send_push_notification"]
self.attempts = 1
verdict = await self.evaluate(...)   # success_criteria_met = True
```
Since `verdict.success_criteria_met` is `True`, it returns the final history:
```python
[
    {"role": "user", "content": "Remind me to call the dentist..."},
    {"role": "assistant", "content": "Waiting for your approval:\n..."},
    {"role": "assistant", "content": "I've sent you a push notification reminding you to call the dentist tomorrow at 9am."},
    {"role": "assistant", "content": "Evaluator: Push notification was sent as requested; criteria met."},
]
```

That's the whole cycle: `run_turn` → pause → UI approves → `resume` → same thread continues → evaluator checks → done.
