# Callbacks Explained

## What is a callback in CrewAI?

A **callback** is a function you attach to a `Task`. CrewAI automatically calls it the moment that task finishes, passing the task's output as the argument. Think of it as a "post-task hook".

---

## The callback function: `log_module_built`

```python
def log_module_built(output) -> None:
    """Callback fired after each code or test task completes."""
    print(f"[callback] task complete: {output.description[:80].strip()}")
    raw = output.raw or ""
    if raw.strip().startswith(("def ", "class ", "import ", "from ")):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(raw)
            tmp_path = f.name
        try:
            py_compile.compile(tmp_path, doraise=True)
            print(f"[callback] syntax OK")
        except py_compile.PyCompileError as e:
            print(f"[callback] syntax error: {e}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
```

**Step by step:**

**Step 1 — Receive the task output**
When the task finishes, CrewAI calls `log_module_built(output)`. The `output` object is a `TaskOutput` with fields like `.raw` (the agent's raw text response) and `.description` (the task's description string).

**Step 2 — Log task completion**
```python
print(f"[callback] task complete: {output.description[:80].strip()}")
```
Prints the first 80 characters of the task description so you can see which task just finished in the terminal logs.

**Step 3 — Get the raw output**
```python
raw = output.raw or ""
```
Extracts the agent's raw text output (the Python code the agent wrote). The `or ""` is a safety guard — if the agent returned nothing, it defaults to an empty string instead of `None`.

**Step 4 — Check if it looks like Python code**
```python
if raw.strip().startswith(("def ", "class ", "import ", "from ")):
```
A quick heuristic: real Python modules typically start with one of these keywords. This guards against trying to syntax-check something that isn't code (e.g. if the agent accidentally wrapped the output in markdown).

**Step 5 — Write to a temp file**
```python
with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
    f.write(raw)
    tmp_path = f.name
```
Writes the code to a temporary `.py` file on disk. `delete=False` is needed because `py_compile` needs to open the file by path after this `with` block closes it.

**Step 6 — Compile/syntax-check the code**
```python
py_compile.compile(tmp_path, doraise=True)
print(f"[callback] syntax OK")
```
`py_compile.compile()` is Python's built-in syntax checker — it parses the file exactly like the interpreter would, but doesn't run it. `doraise=True` means it raises an exception on syntax error instead of silently failing.

**Step 7 — Handle syntax errors**
```python
except py_compile.PyCompileError as e:
    print(f"[callback] syntax error: {e}")
```
If the code has a syntax error, it catches and prints it. Note: it just **logs** the error — it doesn't stop the crew or retry. This is a diagnostic tool, not an enforcer.

**Step 8 — Clean up the temp file**
```python
finally:
    Path(tmp_path).unlink(missing_ok=True)
```
Always deletes the temp file regardless of whether compilation succeeded or failed. `missing_ok=True` prevents a crash if the file was already deleted.

---

## Where the callback is attached

```python
@task
def code_task(self) -> Task:
    return Task(
        config=self.tasks_config["code_task"],
        callback=log_module_built,   # <-- attached here
    )

@task
def test_task(self) -> Task:
    return Task(
        config=self.tasks_config["test_task"],
        callback=log_module_built,   # <-- and here
    )
```

The **same callback** is reused on both `code_task` and `test_task` inside `ModuleCrew`. So every time the backend engineer writes a module, and every time the test engineer writes a test file, the syntax check runs automatically.

`DesignCrew` and `FrontendCrew` have **no callback** — the design task output is validated via Pydantic (`output_pydantic=SystemDesign`), and the frontend task outputs `app.py` which isn't syntax-checked here.

---

## Summary flow

```
ModuleCrew runs...
  → backend_engineer finishes code_task
      → CrewAI calls log_module_built(output)
          → logs task name
          → writes code to /tmp/xyz.py
          → py_compile checks syntax
          → prints "syntax OK" or "syntax error: ..."
          → deletes /tmp/xyz.py
  → test_engineer finishes test_task
      → CrewAI calls log_module_built(output)
          → same process repeats
```

---

## What Callbacks Really Do in This Workflow

The workflow runs 7 modules × 2 tasks each = **14 task executions** in `ModuleCrew`. Every single one fires `log_module_built` the moment it finishes.

### 1. Real-time progress signal

Without the callback, you'd stare at the terminal with no idea if the agent is still thinking or has finished. The callback immediately prints:
```
[callback] task complete: Write the Python module account.py containing class Account...
```
So you always know which module just finished being written or tested.

### 2. Instant syntax validator

The moment `backend_engineer` finishes writing, say, `trading_service.py`, the callback:
- takes the raw code
- compiles it with Python's own parser
- tells you right away: `[callback] syntax OK` or `[callback] syntax error: ...`

This means you don't have to wait until Phase 3 (frontend build) or runtime to discover the backend engineer produced broken Python.

### 3. It does NOT block or fix anything

The callback is **read-only/diagnostic only**. If it finds a syntax error, it just prints it and moves on. The crew continues regardless — it doesn't retry the task, alert the agent, or stop the pipeline.

### What it doesn't cover

- `DesignCrew` has no callback — but uses `output_pydantic=SystemDesign` which is a stronger guarantee (Pydantic validates the JSON structure)
- `FrontendCrew` has no callback — so `app.py` is never syntax-checked automatically
- The callback only checks **syntax**, not whether the logic is correct or the imports will resolve at runtime

### In short

It's a **lightweight quality monitor** — gives you instant feedback in the terminal as each of the 14 code/test tasks complete, so you can spot broken output early without waiting for the full run to finish.
