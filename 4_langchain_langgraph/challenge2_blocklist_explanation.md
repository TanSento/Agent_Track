# Challenge 2: Blocking Browser Navigation With Middleware

This note explains the second exercise challenge from `3_lab3.ipynb`: writing middleware that refuses navigation to a site on a block list, then proving that the block works.

The goal is to let the browser agent use its normal Playwright MCP tools, except when it tries to navigate to a blocked site. In that case, the middleware stops the tool call before the browser opens the page and returns a tool result telling the agent that navigation was blocked.

## Full Code

```python
# Exercise challenge: block navigation to selected sites

from urllib.parse import urlparse
from langchain_core.messages import ToolMessage

blocked_sites = {"example.com"}

def is_blocked_url(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    hostname = hostname.removeprefix("www.")
    return hostname in blocked_sites

@wrap_tool_call
async def block_listed_navigation(request, handler):
    call = request.tool_call
    args = call.get("args", {})
    url = args.get("url", "")

    if call["name"] == "browser_navigate" and is_blocked_url(url):
        return ToolMessage(
            content=f"Navigation blocked: {url} is on the block list.",
            tool_call_id=call["id"],
            status="error",
        )

    return await handler(request)

blocked_browser_agent = create_agent(
    model="openai:gpt-5.5",
    tools=browser_tools,
    middleware=[block_listed_navigation],
    system_prompt="You are a web research assistant. If a tool says navigation was blocked, tell the user clearly and do not try to bypass it.",
)

blocked_result = await blocked_browser_agent.ainvoke({"messages": [{"role": "user", "content": "Open https://example.com and tell me what is on the page."}]})
print("Blocked-site test:")
print(blocked_result["messages"][-1].content)

allowed_result = await blocked_browser_agent.ainvoke({"messages": [{"role": "user", "content": "Now open https://news.ycombinator.com and tell me the title of the top story."}]})
print("\nAllowed-site test:")
print(allowed_result["messages"][-1].content)
```

## What The Middleware Does

The middleware sits between the agent and each tool call.

When the agent decides to use a tool, LangChain creates a tool-call request. The middleware receives that request before the tool actually runs. This gives us a chance to inspect the tool name and arguments.

If the tool call is safe, the middleware passes it onward:

```python
return await handler(request)
```

If the tool call is blocked, the middleware does not call `handler`. That means the real tool never runs.

Instead, it returns a `ToolMessage` that says the navigation was blocked:

```python
return ToolMessage(
    content=f"Navigation blocked: {url} is on the block list.",
    tool_call_id=call["id"],
    status="error",
)
```

This is how we short-circuit the tool call.

## Why We Import `urlparse`

```python
from urllib.parse import urlparse
```

The browser navigation tool receives a full URL, such as:

```text
https://example.com
https://www.example.com/page
https://news.ycombinator.com
```

We do not want to compare the whole URL string directly, because small differences like `https://`, `www.`, paths, or query strings would make matching unreliable.

Instead, `urlparse(url).hostname` extracts only the hostname:

```python
urlparse("https://www.example.com/page").hostname
```

That gives:

```text
www.example.com
```

Then this line removes a leading `www.`:

```python
hostname = hostname.removeprefix("www.")
```

So both `example.com` and `www.example.com` can be treated as the same site.

## The Block List

```python
blocked_sites = {"example.com"}
```

This is a Python set containing hostnames we want to block.

Using a set is a good fit because membership checks are simple and fast:

```python
hostname in blocked_sites
```

To block more sites, add them to the set:

```python
blocked_sites = {"example.com", "facebook.com", "x.com"}
```

## The URL Check Function

```python
def is_blocked_url(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    hostname = hostname.removeprefix("www.")
    return hostname in blocked_sites
```

This helper function keeps the middleware easier to read.

It does three things:

1. Extracts the hostname from the URL.
2. Normalizes the hostname by removing `www.`.
3. Returns `True` if the hostname is in `blocked_sites`.

The `or ""` part protects us if the URL is missing or malformed. If `urlparse(url).hostname` returns `None`, the code uses an empty string instead.

