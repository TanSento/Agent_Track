# The Agent Loop — what each file does

This folder is Day 5 of Week 5: an outer agent loop that coordinates the five framework workers you already built. The orchestrator is itself a Google ADK agent. It does not write the games. It decides *what* each builder should teach, launches them in parallel against one shared SQLite board, plays each finished game in a real browser, and sends a builder back once if a game is broken.

The output is a small language-learning arcade under `site/`: a shared `common.css`, one folder per worker (`strands/`, `pydantic/`, …) with `game.html` / `game.css` / `game.js`, and an `index.html` hub.

```
agent_loop.py          CLI entry point
    │
    ├── catalog.py     which workers exist, how to launch them
    ├── config.py      which models to use
    ├── orchestrator.py  the ADK agent + its tools (the loop)
    │       │
    │       ├── board.py        shared SQLite todo board
    │       ├── live_board.py   Rich live view of that board
    │       ├── prompts.py      all the prompt text
    │       ├── css_agent.py    author common.css + index.html
    │       ├── qa_agent.py     play a game in Chrome via Playwright MCP
    │       └── quiet.py        silence ADK / genai log noise
    │
    ├── lab.md         the course write-up (how to run it)
    └── SWAP_AI.md     how to swap models / headless QA
```

---

## The run, in one pass

1. `agent_loop.py` discovers workers, points everyone at `site/board.sqlite`, and calls `orchestrator.run(...)`.
2. The orchestrator agent follows `ORCHESTRATOR_PROMPT`: author style → launch every worker with a distinct learning objective → wait → test each game → one fix round if needed → build the hub.
3. Each worker is a subprocess of a file you already wrote (`strands_worker.py`, etc.). It reads its goal off the shared board, invents a game, writes three files into `site/<slug>/`, and marks the goal done.
4. A short-lived QA agent opens each `game.html` in Chrome (Playwright MCP) and reports whether it works.
5. A safety net writes a plain CSS/HTML template if the art-director agent never produced one.
6. The CLI prints a `file://` link to `site/index.html` and opens it.

---

## `agent_loop.py` — CLI entry point

Thin wrapper. It does not contain the loop; it prepares the environment and starts the orchestrator.

**Startup order matters.** dotenv and model env vars are loaded *before* `config` / `catalog` / `orchestrator` are imported, because those modules read `ORCHESTRATOR_MODEL`, `WORKER_MODEL`, and `BOARD_PATH` at import time.

What `main()` does:

1. Parse flags: `--language`, `--skip`, `--dry-run`, `--no-open`.
2. Call `catalog.discover(skip=...)`. If no worker files exist, exit.
3. Print the team. On `--dry-run`, stop here (no API spend).
4. Call `orchestrator.run(language, workers, SITE, BOARD_PATH)`.
5. Print a deterministic final check (`orchestrator.is_built` per folder), so a game the agent missed is still visible.
6. Print the `index.html` URI. Unless `--no-open`, call `qa_agent.open_site`.

