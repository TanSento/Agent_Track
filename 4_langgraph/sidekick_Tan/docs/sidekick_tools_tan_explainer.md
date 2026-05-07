# sidekick_tools_tan.py — Code Explainer

## Overview

This file defines all the tools the agent can use. It is imported by `sidekick_tan.py` and serves two purposes:

1. **Provides LangChain `Tool` objects** that are bound to the worker LLM — the LLM sees these tools and can choose to call them during task execution
2. **Provides plain Python functions** (`read_sandbox_files`, `run_sandbox_script`) that `sidekick_tan.py` calls directly in the verifier node — bypassing the LLM entirely to get ground truth

---

## How This File Connects to sidekick_tan.py

`sidekick_tan.py` imports four things from this file:

```python
from sidekick_tools_tan import playwright_tools, other_tools, read_sandbox_files, run_sandbox_script
```

| Import | Used where | How |
|---|---|---|
| `playwright_tools()` | `Sidekick.setup()` | Launches browser, returns tools + browser + playwright handles |
| `other_tools()` | `Sidekick.setup()` | Returns all remaining tools as a list |
| `read_sandbox_files()` | `Sidekick.verifier()` | Called directly as a Python function — no LLM involved |
| `run_sandbox_script()` | `Sidekick.verifier()` | Called directly as a Python function — no LLM involved |

In `setup()`, both tool lists are combined:
```python
self.tools, self.browser, self.playwright = await playwright_tools()
self.tools += await other_tools()
```

The full `self.tools` list is then:
- Bound to the worker LLM: `worker_llm.bind_tools(self.tools)` — so the worker can call any tool
- Passed to `ToolNode(tools=self.tools)` — so LangGraph knows how to execute tool calls

---

## Module-Level Setup

```python
load_dotenv(find_dotenv(), override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()
```

These run once when the module is imported. `find_dotenv()` walks up the directory tree to find the `.env` file — this ensures it works regardless of where `app.py` is launched from. `serper` is initialised once and reused across all search calls.

---

## Functions

### `playwright_tools()` — async

```python
async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright
```

Launches a real Chromium browser instance (visible, not headless) and wraps it in a `PlayWrightBrowserToolkit`. Returns three things:
- `tools` — LangChain browser tools (navigate, click, extract text, etc.)
- `browser` — the raw Playwright browser handle, kept so it can be closed on session end
- `playwright` — the Playwright process handle, also needed for cleanup

**Why return browser and playwright?** Playwright must be explicitly stopped — if not, the browser process keeps running after the session ends. `sidekick_tan.py` stores both handles and closes them in `Sidekick.cleanup()`.

---

### `push(text: str)` — sync

```python
def push(text: str):
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "success"
```

Sends a push notification to the user's phone via the Pushover API. Wrapped as a `Tool` in `other_tools()` so the agent can call it when it wants to alert the user.

---

### `get_file_tools()` — sync

```python
def get_file_tools():
    sandbox_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sandbox")
    toolkit = FileManagementToolkit(root_dir=sandbox_path)
    return toolkit.get_tools()
```

Creates a `FileManagementToolkit` scoped to `4_langgraph/sandbox/`. The path is resolved using `__file__` (absolute path of this file) so it always points to the correct sandbox directory regardless of where the app was launched from.

`FileManagementToolkit` provides: read file, write file, list directory, delete file — all locked to `sandbox/`. The agent cannot escape this directory.

**Important constraint:** When the agent uses these tools, filenames must be plain names like `"results.txt"` — not `"sandbox/results.txt"` — because the toolkit is already rooted at sandbox.

---

### `_sandbox_path()` — sync

```python
def _sandbox_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sandbox")
```

Shared helper that returns the absolute path to `4_langgraph/sandbox/`. Used internally by `read_sandbox_files()` and `run_sandbox_script()` so the path logic is defined in one place.

---

### `read_sandbox_files()` — sync

```python
def read_sandbox_files() -> str:
    sandbox = _sandbox_path()
    files = [f for f in os.listdir(sandbox) if os.path.isfile(os.path.join(sandbox, f))]
    ...
    return "\n\n".join(parts)
```

Reads every file in sandbox and returns their full contents as a formatted string:
```
--- filename.txt ---
<file contents>

--- script.py ---
<file contents>
```

**Two uses:**
1. Called directly in `Sidekick.verifier()` to get ground truth for the LLM comparison
2. Exposed as a `Tool` (`read_sandbox_files`) so the worker LLM can also inspect sandbox contents itself

---

### `run_sandbox_script(filename: str)` — sync

```python
def run_sandbox_script(filename: str) -> str:
    sandbox = _sandbox_path()
    script_path = os.path.join(sandbox, filename)
    result = subprocess.run(["python", script_path], capture_output=True, text=True, timeout=30)
    return result.stdout or "(no output)"
```

Runs a named Python script from sandbox using `subprocess` and returns its stdout. This is deterministic — it actually executes the code rather than asking the LLM to reason about what it would output.

**Two uses:**
1. Called directly in `Sidekick.verifier()` — the verifier runs every `.py` file in sandbox and passes real stdout to the LLM for comparison against results files
2. Exposed as a `Tool` (`run_sandbox_script`) so the worker can also call it to self-verify before finishing

**Why subprocess instead of the Python REPL tool?** The REPL tool is stateful and managed by LangChain. Here we need a clean, direct execution from the filesystem to get honest output — no state carried over from previous REPL calls.

---

### `other_tools()` — async

```python
async def other_tools():
    ...
    return file_tools + [push_tool, tool_search, python_repl, wiki_tool, sandbox_read_tool, sandbox_run_tool]
```

Assembles all non-browser tools and returns them as a list. Each tool is a LangChain `Tool` with a name, function, and description — the description is what the LLM reads to decide when to use it.

| Tool name | Function | Description shown to LLM |
|---|---|---|
| file tools (4x) | `FileManagementToolkit` | read/write/list/delete files in sandbox |
| `send_push_notification` | `push()` | send a push notification |
| `search` | `serper.run()` | Google search via Serper API |
| `python_repl` | `PythonREPLTool` | execute Python code and capture output |
| `wikipedia` | `WikipediaQueryRun` | look up reference information |
| `read_sandbox_files` | `read_sandbox_files()` | list and read all files in sandbox |
| `run_sandbox_script` | `run_sandbox_script()` | run a Python script from sandbox |

**Note:** `read_sandbox_files` uses a lambda `lambda _: read_sandbox_files()` because the `Tool` interface passes an argument even when the function takes none.

---

## How the Two Files Work Together

```
sidekick_tools_tan.py                    sidekick_tan.py
─────────────────────                    ───────────────
playwright_tools()      ──────────────▶  Sidekick.setup()
                                           self.tools = browser_tools + other_tools
                                           worker_llm.bind_tools(self.tools)
                                           ToolNode(tools=self.tools)

other_tools()           ──────────────▶  Sidekick.setup()

read_sandbox_files()    ──────────────▶  Sidekick.verifier()  [direct Python call]
                        ──────────────▶  worker LLM           [via Tool binding]

run_sandbox_script()    ──────────────▶  Sidekick.verifier()  [direct Python call]
                        ──────────────▶  worker LLM           [via Tool binding]
```

The key design point: `read_sandbox_files` and `run_sandbox_script` exist in `sidekick_tools_tan.py` as plain functions first, then are *also* wrapped as Tools. This means the verifier can call them with guaranteed, deterministic results — while the worker LLM can also call them optionally to self-check its own work.
