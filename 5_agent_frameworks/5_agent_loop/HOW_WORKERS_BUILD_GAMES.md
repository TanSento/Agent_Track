# How Each Worker Builds Its Game

Each worker builds its game through an inner agent-and-tool loop. The Python or TypeScript worker does not contain game code or a fixed game template. Its LLM invents the game and writes the three files through filesystem tools.

## Overall worker flow

```text
Orchestrator creates a goal in board.sqlite
        ↓
Orchestrator launches the selected worker subprocess
        ↓
Worker receives <goal_id> and <board_path>
        ↓
Worker claims the goal
        ↓
Worker agent calls show_todos() to read the assignment
        ↓
Worker agent calls plan_steps() to create a checklist
        ↓
Worker agent uses filesystem MCP tools to write the game
        ↓
Worker reads the files back to verify them
        ↓
Worker calls complete_task() for its steps and goal
        ↓
Worker process exits
```

## 1. The orchestrator creates the game assignment

When the orchestrator calls:

```python
launch_worker(
    framework="strands",
    objective="Greetings and Introductions",
)
```

`launch_worker()` formats `GAME_TASK` from `prompts.py`.

The generated assignment tells the worker to:

- Invent a game teaching the assigned objective.
- Use vanilla HTML, CSS, and JavaScript.
- Include progression and increasing difficulty.
- Track a score.
- Display correct and wrong feedback.
- Write exactly three files.
- Link the shared `common.css`.
- Include a link back to `index.html`.
- Work when opened directly through `file://`.
- Read all three files back before marking the task complete.

For Strands, the relevant portion becomes:

```text
Teach Greetings and Introductions in Spanish.

Write exactly three files into the folder "strands/":

strands/game.html
strands/game.css
strands/game.js
```

The entire assignment is inserted into SQLite:

```python
goal_id = board.add_goal(task)
```

## 2. The worker is launched as a separate process

For Strands, the orchestrator runs:

```text
uv run strands_worker.py <goal_id> <board.sqlite>
```

For example:

```text
uv run strands_worker.py 1 /.../5_agent_loop/site/board.sqlite
```

The other workers are launched similarly:

```text
uv run pydantic_worker.py <goal_id> <board.sqlite>
uv run maf_worker.py <goal_id> <board.sqlite>
uv run agno_worker.py <goal_id> <board.sqlite>
npx tsx worker.ts <goal_id> <board.sqlite>
```

All workers can run concurrently.

## 3. The worker switches into Day 5 mode

Using Strands as an example, its module reads:

```python
TASK_ID = int(sys.argv[1]) if len(sys.argv) > 2 else None
```

Because the orchestrator supplied two arguments:

```python
TASK_ID = <goal ID>
```

It then configures the shared board:

```python
os.environ.setdefault(
    "BOARD_PATH",
    sys.argv[2],
)
```

The worker's write directory becomes the parent directory of the board:

```python
WORK_DIR = Path(sys.argv[2]).resolve().parent
```

Therefore:

```text
board path:      5_agent_loop/site/board.sqlite
write directory: 5_agent_loop/site/
```

This is why the worker can write:

```text
site/strands/game.html
site/strands/game.css
site/strands/game.js
```

## 4. The worker receives four kinds of tools

Every worker receives equivalent tools, although each framework registers them differently.

### `show_todos`

```python
def show_todos() -> list[dict]:
    return board.list_todos()
```

This lets the worker read the complete assignment from SQLite.

### `plan_steps`

```python
def plan_steps(
    goal_id: int,
    steps: list[str],
) -> dict:
    return {
        "goal_id": goal_id,
        "step_ids": [
            board.add_step(goal_id, step)
            for step in steps
        ],
    }
```

This lets the worker create a checklist underneath its goal.

### `complete_task`

```python
def complete_task(
    task_id: int,
    result: str,
) -> dict:
    board.complete_todo(task_id, result)
    return {
        "task_id": task_id,
        "status": "done",
    }
```

This lets the worker mark individual steps and the parent goal complete.

