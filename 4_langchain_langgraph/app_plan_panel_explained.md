# How the plan panel in app.py is built

The plan panel is built from three pieces working together: a Gradio component, an HTML-rendering function, and a polling timer that keeps it live *without* going through the slow chat callback.

## 1. The component itself — [app.py:77](app.py#L77)

```python
todos_panel = gr.HTML(render_todos([]), elem_id="plan-panel")
```

It's just a `gr.HTML` block sitting in a `Column` next to the `Chatbot` ([app.py:74-77](app.py#L74-L77)), seeded with an empty-state render. `elem_id="plan-panel"` is what lets `styles.py` target it with CSS.

## 2. Turning todos into HTML — [render_todos()](app.py#L21-L29)

```python
def render_todos(todos):
    if not todos:
        items = '<div class="placeholder">The Sidekick will write its plan here as it works</div>'
    else:
        items = "<ul>" + "".join(
            f'<li class="{todo["status"]}"><span class="mark"></span>{html.escape(todo["content"])}</li>'
            for todo in todos
        ) + "</ul>"
    return f"<h3>Plan</h3>{items}"
```

Each todo becomes an `<li>` whose `class` is its status (`pending` / `in_progress` / `completed`), with a little `<span class="mark">` dot. In [styles.py:61-64](styles.py#L61-L64), that class drives the dot's color — pale blue outline for pending, purple for in-progress, gold-filled for completed (and completed text fades to grey).

## 3. What actually refreshes it — [watch_todos()](app.py#L50-L54) + the Timer

```python
timer = gr.Timer(1)
...
timer.tick(watch_todos, [sidekick], [todos_panel], show_progress="hidden")
```

```python
def watch_todos(sidekick):
    return render_todos(sidekick.todos) if sidekick else render_todos([])
```

This is the key design choice, and it's explained in the docstring: `todos_panel` is deliberately **not** an output of `process_message`. If it were, Gradio would treat it as locked/pending for the entire duration of `sidekick.run_turn(...)` (which can run for minutes across browser actions and retries), so nothing would visibly update until the whole turn finished. Instead, a `gr.Timer` ticking once a second independently calls `watch_todos`, which just reads whatever `sidekick.todos` currently holds — the same list that `_advance()` is updating live in `sidekick.py` on every streamed graph step. So the panel effectively polls the agent's in-progress plan once a second while `process_message` runs in the background.