Also: force stdout UTF-8 (Windows consoles choke on emoji in agent summaries) and set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` so Gemini uses the API key, not Vertex.

```bash
uv run agent_loop.py                    # Spanish arcade, every worker on disk
uv run agent_loop.py --language French
uv run agent_loop.py --skip agno mastra
uv run agent_loop.py --dry-run
uv run agent_loop.py --no-open
```

---

## `config.py` — the two model ids

One place to swap models. Two constants, each overridable by env var:

| Constant | Default | Who uses it |
|---|---|---|
| `ORCHESTRATOR_MODEL` | `gemini-3.5-flash` | ADK orchestrator, art director (`css_agent`), QA tester |
| `WORKER_MODEL` | `gpt-5.5` | the five framework workers (pushed into their env by `agent_loop.py`) |

Cheaper alternatives are in the comments. `SWAP_AI.md` covers one-off env overrides.

---

## `catalog.py` — worker manifest and launch argv

The only file that knows the cross-folder layout of Week 5.

`WORKERS` is a list of records, in the order the frameworks were taught:

| Field | Meaning |
|---|---|
| `key` | also the output folder slug (`strands`, `pydantic`, `maf`, `agno`, `mastra`) |
| `name` | human label on the live board |
| `colour` | Rich colour for that worker’s rows |
| `file` | path relative to this folder, e.g. `../2_strands_pydantic/strands_worker.py` |
| `runner` | `"python"` → `uv run …` or `"node"` → `npx tsx …` |

**`discover(skip=...)`** — include a worker only if its file exists on disk and its key is not in `--skip`. A student who skipped a day simply has a smaller team.

**`launch_argv(worker, task_id, board_path)`** — the subprocess command that puts a worker into Day 5 mode: it receives a board task id and the shared board path. Resolves `uv` / `npx` with `shutil.which` because a bare `npx` is a `.cmd` shim on Windows and `Popen` will not find it.

The game itself is *not* in the catalog. The orchestrator invents a learning objective at runtime; the worker invents the game.

---

## `board.py` — shared SQLite todo board

The coordination substrate. Same idea as Days 1–4, now one file shared by every process: `site/board.sqlite` (path from `BOARD_PATH`).

One table, `todos`:

| Column | Role |
|---|---|
| `id` | autoincrement |
| `parent_id` | `NULL` = a top-level goal; set = a step under that goal |
| `task` | the text the worker reads |
| `status` | `pending` / `in_progress` / `done` |
| `result` | short note when completed |

WAL mode + a 5 second busy timeout let several agents read and write at once without locking each other out.

API the rest of the loop uses:

- `reset_board()` — drop and recreate the table at the start of a run
- `add_goal(task)` — orchestrator seeds one goal per worker; returns the id handed to the subprocess
- `add_step` / `claim_todo` / `complete_todo` — used *inside* the workers (not by the orchestrator)
- `list_todos()` — `live_board` polls this to redraw
- `show_board()` — pretty print for humans (Days 1–4); Day 5 uses `live_board` instead

A worker is given one goal id. It writes its own steps under that goal, ticks them off, then marks the goal done. The orchestrator never writes steps; it only adds goals and watches.

---

## `live_board.py` — Rich live view of the board

Not a second board. A renderer over `board.list_todos()`.

`render(registry)` groups todos by `parent_id`. Top-level goals are the games; children are the steps each worker wrote for itself. Colour comes from `registry` (goal id → worker record), which the orchestrator fills when it launches. Workers never know their own colour.

Status styling:

- **done** — dim + strikethrough, with the `result` appended
- **in_progress** — bold
- **pending** — plain

A legend at the bottom maps colour to framework name. `wait_for_team` wraps this in `rich.live.Live` and refreshes ~8 times a second while workers run.

---

## `prompts.py` — all prompt text, out of the code

Nothing framework-specific lives here. A worker reads its task off the board; it does not care which framework it is.

| Prompt | Who uses it | What it asks for |
|---|---|---|
| `GAME_TASK` | `launch_worker` → board goal | Invent a vanilla HTML/CSS/JS game for `{objective}` in `{language}`; write exactly three files into `{slug}/`; link `../common.css` and `../index.html` |
| `ORCHESTRATOR_PROMPT` | the ADK orchestrator’s instruction | The 7-step playbook: style → launch all → wait → test → one fix round → hub → stop |
| `CSS_PROMPT` | `css_agent.author_style` | One cohesive `common.css` (dark theme, `.correct` / `.wrong`) |
| `HUB_PROMPT` | `css_agent.build_hub` | One `index.html` linking every finished game |
| `FIX_TASK` | `relaunch_worker` → board goal | Open the three files, fix the named `{symptom}`, keep local relative links |
| `QA_PROMPT` | `qa_agent.judge_game` | Open `{uri}`, click a few things, check the console, then call `report_game` |

The design is goal-focused: name the objective and the bar, leave the game design to the worker, leave “does this work / who to send back” to the orchestrator.

---

## `orchestrator.py` — the ADK agent and its tools

This is the loop. It is **not** a Python `for` loop that calls workers in order. It is an `LlmAgent` given a goal and six tools. The agent owns the decisions; the tools own the mechanics.

### `Team`

Working state the tools close over. The agent never sees this object.

- `by_key` / `by_slug` — look up a worker
- `objectives` — slug → the learning objective the agent assigned
- `registry` — goal id → worker (feeds `live_board` colour)
- `pending` — `Popen` handles not yet waited on
- `fixed` — slugs that already had their one repair (hard cap)

### Worker subprocesses

`_launch` uses `catalog.launch_argv`, cwd = the worker’s own folder, stdout/stderr to `DEVNULL` (framework banners would tear the live board). On POSIX, `start_new_session=True` so a timeout can SIGTERM the whole uv/npx/MCP tree. `_terminate` does `taskkill /T` on Windows, `killpg` elsewhere. Default worker timeout is 300s (`WORKER_TIMEOUT_S`).

### The six tools (`make_tools`)

| Tool | Sync / async | What it actually does |
|---|---|---|
| `author_style` | async | `css_agent.author_style` → `site/common.css` |
| `launch_worker(framework, objective)` | sync | format `GAME_TASK`, `board.add_goal`, spawn the worker, return immediately |
| `wait_for_team` | async | poll `Popen` until all exit; `Live` board the whole time; kill hung workers past timeout |
| `test_game(slug)` | async | `qa_agent.judge_game` with a 150s cap (`QA_TIMEOUT_S`); print WORKS / BROKEN |
| `relaunch_worker(framework, problem)` | sync | one `FIX_TASK` goal + spawn; refused if that slug is already in `fixed` |
| `build_hub` | async | `css_agent.build_hub` with titles scraped from each `game.html` `<title>` |

`is_built(folder)` is the deterministic check: all three of `game.html`, `game.css`, `game.js` exist and are non-empty.

### Running the agent

`_build_agent` fills `ORCHESTRATOR_PROMPT` with the live team list. `_run` uses `InMemoryRunner` with `max_llm_calls=80`. Orchestrator text is printed dim italic as it thinks. If it hits the call cap or a transient API error, the run stops cleanly — games already on disk are kept.

`_ensure_site` is the non-LLM safety net: if `common.css` or `index.html` is missing after the agent stops, write the built-in templates.

`run(...)` (the public entry) creates `site/`, resets the board, `asyncio.run(_run(team))`, then `_ensure_site`.

---

## `css_agent.py` — art director (style + hub)

Two one-shot ADK turns, not a long-running agent.

- `author_style(language, site_dir)` — `CSS_PROMPT` → write `common.css`. If the model returns fewer than 40 characters (or throws), write `_template_css()` instead.
- `build_hub(language, games, site_dir)` — `HUB_PROMPT` with the list of `"label" at slug/game.html` → write `index.html`. If the result has no `<` or is too short, write `_template_hub(...)`.

`_ask` builds a fresh `LlmAgent` named `art_director`, runs one `InMemoryRunner` turn, concatenates text parts, and strips markdown fences. `_safe` swallows exceptions and returns `""` so a rate limit cannot crash the run.

`write_template_style` / `write_template_hub` are the same templates without an LLM call — used by `orchestrator._ensure_site` if the agent never invoked the tools at all.

---

## `qa_agent.py` — play a game in a real browser

The capstone lesson in miniature: give an agent a goal and a way to check its own success.

`judge_game(language, objective, uri)` builds a **new, short-lived** ADK agent per game so one confusing page cannot burn the whole budget.

Tools:

1. Playwright MCP (`npx @playwright/mcp@latest --browser chrome --isolated`) — same browser-over-MCP idea as Week 4’s Sidekick. `QA_HEADLESS=1` adds `--headless`.
2. `report_game(works, note)` — a local function the agent must call to finish. The verdict is stored in a closure.

Budget: `max_llm_calls=25`. If the agent hits that cap without reporting, the game is treated as working (it stayed responsive for the whole check). If MCP/Chrome is missing, return `None` and the orchestrator leaves the game as built.

Teardown is careful: close the MCP toolset and runner *inside* the event loop with a 10s timeout each, then a tiny `sleep`, so a wedged browser cannot hang the run with “event loop is closed”.

`open_site(index_path)` is the non-agent helper: `webbrowser.open` the finished arcade for the human.

---

## `quiet.py` — silence library chatter

Call `silence()` **before** importing ADK. It:

- filters `[EXPERIMENTAL]` warnings
- turns `google_genai._api_client` down to ERROR (the harmless “both GOOGLE_API_KEY and GEMINI_API_KEY are set” line)
- turns ADK node-runner / runners loggers to CRITICAL so a handled `LlmCallsLimitExceededError` does not dump a traceback

Used by `orchestrator.py`, `css_agent.py`, and `qa_agent.py`.

---

## `lab.md` and `SWAP_AI.md` — course notes, not code

- **`lab.md`** — the Day 5 write-up: setup (same `.env` keys, Node 24, Chrome), how workers join the team when given a task id, the six tools, and the CLI flags.
- **`SWAP_AI.md`** — how to change `ORCHESTRATOR_MODEL` / `WORKER_MODEL` (file or env), and `QA_HEADLESS=1` for CI / no window.

---

## How a worker joins this loop

The workers are **not** in this folder. They are the Day 2–4 files, e.g. `../2_strands_pydantic/strands_worker.py`. Near the top they read:

```python
TASK_ID = int(sys.argv[1]) if len(sys.argv) > 2 else None
```

- No args → standalone demo (own board, translate `notes.txt`). Unchanged.
- `task_id` + `board_path` → Day 5 mode: point board + file tools at the shared site, claim that one goal, build the game the task describes, exit.

`catalog.launch_argv` always passes those two args. The agent, tools, and instructions inside each worker stay the same; only the entry branch changes. That sameness is why five different frameworks can sit on one board.

---

## What ends up on disk

After a successful run, `site/` looks like:

```
site/
  board.sqlite
  common.css
  index.html
  strands/game.html   game.css   game.js
  pydantic/game.html  game.css   game.js
  maf/game.html       game.css   game.js
  agno/game.html      game.css   game.js
  mastra/game.html    game.css   game.js
```

Folders for skipped or missing workers are simply absent. Open `index.html` from disk (`file://`); the games are self-contained, no server required.
