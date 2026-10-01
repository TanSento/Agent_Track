# `simple_worker.py` vs `worker.py`

Both files run the same `root_agent`, use the same SQLite board, and ask the agent to translate `notes.txt` into Spanish. The main difference is that `simple_worker.py` removes features that are not necessary for a basic run.

## What both files do

Both scripts follow this workflow:

1. Reset the todo board.
2. Add the Spanish translation goal.
3. Mark the goal as `in_progress`.
4. Run `root_agent` with `InMemoryRunner`.
5. Display the board.
6. Print the contents of `spanish.txt` if it exists.

## Differences

### 1. Command-line options

`worker.py` imports `argparse` and supports two commands:

```bash
uv run worker.py
uv run worker.py --seed-only
```

The normal command creates the goal and immediately runs the agent. The `--seed-only` command creates the goal but stops before running the agent, allowing the user to work on that goal through `adk web`.

`simple_worker.py` has no command-line options:

```bash
uv run simple_worker.py
```

It always creates the goal and immediately runs the agent.

### 2. Workspace preparation

Before creating the goal, `worker.py` runs:

```python
WORKSPACE.mkdir(exist_ok=True)
(WORKSPACE / "spanish.txt").unlink(missing_ok=True)
```

The first line ensures that the workspace directory exists. The second deletes an old `spanish.txt`, preventing an old translation from being mistaken for the result of the current run.

`simple_worker.py` omits these lines. The workspace is already created when `task_worker.agent` is imported, but an existing `spanish.txt` is not deleted.

Therefore, `worker.py` provides a cleaner and more repeatable demonstration.

### 3. Logging control

`worker.py` calls:

```python
from quiet import silence

silence()
```

This reduces noisy library logging before importing ADK and the agent.

`simple_worker.py` does not silence those logs, so it may show more terminal output.

The `# noqa: E402` comments in `worker.py` tell the linter that its imports intentionally appear after `silence()`.

### 4. Status messages

`worker.py` prints additional explanations:

```text
Seeded goal 1: ...
Board after the run:
```

It also tells the user what to do after using `--seed-only`.

`simple_worker.py` prints only the board and the generated file, keeping the code shorter.

### 5. Type-annotation compatibility

`worker.py` uses:

```python
from __future__ import annotations
```

This postpones the evaluation of type annotations and can improve compatibility with some type hints and older Python versions.

`simple_worker.py` does not need it because its annotations are basic and the project uses modern Python.

### 6. Agent prompt wording

`worker.py` says:

```python
"Please work the pending task on the board."
```

`simple_worker.py` says:

```python
"Please work the goal on the board."
```

The simpler wording is slightly more accurate because both scripts change the goal from `pending` to `in_progress` before running the agent.

## Which one should you use?

Use `simple_worker.py` when learning the essential execution flow:

```text
seed goal → claim goal → run agent → show result
```

Use `worker.py` when you want:

- `adk web` support through `--seed-only`
- cleaner logging
- removal of an old output file
- clearer terminal status messages
- a more complete command-line demonstration

In short, `simple_worker.py` is easier to study, while `worker.py` is more convenient and reliable for repeated demonstrations.