### Filesystem MCP tools

The worker launches:

```text
npx -y @modelcontextprotocol/server-filesystem <WORK_DIR>
```

The MCP server provides operations such as:

```text
list_directory
read_file
write_file
create_directory
```

It is restricted to:

```text
5_agent_loop/site/
```

The worker cannot use that MCP server to write arbitrarily elsewhere.

## 5. The worker claims its goal

The worker's `main()` calls:

```python
board.claim_todo(TASK_ID)
```

This changes the goal status:

```text
pending → in_progress
```

Then it creates this message:

```text
You have claimed task #1 on the shared board.
Work only that task and its steps.

When the work is built and checked, mark task #1
itself done with complete_task, then stop.
```

This message does not contain the complete game assignment. The agent must use `show_todos()` to read task number 1 from SQLite.

## 6. The framework starts its agent loop

Each framework passes approximately the same information to its agent:

```text
Model:
    openai/gpt-5.5 through OpenRouter

Instructions:
    Read the goal, plan steps, perform them with file tools,
    complete every step, and finally complete the goal.

Tools:
    show_todos
    plan_steps
    complete_task
    filesystem tools

Initial message:
    Work task #<goal_id> on the shared board.
```

The framework then runs the agent:

| Worker | Agent execution method |
|---|---|
| Strands | `await worker.invoke_async(message)` |
| Pydantic AI | `await worker.run(message)` |
| Microsoft Agent Framework | `await worker.run(message)` |
| Agno | `await worker.arun(input=message)` |
| Mastra | `await worker.generate(message, {maxSteps: 25})` |

The APIs differ, but the logical operation is the same.

## 7. How the LLM/tool loop works

Consider the Strands worker. It constructs:

```python
worker = Agent(
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
```

Then:

```python
await worker.invoke_async(message)
```

The framework manages a loop resembling:

```text
1. Send instructions, message, and tool definitions to the model.
2. Model requests a tool call.
3. Framework executes that tool.
4. Framework sends the tool result back to the model.
5. Model requests another tool or produces a final answer.
6. Repeat until the model stops.
```

For example:

```text
Worker LLM
    ↓
show_todos()
    ↓
Framework runs Python function
    ↓
SQLite returns all goals and steps
    ↓
Result is sent back to the worker LLM
    ↓
Worker LLM now understands its assignment
```

## 8. The worker creates a plan

After reading its goal, the worker might call:

```python
plan_steps(
    goal_id=1,
    steps=[
        "Inspect the site directory and shared style",
        "Design and write the three game files",
        "Read the files back and verify the requirements",
        "Mark the goal complete",
    ],
)
```

That creates SQLite rows such as:

```text
Goal #1: Build a Spanish greetings game
    Step #6: Inspect the site directory and shared style
    Step #7: Design and write the three game files
    Step #8: Read the files back and verify requirements
    Step #9: Mark the goal complete
```

Because workers run concurrently, step IDs from different workers may be interleaved.

## 9. The worker invents the game

The game itself comes from the worker LLM.

There is no function like:

```python
build_greetings_game()
```

Instead, the model reads the objective and decides:

- The game theme.
- The title.
- The educational content.
- The questions and answers.
- Scoring rules.
- Progression rules.
- HTML structure.
- Visual design.
- JavaScript interactions.

For example, the Strands worker received a greetings objective and invented:

```text
¡Hola, Detective!
```

The Agno worker received a common-verbs objective and invented:

```text
Verb Voyage
```

Those concepts were generated at runtime, not selected from templates.

## 10. The worker writes `game.html`

The worker sends a filesystem MCP tool call conceptually like:

```json
{
  "name": "write_file",
  "arguments": {
    "path": "strands/game.html",
    "content": "<!DOCTYPE html>..."
  }
}
```

The framework forwards this to the filesystem MCP server, which writes:

```text
5_agent_loop/site/strands/game.html
```

The generated HTML must include:

```html
<link rel="stylesheet" href="../common.css">
<link rel="stylesheet" href="game.css">
```