## Why The Middleware Is Async

The browser tools are loaded from the Playwright MCP server, and the notebook calls the browser agent with:

```python
await blocked_browser_agent.ainvoke(...)
```

Because the agent is invoked asynchronously, the middleware also needs an async implementation.

That is why the function is written as:

```python
@wrap_tool_call
async def block_listed_navigation(request, handler):
```

And why the allowed tool call is passed onward with:

```python
return await handler(request)
```

The first version used a synchronous middleware function:

```python
def block_listed_navigation(request, handler):
```

That caused this error:

```text
Asynchronous implementation of awrap_tool_call is not available.
```

The fix was to make the wrapped function async. LangChain then treats it as async tool-call middleware and can use it during `ainvoke`.

## Inspecting The Tool Call

Inside the middleware:

```python
call = request.tool_call
args = call.get("args", {})
url = args.get("url", "")
```

`request.tool_call` contains information about the tool the agent wants to run.

For browser navigation, it looks conceptually like this:

```python
{
    "name": "browser_navigate",
    "args": {"url": "https://example.com"},
    "id": "some-tool-call-id",
}
```

The important fields are:

- `name`: the tool name.
- `args`: the arguments being passed to that tool.
- `id`: the tool-call ID LangChain uses to match tool results back to tool requests.

## Blocking Only Navigation

```python
if call["name"] == "browser_navigate" and is_blocked_url(url):
```

This condition is intentionally specific.

It blocks only the `browser_navigate` tool, and only when the target URL is on the block list.

Other browser tools, such as screenshot, click, hover, or snapshot, are not blocked by this middleware. That keeps the rule focused on site navigation.

## Returning A `ToolMessage`

When the middleware blocks navigation, it returns:

```python
ToolMessage(
    content=f"Navigation blocked: {url} is on the block list.",
    tool_call_id=call["id"],
    status="error",
)
```

This is important because the agent expects tool calls to produce tool messages.

The `tool_call_id` connects this result to the original tool call. Without it, LangChain would not know which tool request this response belongs to.

The `status="error"` marks the tool result as an error result. The agent can then explain the problem to the user instead of pretending it visited the page.

## Creating The Agent

```python
blocked_browser_agent = create_agent(
    model="openai:gpt-5.5",
    tools=browser_tools,
    middleware=[block_listed_navigation],
    system_prompt="You are a web research assistant. If a tool says navigation was blocked, tell the user clearly and do not try to bypass it.",
)
```

This creates a normal browser agent, but with the new middleware installed.

The important line is:

```python
middleware=[block_listed_navigation]
```

That tells LangChain to run our middleware around every tool call.

The system prompt also matters. It tells the model what to do when a tool reports that navigation was blocked:

- Tell the user clearly.
- Do not try to bypass the block.

## Proving The Block Works

The first test asks the agent to open a blocked site:

```python
blocked_result = await blocked_browser_agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Open https://example.com and tell me what is on the page."
    }]
})
```

Because `example.com` is in `blocked_sites`, the middleware intercepts the `browser_navigate` call and returns a blocked `ToolMessage`.

Expected behavior:

- The browser should not navigate to `example.com`.
- The agent should say that navigation was blocked.

The second test asks the agent to open an allowed site:

```python
allowed_result = await blocked_browser_agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Now open https://news.ycombinator.com and tell me the title of the top story."
    }]
})
```

Because `news.ycombinator.com` is not in `blocked_sites`, the middleware allows the tool call to continue:

```python
return await handler(request)
```

Expected behavior:

- The browser should navigate to Hacker News.
- The agent should report the top story.

## The Big Idea

Middleware gives you a control point inside the agent loop.

In this challenge, we used middleware to enforce a navigation policy:

- Inspect each browser tool call.
- Detect attempts to navigate to blocked sites.
- Stop blocked navigation before the browser tool runs.
- Return a clear tool result to the agent.
- Allow normal browser behavior for unblocked sites.

This is the same general pattern you can use for other agent safety or control rules, such as requiring approval before purchases, blocking private domains, logging tool usage, retrying failed tools, or limiting expensive actions.
