# `MultiServerMCPClient` — Connecting to the Playwright MCP Server

```python
client = MultiServerMCPClient({
    "playwright": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest", "--isolated"],
    }
})

browser_tools = await client.get_tools()
print(f"Loaded {len(browser_tools)} browser tools:")
for t in browser_tools:
    print(" -", t.name)
```

This cell connects Python to the **Playwright MCP server** — a separately running Node.js program that controls a real browser — and discovers what tools it exposes.

---

## `MultiServerMCPClient({...})`

Creates a client that knows how to talk to one or more MCP servers. The dictionary key `"playwright"` is just a local name you give this server. The config inside tells it how to launch it:

| key | value | meaning |
|---|---|---|
| `"transport"` | `"stdio"` | communicate over standard input/output (the most common MCP transport) |
| `"command"` | `"npx"` | use Node's package runner to launch the server |
| `"args"` | `["-y", "@playwright/mcp@latest", "--isolated"]` | download and run the official Playwright MCP package; `--isolated` starts a fresh browser session each time |

The server doesn't start yet at this point — the client just holds the configuration.

---

## `await client.get_tools()`

This actually launches the Node process, connects to it over stdio, and asks it: *"what tools do you have?"* The MCP server responds with a list of 23 tools like `browser_navigate`, `browser_click`, `browser_take_screenshot`, etc. Because it starts a separate process and waits for the handshake, it must be `await`ed.

---

## What comes back

`browser_tools` is a list of LangChain-compatible tool objects — identical in shape to the `@tool`-decorated functions you've written before. From the agent's point of view they are indistinguishable from local Python tools. That's the whole point of MCP: tools that live in any language, in any separate process, plug into the agent loop exactly the same way.

```
Python process              Node.js process
┌──────────────────┐  stdio  ┌───────────────────────────┐
│ MultiServerMCP   │◄───────►│ @playwright/mcp server    │
│ client           │         │ (controls Chrome)          │
│                  │         │                           │
│ browser_tools    │         │ browser_navigate          │
│  = [tool1, ...]  │         │ browser_click             │
└──────────────────┘         │ browser_snapshot ...      │
                             └───────────────────────────┘
```
