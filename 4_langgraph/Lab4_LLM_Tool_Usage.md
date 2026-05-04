# How the LLM Uses Tools in lab4

Here's the full end-to-end flow across the notebook:

---

### Step 1 — Tools are created
```python
async_browser = create_async_playwright_browser(headless=False)
toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
tools = toolkit.get_tools()
```
`tools` is a list of callable Python functions (navigate, click, extract text, etc.) each with a name, description, and typed parameters.

---

### Step 2 — Tools are bound to the LLM
```python
worker_llm_with_tools = worker_llm.bind_tools(tools)
```
`.bind_tools()` serializes each tool's **schema** (name + description + parameter types) and sends it to the LLM on every call. The LLM never runs the tools itself — it just knows what's available.

---

### Step 3 — Worker calls the LLM
```python
response = worker_llm_with_tools.invoke(messages)
```
The LLM reads the conversation + tool schemas and decides: "Do I need a tool, or can I answer directly?"

- **If it needs a tool** → returns an `AIMessage` with `tool_calls` populated and `content = ""`
- **If it can answer** → returns an `AIMessage` with `content` filled and `tool_calls = []`

---

### Step 4 — Router checks the response
```python
def worker_router(state):
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    else:
        return "evaluator"
```
This inspects the last message. If the LLM requested a tool call, route to `"tools"`. Otherwise, send to `"evaluator"`.

---

### Step 5 — ToolNode executes the tool
```python
graph_builder.add_node("tools", ToolNode(tools=tools))
```
`ToolNode` reads `tool_calls` from the `AIMessage`, finds the matching Python function by name, runs it with the LLM's arguments, and wraps the result in a `ToolMessage` appended to state.

---

### Step 6 — Result goes back to worker
```python
graph_builder.add_edge("tools", "worker")
```
The `ToolMessage` result is now in the message history. The worker LLM sees it and decides what to do next — call another tool, or produce a final answer.

---

### The loop visualized

```
worker (LLM decides)
   │
   ├── tool_calls? ──▶ ToolNode (runs Python fn) ──▶ worker (sees result)
   │                        ↑___________________________|
   │
   └── no tool_calls ──▶ evaluator ──▶ END or retry worker
```

The key insight: **the LLM only picks which tool and with what arguments** — it never executes code. `ToolNode` is the actual executor, bridging the LLM's decision to real Python code running in your environment.
