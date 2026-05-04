# app.py — Code Explanation

## `setup()`
Runs once when the UI first loads. Creates a `Sidekick` instance, calls `await sidekick.setup()` (which initializes playwright, tools, LLMs, and builds the graph), then returns it to be stored in Gradio's `gr.State`.

---

## `process_message(sidekick, message, success_criteria, history)`
The main callback — runs every time the user submits a request. Calls `sidekick.run_superstep()` which runs the full LangGraph worker→evaluator loop, then returns the updated chat history *and* the sidekick object back into state. Returning `sidekick` back is important — it keeps the same stateful object alive across interactions.

---

## `reset()`
Tears down the current sidekick and creates a brand new one from scratch (new playwright browser, new graph, new memory). Returns empty strings for the text boxes, `None` to wipe the chat, and the fresh sidekick into state.

---

## `free_resources(sidekick)`
A cleanup callback registered with `gr.State(delete_callback=free_resources)`. Gradio calls this automatically when a session ends (browser tab closed, timeout, etc.), closing the playwright browser and stopping the playwright process so resources aren't leaked.

---

## `gr.State(delete_callback=free_resources)`
Invisible per-session store that holds the `Sidekick` instance. Each browser tab gets its own isolated `Sidekick`. The `delete_callback` hooks into Gradio's session lifecycle so cleanup happens automatically.

---

## Event Wiring

| Event | Trigger | Function |
|---|---|---|
| `ui.load(...)` | Page first loads | `setup` → initializes sidekick |
| `message.submit(...)` | Enter in message box | `process_message` |
| `success_criteria.submit(...)` | Enter in criteria box | `process_message` |
| `go_button.click(...)` | Click "Go!" | `process_message` |
| `reset_button.click(...)` | Click "Reset" | `reset` → new sidekick |

All three submit/click paths for `process_message` are identical — just convenience so the user can trigger with Enter from either text box or by clicking.

---

## `ui.launch(inbrowser=True)`
Starts the Gradio web server and automatically opens a browser tab pointing to it.

---

## Note: Import Source
`app.py` imports from `sidekick` (no `_tan`):

```python
from sidekick import Sidekick
```

This points to Ed's original `sidekick.py`, not `sidekick_tan.py`. Both files have the `setup()` method, but `app.py` currently uses Ed's version.
