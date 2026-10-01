# Google ADK: Runners and Run Methods

Think of it this way:

- **Agent** = the worker
- **Runner** = the manager who runs the worker
- **Session** = one conversation
- **Event** = something that happened, such as text output or a tool call

## 1. `InMemoryRunner`

It stores conversations temporarily in RAM:

```python
runner = InMemoryRunner(agent=agent)

await runner.run_debug("My name is Tan.")
await runner.run_debug("What is my name?")
```

The agent may remember “Tan” while the notebook kernel is running. Restarting the kernel erases that memory.

Use it for learning, notebooks, and testing.

## 2. `Runner`

`Runner` lets you provide the storage services yourself:

```python
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=my_database_session_service,
)
```

A production app can use database-backed services so conversations survive restarts.

## 3. `run_debug()`: easy mode

```python
events = await runner.run_debug("Say hello in Vietnamese")
```

ADK handles session setup and prints debugging information automatically. Use it when experimenting.

## 4. `run_async()`: controlled mode

You create the session and handle every event:

```python
session = await runner.session_service.create_session(
    app_name=runner.app_name,
    user_id="tan",
)

async for event in runner.run_async(
    user_id="tan",
    session_id=session.id,
    new_message=types.UserContent("Say hello in Vietnamese"),
):
    print(event.author, event.content)
```

This lets you react to individual events:

```python
async for event in runner.run_async(...):
    for call in event.get_function_calls():
        print("Tool called:", call.name)

    if event.is_final_response():
        print("Final answer:", event.content.parts[0].text)
```

That is why the board example uses `run_async`: it can redraw the board immediately after `complete_task` runs.

## Quick choice

- Learning quickly → `InMemoryRunner` + `run_debug()`
- Need to inspect tool calls/events → `run_async()`
- Normal synchronous Python → `run()`
- Live audio/video → `run_live()`
- Persistent production storage → configurable `Runner` with persistent services
