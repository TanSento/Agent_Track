# How the orchestrator calls different workers

The orchestrator never imports a worker or calls it as a Python function. It is an LLM with a tool named `launch_worker`. When it wants Strands (or Agno, Mastra, …) it **calls that tool with a framework key**, and Python starts that worker as its **own subprocess**.

## 1. Who is on the team

`agent_loop.py` asks `catalog.discover()` which worker files exist, then hands that list to the orchestrator. Each record has a **key** (`strands`, `pydantic`, `maf`, `agno`, `mastra`) and a **file path**.

```python
WORKERS = [
    {"key": "strands",  "name": "AWS Strands",                  "file": "../2_strands_pydantic/strands_worker.py",  "runner": "python"},
    {"key": "pydantic", "name": "Pydantic AI",                  "file": "../2_strands_pydantic/pydantic_worker.py", "runner": "python"},
    {"key": "maf",      "name": "Microsoft Agent Framework",    "file": "../3_maf_agno/maf_worker.py",              "runner": "python"},
    {"key": "agno",     "name": "Agno",                         "file": "../3_maf_agno/agno_worker.py",             "runner": "python"},
    {"key": "mastra",   "name": "Mastra",                       "file": "../4_mastra/worker.ts",                    "runner": "node"},
]
```

That list is written into the orchestrator’s prompt as `{team}`, so the model knows the legal keys:

```
- AWS Strands (framework key: strands, folder: strands/)
- Pydantic AI (framework key: pydantic, folder: pydantic/)
- Microsoft Agent Framework (framework key: maf, folder: maf/)
- Agno (framework key: agno, folder: agno/)
- Mastra (framework key: mastra, folder: mastra/)
```

## 2. The LLM picks a worker by key

The prompt tells it: for each framework, invent a learning objective, then call `launch_worker(framework, objective)`. It is supposed to start **all of them before waiting**, so they run in parallel.

## 3. The tool looks up that key and spawns a process

```python
def launch_worker(framework: str, objective: str) -> str:
    worker = team.by_key.get(framework)   # "strands" → the Strands record
    ...
    task = prompts.GAME_TASK.format(...)  # the game brief
    goal_id = board.add_goal(task)        # drop it on the shared SQLite board
    team.pending.append(_launch(goal_id, worker, team.board_path))
```

`_launch` does not talk to the worker over an API. It runs a shell command via `catalog.launch_argv`:

| `framework` | Command that actually starts |
|---|---|
| `strands` | `uv run …/strands_worker.py <goal_id> <board.sqlite>` |
| `pydantic` | `uv run …/pydantic_worker.py <goal_id> <board.sqlite>` |
| `maf` | `uv run …/maf_worker.py <goal_id> <board.sqlite>` |
| `agno` | `uv run …/agno_worker.py <goal_id> <board.sqlite>` |
| `mastra` | `npx tsx …/worker.ts <goal_id> <board.sqlite>` |

Each process gets **one goal id** and the **shared board path**. The worker reads its task off the board, writes files into `site/<key>/`, and exits. The orchestrator only waits via `wait_for_team` until those processes finish.

So “calling a different worker” = the LLM choosing a different **string key** → the tool looking it up in `team.by_key` → `Popen` of a different script. They never share an in-process function call.

---

## Example: one Spanish run with all five workers

**1. You start it**

```bash
uv run agent_loop.py
```

**2. The LLM calls `launch_worker` five times** (it invents the objectives)

```
launch_worker(framework="strands",   objective="greetings")
launch_worker(framework="pydantic",  objective="numbers")
launch_worker(framework="maf",       objective="common verbs")
launch_worker(framework="agno",      objective="food and drink")
launch_worker(framework="mastra",    objective="colours")
```

Each call is just that string key. `"agno"` is looked up in `team.by_key` → the Agno record (`agno_worker.py`, runner `python`).

**3. For Agno, Python actually runs this**

```
uv run /.../3_maf_agno/agno_worker.py 4 /.../5_agent_loop/site/board.sqlite
```

`4` is the goal id just written on the board. The board row is the `GAME_TASK` text: invent a Spanish game that teaches **food and drink**, write three files into `site/agno/`.

Strands would be the same shape with a different script:

```
uv run /.../2_strands_pydantic/strands_worker.py 1 /.../site/board.sqlite
```

Mastra is the Node one:

```
npx tsx /.../4_mastra/worker.ts 5 /.../site/board.sqlite
```

Those five processes start immediately and run **at the same time**. The orchestrator does not sit inside them. It then calls `wait_for_team` and watches `board.sqlite` fill in.

**4. After they exit**, same idea for a repair:

```
relaunch_worker(framework="maf", problem="buttons do nothing")
```

That looks up `"maf"` again and spawns `maf_worker.py` with a new goal id whose task is the `FIX_TASK` text.
