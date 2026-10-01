# The Agent Loop — Full Explanation

## The goal

This is the capstone of Week 5 ("Agent Frameworks"). All week, the student built **the same worker agent five times**, once per framework (AWS Strands, Pydantic AI, Microsoft Agent Framework, Agno, Mastra) — each one doing an identical trivial task: read `notes.txt`, translate to Spanish, write `spanish.txt`, using a shared SQLite "todo board" to plan/track its own steps.

Day 5's point: because all five workers share the *exact same shape* (goal → plan steps on a board → work with file tools → tick off steps → close goal), they can be handed to a **coordinator** and put to work as a team with almost no extra glue. So today:

- A **sixth agent** (the orchestrator, built on Google ADK) is given a high-level goal: *"build a language-learning arcade using this team."*
- It invents a distinct learning objective per framework, launches all 5 workers **in parallel** as subprocesses, each inventing and building its own mini browser game (`game.html/css/js`) teaching that objective.
- It then **plays each game in a real browser** (via a QA sub-agent) to judge whether it actually works, sends any broken one back for exactly one fix attempt, and finally authors a themed home page linking them all.

The lesson in miniature: *give an agent a goal and a way to check its own success, and let it make the calls* — rather than a human/script hard-coding the sequence.

## The three layers

```
agent_loop.py  (CLI entry point, no intelligence)
      │
      ▼
orchestrator.py (the ADK agent — the "brain" of the whole run)
      │  calls tools:
      ├── css_agent.py   → author_style, build_hub  (art direction)
      ├── qa_agent.py    → test_game                (browser QA)
      └── subprocess launches →  5 framework workers (the "hands")
                                       │
                                       ▼
                              board.py (shared SQLite todo board)
```

### 1. `agent_loop.py` — dumb entry point
Just argument parsing (`--language`, `--skip`, `--dry-run`, `--no-open`) and worker discovery via `catalog.py` (file-existence check — if you skipped a day, that framework's file doesn't exist, so it's silently left out of the team). It hands off to `orchestrator.run(...)` and does a final deterministic sanity check afterward (in case the LLM's own bookkeeping missed something), then opens the finished site in a browser.

### 2. `orchestrator.py` — the orchestrator agent (the actual "loop")
This is the key insight: **the orchestrator is not a Python `while` loop calling workers in a fixed order** — it's itself a Google ADK `LlmAgent` with a goal-focused prompt (`prompts.py: ORCHESTRATOR_PROMPT`) and 6 tools. The LLM decides the sequence; the tools are just the deterministic mechanics:

| Tool | What it does |
|---|---|
| `author_style()` | Calls the art-director sub-agent once, up front, to write `common.css` (shared house style for all games) |
| `launch_worker(framework, objective)` | Picks a distinct learning objective (e.g. "greetings", "food and drink"), writes a goal onto the shared board, and spawns that framework's worker as a subprocess pointed at the shared board + site folder. Returns immediately — non-blocking, so the orchestrator calls this once per framework before waiting |
| `wait_for_team()` | Blocks until every launched subprocess exits, rendering a live colour-coded Rich board (`live_board.py`) the whole time. Has a timeout (`WORKER_TIMEOUT`, default 300s) so a hung worker gets killed rather than stalling the run forever |
| `test_game(slug)` | Hands one finished game to a fresh, short-lived QA sub-agent (see below) that actually opens it in Chrome and judges whether it works |
| `relaunch_worker(framework, problem)` | If `test_game` reports broken, drops a "fix" task on the board and relaunches just that one worker — capped at **one** fix attempt per game, enforced by `team.fixed` |
| `build_hub()` | Calls the art-director sub-agent again, once, at the end, to write `index.html` linking every finished game by the title its builder gave it |

The orchestrator's own working state lives in a `Team` object (which workers exist, which objectives were assigned, which subprocesses are pending, which slugs already got their one fix) — the LLM never sees this object directly, only what the tool functions choose to return as text.

Safety nets baked in: a turn budget (`_MAX_TURNS = 80`) so a confused agent can't loop forever; if the art-director calls fail or come back empty, plain built-in HTML/CSS templates are written instead so the site is never left broken (`_ensure_site`).

### 3. `css_agent.py` — the "art director"
Two single-turn, stateless ADK agent calls with no tools, just an LLM asked to return raw CSS or HTML:
- `author_style` → writes `common.css` (dark theme, CSS variables, `.correct`/`.wrong` feedback classes) before any games exist
- `build_hub` → writes `index.html` once it knows which games actually got built and what they're titled

Both fall back to a hand-written template (`_template_css`/`_template_hub`) if the LLM call fails or returns garbage.