and a back link such as:

```html
<a href="../index.html">Back to arcade</a>
```

It also loads:

```html
<script src="game.js"></script>
```

## 11. The worker writes `game.css`

It makes another filesystem call:

```json
{
  "name": "write_file",
  "arguments": {
    "path": "strands/game.css",
    "content": "..."
  }
}
```

The worker's CSS can reuse variables and shared classes from:

```text
site/common.css
```

The shared stylesheet is linked before the worker-specific stylesheet, so the game can extend or override the common styles.

## 12. The worker writes `game.js`

It then writes the game logic:

```json
{
  "name": "write_file",
  "arguments": {
    "path": "strands/game.js",
    "content": "..."
  }
}
```

The generated JavaScript typically includes:

- Question or vocabulary data.
- Game state.
- Score tracking.
- Level or round tracking.
- Answer-button handlers.
- Correct/wrong feedback.
- Progression logic.
- Restart behavior.

Everything must be local because the game needs to work through `file://`.

## 13. The worker marks file-writing steps complete

After creating the files, it might call:

```python
complete_task(
    task_id=7,
    result=(
        "Created strands/game.html, game.css, "
        "and game.js."
    ),
)
```

That updates the board, and the live terminal immediately shows the step as completed.

## 14. The worker reads the files back

The assignment explicitly tells the worker to read the three files back through its file tools before completing the task.

The expected calls resemble:

```text
read_file("strands/game.html")
read_file("strands/game.css")
read_file("strands/game.js")
```

This basic self-check confirms that:

- The files were actually written.
- They are not empty.
- Their contents were not truncated.
- The required links appear in `game.html`.

It does not guarantee that the JavaScript works in a browser; browser QA occurs later.

## 15. The worker completes the goal

After verification, it calls something like:

```python
complete_task(
    task_id=1,
    result=(
        "Built and verified the self-contained "
        "Spanish greetings game."
    ),
)
```

The goal status changes:

```text
in_progress → done
```

Then the worker agent stops and the subprocess exits.

## Framework-specific implementation differences

### AWS Strands

Uses:

```python
Agent(
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
```

Runs with:

```python
await worker.invoke_async(message)
```

### Pydantic AI

Uses:

```python
Agent(
    MODEL,
    instructions=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
    ],
    toolsets=[
        filesystem,
    ],
)
```

Runs with:

```python
await worker.run(message)
```

### Microsoft Agent Framework

Creates the MCP filesystem tool inside `main()`:

```python
filesystem = MCPStdioTool(...)
```

Then:

```python
Agent(
    client=client,
    instructions=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
```

Runs with:

```python
await worker.run(message)
```

### Agno

Creates:

```python
MCPTools(
    server_params=server,
    timeout_seconds=60,
)
```

Then:

```python
Agent(
    model=model,
    instructions=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
```

Runs with:

```python
await worker.arun(input=message)
```

### Mastra

Combines board and filesystem tools:

```typescript
tools: {
  ...boardTools,
  ...(await filesystem.listTools()),
}
```

Then runs:

```typescript
await worker.generate(message, {
  maxSteps: 25,
});
```

Mastra explicitly limits its worker loop to 25 steps. The Python workers depend on their respective framework behavior and model termination.

## What the worker checks versus what the orchestrator checks

The worker performs a file-level self-check:

```text
Did I write all three files?
Can I read them back?
Do they contain the required code and links?
```

After the process exits, the orchestrator performs a basic deterministic check:

```python
is_built(folder)
```

That only confirms:

```text
game.html exists and is non-empty
game.css exists and is non-empty
game.js exists and is non-empty
```

Finally, the separate QA agent performs the behavioral check:

```text
Does the page load?
Do buttons respond?
Does the browser console show errors?
```

Building and verification therefore happen in three layers:

```text
Worker LLM
    → invents and writes the game
    → reads its files back

Orchestrator Python
    → checks that all three files exist and are non-empty

QA LLM with Playwright
    → opens and plays the game in Chrome
```
