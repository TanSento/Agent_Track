# sidekick_tan.py — Code Explainer

## Overview

This file defines the `Sidekick` class — the brain of the agent. It builds and runs a LangGraph state machine where each node is a specialised agent (clarifier, planner, classifier, worker, verifier, evaluator). The graph wires them together with conditional routing logic so the agent can loop, retry, and stop at the right time.

---

## Imports and Dependencies

```python
from sidekick_tools_tan import playwright_tools, other_tools, read_sandbox_files, run_sandbox_script
```

This file depends directly on `sidekick_tools_tan.py` for:
- `playwright_tools()` — browser + browser tools
- `other_tools()` — all other LangChain tools (search, file, REPL, etc.)
- `read_sandbox_files()` — called directly in the verifier to read sandbox file contents
- `run_sandbox_script()` — called directly in the verifier to execute Python scripts and get real stdout

The tools are used in two ways:
1. **Worker**: tools are bound to the LLM via `bind_tools()`, so the LLM can choose to call them
2. **Verifier**: `read_sandbox_files` and `run_sandbox_script` are called as plain Python functions (not via LLM), to get ground truth

---

## State

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]
    clarification_question: Optional[str]
    task_type: Optional[str]
    verification_feedback: Optional[str]
```

`State` is a `TypedDict` — required by LangGraph because it merges state dicts between nodes using reducers. `messages` uses the `add_messages` reducer, which appends new messages rather than overwriting.

Each field is written by a specific node:

| Field | Written by |
|---|---|
| `messages` | every node (appended via reducer) |
| `success_criteria` | set externally in `run_superstep` |
| `task_plan` | `planner` |
| `clarification_question` | `clarifier` |
| `task_type` | `task_classifier` |
| `verification_feedback` | `verifier` |
| `feedback_on_work` | `evaluator` |
| `success_criteria_met` | `evaluator` |
| `user_input_needed` | `evaluator` or `clarifier` |

---

## Pydantic Output Models

Each structured-output node has a Pydantic model that the LLM must return. LangGraph uses `.with_structured_output(Model)` to force the LLM to return valid JSON matching the schema.

| Model | Used by | Key fields |
|---|---|---|
| `ClarifierOutput` | clarifier | `needs_clarification`, `question` |
| `PlannerOutput` | planner | `task_plan` |
| `TaskClassifierOutput` | task_classifier | `task_type` |
| `VerifierOutput` | verifier | `issues_found`, `issues` |
| `EvaluatorOutput` | evaluator | `feedback`, `success_criteria_met`, `user_input_needed` |

The worker does **not** use structured output — it uses `bind_tools()` instead so the LLM can freely call tools or return a plain text response.

---

## The Sidekick Class

### `__init__`

Sets up empty placeholders for all LLM instances, tools, the compiled graph, browser, and Playwright. Also generates a unique `sidekick_id` (UUID) used as the `thread_id` for `MemorySaver` — this allows conversation history to persist across multiple `run_superstep` calls within the same session.

### `setup` (async)

Must be called before the graph is used. It:
1. Calls `playwright_tools()` to launch a Chromium browser and get browser tools
2. Calls `other_tools()` to get all remaining tools
3. Creates one `ChatOpenAI` instance per node, each configured with `with_structured_output()` or `bind_tools()`
4. Calls `build_graph()` to compile the LangGraph

All LLMs point to OpenRouter via a custom `base_url`.

---

## Graph Nodes

### `clarifier`

**Purpose:** Decide whether the user's request is clear enough to proceed, or if one clarifying question is needed first.

**Loop prevention:** Before doing anything, it scans `state["messages"]` for any prior `AIMessage` starting with `"Question:"`. If found, it skips — preventing infinite clarification loops when the user provides a follow-up answer and the graph re-enters this node.

**Output:** If ambiguous, appends a `"Question: ..."` message and sets `clarification_question` + `user_input_needed`. If clear, returns `clarification_question: None`.

**Router (`clarifier_router`):** Returns `"END"` if `clarification_question` is set (stops graph, shows question to user), otherwise routes to `"planner"`.

---

### `planner`

**Purpose:** Break the user's request into an ordered, numbered list of concrete subtasks before any execution begins.

**Why:** Without a planner, the worker tries to figure out sequencing on the fly and often writes summaries before running scripts, causing fabricated output.

**Output:** Sets `task_plan` in state — a numbered list string the worker reads and follows strictly.

---

### `task_classifier`

**Purpose:** Read the task plan and classify the primary type of work as one of `research`, `coding`, `writing`, or `general`.

**Output:** Sets `task_type` in state. This is read by the worker to select its specialist prompt.

---

### `worker`

**Purpose:** Execute the task using tools. The core action node.

**Specialist prompts:** Based on `task_type`, the worker gets a different system prompt:
- `research` — prioritise web search and browser, verify facts before reporting
- `coding` — write scripts, run via REPL, use `print()` for output, save results via file writing tool (not `open()` inside scripts)
- `writing` — produce structured documents from already-gathered data only
- `general` — generic helpful assistant

**System message injection:** The worker finds any existing `SystemMessage` in `state["messages"]` and replaces its content. If none exists, it prepends one. This means the system prompt is always current even on retries.

**Feedback injection:** If `feedback_on_work` (from evaluator) or `verification_feedback` (from verifier) is in state, it is appended to the system message so the worker knows what to fix.

**Output:** Returns `{"messages": [response]}` — just the LLM's response appended to history.

**Router (`worker_router`):**
- If the response has `tool_calls` → route to `"tools"` (let ToolNode execute them, then return to worker)
- Otherwise → route to `"verifier"` (worker is done, check its output)

---

### `tools`

A LangGraph `ToolNode` — prebuilt node that receives tool call requests from the worker's last message, executes the matching tool, and appends the tool result as a `ToolMessage`. Always routes back to `worker`.

---

### `verifier`

**Purpose:** Before the evaluator sees the worker's output, independently verify it using ground truth from the filesystem — not from the conversation history.

**How it works:**
1. Calls `read_sandbox_files()` directly — gets full contents of every file in sandbox
2. Scans sandbox for `.py` files, calls `run_sandbox_script(filename)` on each — gets real stdout
3. Passes both to the LLM with the worker's final response and asks: do the worker's claims match the actual script output and file contents?

**Why not just read the conversation?** The worker could claim to have saved certain numbers without actually doing so. The verifier bypasses the conversation entirely and checks the filesystem directly.

**Output:**
- If issues found: sets `verification_feedback` with specific description, appends a message to history
- If no issues: returns `verification_feedback: None`

**Router (`verifier_router`):** Always returns `"evaluator"` — the verifier never directly retries the worker. If issues were found, the evaluator will send the worker back, and the worker picks up `verification_feedback` from state.

---

### `evaluator`

**Purpose:** Judge whether the worker's final response meets the success criteria.

**Output:** Returns `EvaluatorOutput` with:
- `feedback` — written into `feedback_on_work` state field
- `success_criteria_met` — True if done
- `user_input_needed` — True if worker is stuck or has a question

**Router (`route_based_on_evaluation`):**
- `success_criteria_met` or `user_input_needed` → `"END"`
- Otherwise → `"worker"` (retry with feedback)

---

## `format_conversation`

A helper used by both verifier and evaluator to format `state["messages"]` into a readable string. Skips `SystemMessage` and `ToolMessage`, shows `HumanMessage` as `User:` and `AIMessage` as `Assistant:`.

---

## `build_graph`

Assembles the LangGraph:

```
START → clarifier → (END | planner) → task_classifier → worker
worker → (tools → worker | verifier) → evaluator → (END | worker)
```

Compiled with `MemorySaver` as the checkpointer, so state is persisted between `run_superstep` calls using `thread_id = sidekick_id`.

---

## `run_superstep`

Called once per user message from the Gradio UI (`app.py`). Initialises full state with all fields reset to `None`/`False` (except `messages` and `success_criteria`), then invokes the compiled graph.

After the graph completes:
- `result["messages"][-2]` — the worker's final answer (second to last)
- `result["messages"][-1]` — the evaluator's feedback (last)

Both are returned to the UI as chat history entries.

**Note:** `messages` uses `add_messages` reducer, so passing the same message in a new `run_superstep` will append to history — not replace it. This is intentional for multi-turn conversations.

---

## `cleanup`

Called when the Gradio session ends (via `delete_callback` on `gr.State`). Closes the Playwright browser and stops the Playwright process gracefully, handling both async and sync event loop contexts.