### 4. `qa_agent.py` — the "QA tester"
This is the more interesting sub-agent. For each finished game, `judge_game()` spins up a **brand-new, short-lived ADK agent** equipped with:
- The **Playwright MCP browser server** (`npx @playwright/mcp`) — a real, driveable Chrome instance (same idea as the Sidekick's browser-over-MCP in Week 4)
- One custom tool, `report_game(works, note)`, which is how the agent records its verdict and signals it's done

The agent is told (`QA_PROMPT`) to open the game, click around, check the console, and call `report_game` within ~5 actions. A fresh agent per game keeps browser/context state small and bounded (`_MAX_CALLS = 25`); if the agent burns its whole budget without calling `report_game` but was clearly still interacting, that's treated as "it works" rather than a false failure. Browser teardown is carefully bounded (`_CLOSE_TIMEOUT`) so a wedged browser can't hang the whole run.

### 5. `board.py` / `live_board.py` — the shared substrate
A single SQLite file (`site/board.sqlite`, WAL mode + busy-timeout so concurrent processes don't collide) with one `todos` table: goals (`parent_id NULL`) and steps (`parent_id = goal id`), each with `status` (pending/in_progress/done) and a `result` note. Every framework's worker — all week, and now all five at once — reads and writes this same table through nearly identical `show_todos`/`plan_steps`/`complete_task` tool functions. `live_board.py` renders it live in the terminal, colour-coding each goal/step by which framework owns it (colour comes from the orchestrator's own `registry`, so workers never need to know their own colour).

### 6. The five framework workers — the "hands"
These are **unchanged from earlier in the week** (`2_strands_pydantic/strands_worker.py`, `pydantic_worker.py`, `3_maf_agno/maf_worker.py`, `agno_worker.py`, `4_mastra/worker.ts`). Each is dual-mode, switched by whether `sys.argv` has a task id + board path:

- **Standalone** (`uv run strands_worker.py`): seeds its own single goal (the Day 2/3 "translate notes.txt" demo) and works it alone.
- **Day 5 mode** (`uv run strands_worker.py <taskId> <boardPath>`): points its board and filesystem-MCP tool at the *shared* board/site instead of its own workspace, claims the one task the orchestrator assigned it, and works only that.

The agent/tools/instructions are byte-for-byte identical between modes — only a small branch at the top picks the mode. All five follow the identical pattern despite the framework-specific APIs (Strands' `@tool` decorator + `MCPClient`, Pydantic AI's `MCPToolset`, MAF's `MCPStdioTool`, Agno's `MCPTools`, Mastra's TS `Agent` + tool objects), each pointed at OpenRouter via that framework's OpenAI-compatible client. Each worker gets its task text from `prompts.py: GAME_TASK` (read off the board, not passed as a CLI argument) — it's told to invent a game, teach the given objective, write exactly `game.html/css/js`, link the shared `common.css`, and link back to the hub — and it decides everything else about *how* the game plays.

## One full run, start to finish

1. `agent_loop.py` discovers however many of the 5 worker files exist, resets the board, and starts the orchestrator agent with the goal "design and build the arcade."
2. Orchestrator calls `author_style` → `common.css` written.
3. Orchestrator invents 5 distinct objectives and calls `launch_worker` once per framework → 5 subprocesses spawned in parallel, each claiming its own goal row on the shared board and building its own game.
4. Orchestrator calls `wait_for_team` → blocks, live board fills in with each framework's steps in its own colour, until all subprocesses exit (or timeout).
5. Orchestrator calls `test_game` per framework → a QA sub-agent actually plays each game in Chrome and reports works/broken + a note.
6. For anything broken, orchestrator calls `relaunch_worker` (one shot) → `wait_for_team` again → `test_game` again.
7. Orchestrator calls `build_hub` → `index.html` written linking every finished game.
8. `agent_loop.py` does one final deterministic file-existence check as a safety net, then opens `site/index.html` in the browser.

## Notable design decisions worth knowing

- **Agent owns decisions, tools own mechanics** — a recurring principle: nothing in `orchestrator.py`'s tools contains judgment calls (which objective to assign, whether a game "works", when to give up fixing) — that's all left to the LLM. The tools are pure mechanism (subprocess management, SQLite writes, browser automation).
- **Bounded everything** — turn budgets, worker timeouts, QA timeouts, one fix attempt per game, bounded browser-close — so a confused or slow LLM/subprocess can't hang or spiral the whole run.
- **Degrade gracefully, never crash** — missing worker file → smaller team; failed CSS/HTML generation → template fallback; QA unreachable → leave game as "built" rather than failing the run; orchestrator error/budget exceeded → finish with what's already on disk.
- **Everything is swappable in one place** — `config.py` is the only place model ids are set (`ORCHESTRATOR_MODEL`, `WORKER_MODEL`, both via OpenRouter), and `prompts.py` is the only place any prompt text lives.

Note: there's also a sibling folder `5_agent_loop_ed/` (an instructor's reference copy) — same file set, likely worth diffing against if you want to compare your version to the reference implementation.
