# MCP stdio servers, simply explained

An **MCP server** is a separate program that gives an AI agent tools, such as reading files or fetching a web page. The agent asks the server to use a tool, and the server sends back the result.

## What does “stdio” mean?

**Stdio** is a way for two programs on the same computer to talk. The agent starts the MCP server as a child process and connects to it through pipes:

```text
Agent / MCP client                  MCP server
        request  ────────────────> stdin
        result   <──────────────── stdout
                                   stderr ──> logs and errors
```

The requests and results follow MCP's JSON-RPC message format. The pipes are just how those messages travel. `stdout` must contain MCP messages, so the server should write logs to `stderr`.

## How do you start one?

This Python configuration starts the filesystem MCP server:

```python
files_params = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path],
}
```

It is like running this command in a terminal:

```text
npx -y @modelcontextprotocol/server-filesystem /absolute/path/to/sandbox
```

| Piece | Meaning |
| --- | --- |
| `command` | The program used to launch the server. |
| `args` | The words passed to that program, in order. |
| `npx` | Runs a JavaScript package. `uvx` plays a similar role for Python packages. |
| `-y` | Lets `npx` proceed without asking an interactive installation question. |
| `@modelcontextprotocol/server-filesystem` | The server package to run. |
| `sandbox_path` | The directory that this filesystem server is allowed to access. |

Use an **absolute path** for `sandbox_path` so it points to the intended directory regardless of where the server starts. The filesystem server checks this path when it starts and refuses access outside the allowed directory.

## How is this different from an HTTP server?

With **stdio**, you provide a command. The client starts a local server and talks to it through pipes. With **HTTP**, you provide a URL and connect to a server over the network.

Stdio describes the connection between the agent and server. It does not prevent the server itself from accessing the internet; for example, a fetch server may make web requests. `npx` or `uvx` may also download a package before starting it.

**In one sentence:** `command` and `args` start a local tool server, and the agent exchanges MCP messages with it through standard input and output.
