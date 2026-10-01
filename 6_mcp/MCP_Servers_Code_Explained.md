# How the MCP server code works

This explains [mcp_servers.py](backend/mcp_servers.py) and the files that start and use its servers.

## The main idea

`mcp_servers.py` is a **configuration file for connections**. It does not contain the trading tools themselves. It tells the app how to start six separate MCP server programs:

```text
Trading app
├─ Trader agent
│  ├─ Accounts server
│  ├─ Push server
│  └─ Market server
└─ Researcher agent, available to the Trader as a tool
   ├─ Fetch server
   ├─ Tavily search server
   └─ Memory server
```

Each line from the app to a server is its own **stdio connection**: the app starts a child process, sends MCP requests to its standard input, and reads replies from its standard output. **The servers do not form a network with one another.** The agents coordinate their tool calls.

## `mcp_servers.py`, piece by piece

### Imports and shared settings

At the top, `os` reads environment variables and `Path` finds the project directory. `load_dotenv(override=True)` loads values from `.env`, replacing an existing environment value if the file specifies the same name. `MCPServerStdio` is the client-side wrapper used to start and communicate with a server. `create_static_tool_filter` controls which of a server's tools an agent sees.

```python
PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
tavily_env = {"TAVILY_API_KEY": os.getenv("TAVILY_API_KEY")}
TIMEOUT = 120
```

Because the file is under `6_mcp/backend`, `PROJECT_DIR` resolves to `6_mcp`. The Tavily key is prepared for the search server. `TIMEOUT` is passed to each MCP client session.

### Choosing the market server

At [lines 13–23](backend/mcp_servers.py#L13-L23), the code chooses **one** market server based on whether `MASSIVE_API_KEY` exists:

- **Key present:** `uvx` starts Massive's `mcp_massive` package from the specified GitHub version and passes it the API key.
- **No key:** `uv run -m backend.market_server` starts this project's local market server, which supplies simulated prices.

This choice happens when `mcp_servers.py` is imported. `market_params` is a description of the command to run; assigning it does not yet start a process.

`cwd=PROJECT_DIR` on the local server means it starts inside `6_mcp`. That lets `backend.market_server` be imported as a module and keeps relative file paths anchored to the project directory.

### Building the Trader's three connections

[trader_mcp_servers()](backend/mcp_servers.py#L26) creates command configurations for:

1. `backend.accounts_server`
2. `backend.push_server`
3. The selected market server

It wraps each configuration in `MCPServerStdio(...)` and returns a list of three wrappers. `command` names the launcher, `args` are its command-line arguments, and `cwd` sets its starting directory.

### Building the Researcher's three connections

[researcher_mcp_servers(name)](backend/mcp_servers.py#L36) returns:

1. **Fetch**, started with `uvx mcp-server-fetch`, for retrieving web pages.
2. **Tavily**, started with `npx -y tavily-mcp@latest`, for web search. The tool filter exposes only `tavily_search` to the Researcher.
3. **Memory**, started with `npx -y mcp-memory-libsql`, for saving and recalling information. Its `LIBSQL_URL` contains the trader's name, such as `file:./memory/Warren.db`.

The `-y` flags stop `npx` from waiting for an installation confirmation on the same input stream used for MCP. The memory path is **relative to the memory server's working directory**; this configuration does not set a `cwd` for that server.

## Where the connections actually start

The returned `MCPServerStdio` wrappers become running connections in [Trader.run_with_mcp_servers()](backend/traders.py#L102). `AsyncExitStack` enters each server's async context. Entering the context starts the child process and establishes its MCP session. Leaving the context closes the connections and cleans up the processes.

Then [Trader.create_agent()](backend/traders.py#L74) wires them to agents:

- The Trader receives the **Accounts, Push, and Market** server list.
- The Researcher receives the **Fetch, Tavily, and Memory** server list.
- `researcher.as_tool(...)` makes the whole Researcher agent appear as one callable tool to the Trader.

Finally, `Runner.run(...)` runs the Trader. The Trader can call one of its MCP tools or call the Researcher tool; the Researcher can then call its own MCP tools and return a written result.

## What each local server does

| File | Tools or resources it provides |
| --- | --- |
| [accounts_server.py](backend/accounts_server.py) | Tools to get balance and holdings, buy and sell shares, and change strategy. It also exposes account report and strategy **resources**. |
| [push_server.py](backend/push_server.py) | A `push` tool that sends a message through Pushover. |
| [market_server.py](backend/market_server.py) | A `lookup_share_price` tool, used when the local market server is selected. |

`@mcp.tool()` makes a Python function callable as an MCP tool. `@mcp.resource(...)` makes data readable by URI. Each local server ends with `mcp.run(transport="stdio")`, which starts its MCP request loop when launched as a program.

The Accounts server calls methods on [Account](backend/accounts.py#L28). Those methods read and write the shared SQLite file `accounts.db` through [database.py](backend/database.py#L8). That shared file is how separate Accounts server processes see the same account state.

One subtle point: when `Account.buy_shares()` needs a price, it calls `market.get_share_price()` **as an ordinary Python function**. The Accounts server does not call the Market MCP server. Likewise, the Trader can independently ask the Market MCP server for a price.

## A complete run

[trading_floor.py](backend/trading_floor.py#L41) schedules four traders. When a trader runs, the sequence is roughly:

1. Start that trader's six MCP connections.
2. Use a **separate, short-lived Accounts MCP connection** in [accounts_client.py](backend/accounts_client.py#L13) to read the account report and strategy resources.
3. Give that information to the Trader agent.
4. The Trader asks its Researcher tool for news; the Researcher may search, fetch pages, and use memory.
5. The Trader may look up a price, buy or sell through Accounts, and send a notification through Push.
6. Close the six connections when the run finishes.

A practical code issue is visible in [push_server.py](backend/push_server.py#L24): `print(...)` writes to standard output, which stdio MCP reserves for protocol messages. That log should go to standard error or a logger configured for standard error.
