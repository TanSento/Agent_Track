# MCP: Transports and Server Config

Notes on what `{"command": ..., "args": [...]}` actually does, and how a stdio MCP server is wired up.

---

## Protocol vs. transport

MCP is two separate things, and it helps to keep them apart.

**The protocol** is the message format. It is **JSON-RPC**: you send a request like

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
```

and a JSON reply comes back. This never changes.

**The transport** is how those bytes physically travel between the two programs. This is swappable.

Think of a letter: the letter itself is the protocol, and postal service vs. email is the transport.

| Transport | Where the server runs | What you configure |
|---|---|---|
| **stdio** | A local subprocess on your machine | A command to run: `{"command": "uvx", "args": [...]}` |
| **Streamable HTTP** | Somewhere else, over the network | A URL: `{"url": "https://mcp.context7.com/mcp"}` |

---

## What "stdio" means

Every process gets three channels when it starts. These are the **standard streams**:

- **stdin** (0) — where it reads input
- **stdout** (1) — where it writes normal output
- **stderr** (2) — where it writes errors and log noise

Run a program in a terminal and stdin is your keyboard, stdout and stderr are your screen. But a **parent process** can hijack those and wire them to itself instead. That is exactly what `MCPServerStdio` does.

```
  your notebook                         mcp-server-fetch
  (the MCP client)                      (the MCP server, a subprocess)

  writes request  --------> stdin  --+
                                     +--  server does the work
  reads response  <-------- stdout --+

                  <-------- stderr ---->  /dev/null (silenced in the lab)
```

So **stdio transport** means: launch the server as a **child process**, write JSON-RPC down its stdin, read replies off its stdout. No network, no port, no localhost, no HTTP. The two processes are joined by an in-memory **pipe** the operating system provides.

Roles, in MCP's vocabulary: your notebook is the **host** and the **client**; the program it launches is the **server**. The server runs on your machine, as you, with your permissions, and dies when the `async with` block exits.

**Why stdout is sacred:** stdout is now a data channel, not a display. If the server printed a startup banner there, the client would try to parse `Starting fetch server v1.2...` as JSON and choke. That is why well-behaved servers send all logging to stderr.

---

## npm and npx (and their Python twins)

You already know the Python versions of these:

| Python | JavaScript | What it does |
|---|---|---|
| PyPI | **npm** | The **registry** — the warehouse where people publish packages |
| `uv add requests` | `npm install x` | Download it and **keep** it in your project |
| `uvx some-tool` | **`npx some-tool`** | Download it, **run it once**, throw it away |

That is the whole thing. `npm` is the warehouse (and the tool that installs from it). `npx` runs a package straight out of the warehouse without adding it to your project.

Both appear in lab 1:

```python
fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}                                    # a Python server
files_params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", path]} # a JavaScript server
```

Both lines say the same thing: go get this thing and run it. MCP does not care what language a server is written in. That is much of the point.

**Why run-and-discard rather than install?** These servers are not part of your project. You never `import` them or call their functions. They are separate programs your code starts, talks to over a pipe, and shuts down. Installing them permanently would just be clutter.

---

## Reading a params dict

```python
files_params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]}
```

is literally the shell command:

```
npx -y @modelcontextprotocol/server-filesystem /Users/.../6_mcp/sandbox
```

| Part | Belongs to | Meaning |
|---|---|---|
| `npx` | — | The launcher |
| `-y` | **npx** | Auto-answer "yes" to the install prompt |
| `@modelcontextprotocol/server-filesystem` | **npx** | The package name. `@modelcontextprotocol/` is a **scope**, a namespace in the registry marking the official reference servers |
| `sandbox_path` | **the server** | An argument to the server itself |

The split in that last column is the part people miss. `npx` stops paying attention after the package name; everything after it is handed to the server process as its own **argv** (its command-line arguments).

**So `command` + `args` is the entire config surface for a stdio server.** Anything server-specific — which folders, which API key, which mode — arrives as command-line arguments or **environment variables** (the optional `env` key in the params dict), exactly as if you had typed it in a terminal.

### Why `-y` matters

The first time `npx` runs a package it has not cached, it asks:

```
Need to install the following packages:
  @modelcontextprotocol/server-filesystem
Ok to proceed? (y)
```

and waits for you to type `y` on stdin. But nobody is there to type, and stdin is the MCP transport — the client is writing JSON-RPC into it, not answers to prompts. The prompt is never satisfied and the cell hangs until `client_session_timeout_seconds` runs out.

`-y` means "assume yes" and skips the question.

Lab 1 gets away with omitting `-y` for playwright only because the cell above it already ran `npx -y playwright@latest screenshot`, so the package was cached and npx had nothing to ask.

### `sandbox_path` is a security boundary

The filesystem server could read and write anything, so it takes its **allowed directories** as arguments and refuses everything outside them. Pass one directory and that is the whole universe it can see. An agent that decides to read `~/.ssh/id_rsa` gets an access-denied from the server rather than a file.

Two consequences:

1. `os.path.abspath` is doing real work. The server resolves paths against its own working directory, not the notebook's, so a relative path would scope it somewhere unintended.
2. The server validates those directories at startup and **exits** if none are reachable, rather than run unscoped. Correct behaviour for a security boundary, and the cause of the failure below.

---