# Running the Agent Loop: Exact Calls and Default Arguments

This document explains what happens when you run:

~~~bash
cd 5_agent_loop
uv run agent_loop.py
~~~

It follows the code across files, shows the arguments passed at each stage, and distinguishes deterministic Python execution from calls chosen dynamically by an LLM.

## The essential mental model

There are three execution layers:

~~~text
Normal Python code
    |
    | creates and runs
    v
Google ADK orchestrator agent
    |
    | launches subprocesses
    v
Five framework worker agents
~~~

Python controls startup, configuration, tool registration, subprocess management, timeouts, fallbacks, and cleanup.

The orchestrator LLM chooses which registered orchestration tool to call. Each worker is another LLM agent that chooses its own board and filesystem tool calls.

This distinction matters:

~~~text
Before runner.run_async():
    Python determines the exact call order.

Inside runner.run_async():
    The orchestrator LLM selects tool calls dynamically.

Inside each worker agent:
    That worker LLM selects board and filesystem calls dynamically.
~~~

## Paths used below

For readability:

~~~text
ROOT  = /Users/tanbui/Desktop/Main_Storage/ML&AI/EdDonner/AI_Agent_Track/agents/5_agent_frameworks
LOOP  = ROOT/5_agent_loop
SITE  = LOOP/site
BOARD = LOOP/site/board.sqlite
~~~

The actual program uses absolute pathlib Path objects.

## Default command-line and configuration values

With no CLI options:

~~~python
language = "Spanish"
skip = []
dry_run = False
no_open = False
~~~

Model and timeout defaults are:

~~~python
ORCHESTRATOR_MODEL = "google/gemini-3.5-flash"
WORKER_MODEL = "openai/gpt-5.5"
WORKER_TIMEOUT = 300
QA_TIMEOUT = 150
~~~

The model names and timeouts can be changed by environment variables. In particular, agent_loop.py calls load_dotenv(override=True), so values in .env can replace values already present in the shell.

OPENROUTER_API_KEY must be available in the environment. Its value is passed to model clients but is not hard-coded.

## Complete top-level call tree

~~~text
uv
└── executes 5_agent_loop/agent_loop.py
    └── main()
        ├── parse_args()
        ├── catalog.discover(skip=())
        ├── orchestrator.run("Spanish", workers, SITE, BOARD)
        │   ├── site_dir.mkdir(parents=True, exist_ok=True)
        │   ├── board.reset_board()
        │   ├── Team("Spanish", workers, SITE, BOARD)
        │   └── asyncio.run(_run(team))
        │       ├── _build_agent(team)
        │       │   ├── ORCHESTRATOR_PROMPT.format(...)
        │       │   ├── config.orchestrator_llm()
        │       │   ├── make_tools(team)
        │       │   └── LlmAgent(...)
        │       ├── InMemoryRunner(...)
        │       ├── create_session(...)
        │       └── runner.run_async(...)
        │           └── orchestrator LLM selects registered tools
        ├── orchestrator.is_built(...) for each discovered worker
        └── qa_agent.open_site(SITE / "index.html")
~~~

# Part 1: Deterministic startup

## 1. uv executes agent_loop.py

The bottom of agent_loop.py, lines 89–90, contains:

~~~python
if __name__ == "__main__":
    main()
~~~

Therefore Python calls:

~~~python
main()
~~~

Before main runs, the module-level code:

1. Configures stdout as UTF-8.
2. Calls load_dotenv(override=True).
3. Imports config.py.
4. Defines HERE, SITE, and BOARD_PATH.
5. Places BOARD_PATH and WORKER_MODEL in os.environ.
6. Imports catalog.py, orchestrator.py, and qa_agent.py.

The important environment assignments at agent_loop.py lines 42–43 are:

~~~python
os.environ["BOARD_PATH"] = str(BOARD_PATH)
os.environ["WORKER_MODEL"] = config.WORKER_MODEL
~~~

The subprocesses launched later inherit those values.

## 2. main calls parse_args

agent_loop.py line 60:

~~~python
args = parse_args()
~~~

The command has no options, so sys.argv is effectively:

~~~python
["agent_loop.py"]
~~~

parse_args returns:

~~~python
Namespace(
    language="Spanish",
    skip=[],
    dry_run=False,
    no_open=False,
)
~~~

## 3. main calls catalog.discover

agent_loop.py line 61:

~~~python
workers = catalog.discover(skip=tuple(args.skip))
~~~

The concrete call is:

~~~python
catalog.discover(skip=())
~~~

catalog.discover, in catalog.py lines 29–39, checks whether each configured worker file exists. With all five files available, it returns records equivalent to:

~~~python
workers = [
    {
        "key": "strands",
        "name": "AWS Strands",
        "colour": "cyan",
        "file": "../2_strands_pydantic/strands_worker.py",
        "runner": "python",
        "slug": "strands",
    },
    {
        "key": "pydantic",
        "name": "Pydantic AI",
        "colour": "green",
        "file": "../2_strands_pydantic/pydantic_worker.py",
        "runner": "python",
        "slug": "pydantic",
    },
    {
        "key": "maf",
        "name": "Microsoft Agent Framework",
        "colour": "magenta",
        "file": "../3_maf_agno/maf_worker.py",
        "runner": "python",
        "slug": "maf",
    },
    {
        "key": "agno",
        "name": "Agno",
        "colour": "yellow",
        "file": "../3_maf_agno/agno_worker.py",
        "runner": "python",
        "slug": "agno",
    },
    {
        "key": "mastra",
        "name": "Mastra",
        "colour": "blue",
        "file": "../4_mastra/worker.ts",
        "runner": "node",
        "slug": "mastra",
    },
]
~~~

Missing worker files are omitted. If the result is empty, main raises SystemExit before starting the orchestrator.

## 4. main calls orchestrator.run

agent_loop.py line 73:

~~~python
orchestrator.run(args.language, workers, SITE, BOARD_PATH)
~~~

The effective call is:

~~~python
orchestrator.run(
    language="Spanish",
    workers=workers,
    site_dir=Path("ROOT/5_agent_loop/site"),
    board_path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

## 5. orchestrator.run prepares the site

orchestrator.py lines 313–320:

~~~python
def run(language, workers, site_dir, board_path):
    site_dir.mkdir(parents=True, exist_ok=True)
    board.reset_board()
    team = Team(language, workers, site_dir, board_path)
    asyncio.run(_run(team))
    _ensure_site(team)
    return team
~~~

The mkdir call is effectively:

~~~python
Path("ROOT/5_agent_loop/site").mkdir(
    parents=True,
    exist_ok=True,
)
~~~

## 6. orchestrator.run resets the board

The source calls:

~~~python
board.reset_board()
~~~

No path is explicitly passed. board.py defines:

~~~python
def reset_board(path: Path = BOARD_PATH)
~~~

Because agent_loop.py set BOARD_PATH before importing orchestrator and board, the effective call is:

~~~python
board.reset_board(
    path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

reset_board calls:

~~~python
_connect(
    path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

It then executes:

~~~sql
DROP TABLE IF EXISTS todos;
~~~

and:

~~~sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    task TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT NOT NULL DEFAULT ''
);
~~~

This removes the previous todo history. It does not delete board.sqlite, common.css, index.html, or existing game folders.

Because generated files are retained, old non-empty game files can still satisfy is_built during a new run.

## 7. orchestrator.run creates Team

The effective constructor call is:

~~~python
team = Team(
    language="Spanish",
    workers=workers,
    site_dir=Path("ROOT/5_agent_loop/site"),
    board_path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

Team.__init__, in orchestrator.py lines 105–115, establishes:

~~~python
team.language = "Spanish"
team.workers = workers
team.site_dir = Path("ROOT/5_agent_loop/site")
team.board_path = Path("ROOT/5_agent_loop/site/board.sqlite")
team.by_key = {
    "strands": <strands record>,
    "pydantic": <pydantic record>,
    "maf": <maf record>,
    "agno": <agno record>,
    "mastra": <mastra record>,
}
team.by_slug = <same records indexed by slug>
team.objectives = {}
team.registry = {}
team.pending = []
team.fixed = set()
~~~

## 8. orchestrator.run calls _run

The source call is:

~~~python
asyncio.run(_run(team))
~~~

The argument passed to _run is the Team object created above.

asyncio.run creates an event loop, runs _run(team), and closes the event loop when it finishes.

## 9. _run calls _build_agent

orchestrator.py line 270:

~~~python
runner = InMemoryRunner(
    agent=_build_agent(team),
    app_name=_APP,
)
~~~

Python must evaluate _build_agent(team) before it can call InMemoryRunner.

The concrete call is:

~~~python
_build_agent(team=<Team object>)
~~~

## 10. _build_agent creates the instruction

_build_agent constructs a team description similar to:

~~~text
- AWS Strands (framework key: strands, folder: strands/)
- Pydantic AI (framework key: pydantic, folder: pydantic/)
- Microsoft Agent Framework (framework key: maf, folder: maf/)
- Agno (framework key: agno, folder: agno/)
- Mastra (framework key: mastra, folder: mastra/)
~~~

It then calls:

~~~python
prompts.ORCHESTRATOR_PROMPT.format(
    language="Spanish",
    team=<the five-line team description>,
)
~~~

The resulting prompt tells the agent to author the style, launch all workers, wait, test games, repair broken games once, and build the hub.

## 11. _build_agent creates the model

It calls:

~~~python
config.orchestrator_llm()
~~~

There are no function arguments.

With the default model setting, orchestrator_llm returns:

~~~python
LiteLlm(
    model="openrouter/google/gemini-3.5-flash",
    api_base="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
~~~

## 12. _build_agent calls make_tools

The call is visible at orchestrator.py line 266:

~~~python
tools=make_tools(team)
~~~

The argument is:

~~~python
make_tools(team=<Team object>)
~~~

make_tools, defined at orchestrator.py line 141, defines six nested functions and returns their function objects:

~~~python
[
    author_style,
    launch_worker,
    wait_for_team,
    test_game,
    relaunch_worker,
    build_hub,
]
~~~

make_tools does not execute those six functions. It creates them as closures over the Team object and returns them for registration.

## 13. _build_agent creates the ADK orchestrator

The effective call is:

~~~python
LlmAgent(
    name="orchestrator",
    model=<LiteLlm for openrouter/google/gemini-3.5-flash>,
    instruction=<formatted ORCHESTRATOR_PROMPT>,
    tools=[
        author_style,
        launch_worker,
        wait_for_team,
        test_game,
        relaunch_worker,
        build_hub,
    ],
)
~~~

ADK inspects the registered functions, including their names, parameters, type hints, and docstrings, and exposes them as callable tools to the model.

## 14. _run creates the runner and session

After _build_agent returns:

~~~python
InMemoryRunner(
    agent=<orchestrator LlmAgent>,
    app_name="agent_loop",
)
~~~

It creates a session with:

~~~python
runner.session_service.create_session(
    app_name="agent_loop",
    user_id="orchestrator",
)
~~~

The returned session ID is generated at runtime.

## 15. _run starts the orchestrator

The effective call is:

~~~python
runner.run_async(
    user_id="orchestrator",
    session_id=<generated session ID>,
    new_message=types.UserContent(
        "Design and build the arcade with your team: "
        "give each builder an objective, get the games "
        "built and working, then assemble the home page."
    ),
    run_config=RunConfig(
        max_llm_calls=80,
    ),
)
~~~

At this point the deterministic startup ends. The model now chooses among the six registered tools.

# Part 2: Model-controlled orchestrator tools

The prompt requests the following happy-path order:

~~~text
author_style()
launch_worker(...) once per framework
wait_for_team()
test_game(...) once per built game
relaunch_worker(...) for broken games, at most once each
wait_for_team() after repairs
test_game(...) for repaired games
build_hub()
~~~

This sequence is an instruction, not a hard-coded Python loop. The actual order and number of calls are decided by the orchestrator model.

## 16. author_style

Tool signature:

~~~python
author_style()
~~~

It takes no arguments.

When ADK invokes it, orchestrator.py calls:

~~~python
css_agent.author_style(
    language="Spanish",
    site_dir=Path("ROOT/5_agent_loop/site"),
)
~~~

css_agent.author_style then calls:

~~~python
_safe(
    prompt=prompts.CSS_PROMPT.format(
        language="Spanish",
    )
)
~~~

_safe calls:

~~~python
_ask(
    prompt=<complete Spanish arcade CSS prompt>,
)
~~~

_ask creates another ADK agent:

~~~python
LlmAgent(
    name="art_director",
    model=config.orchestrator_llm(),
    instruction=(
        "You are a precise front-end designer. "
        "Return only the file contents asked for."
    ),
)
~~~

It creates:

~~~python
InMemoryRunner(
    agent=<art-director agent>,
    app_name="agent_loop",
)
~~~

Then:

~~~python
create_session(
    app_name="agent_loop",
    user_id="orchestrator",
)
~~~

And:

~~~python
runner.run_async(
    user_id="orchestrator",
    session_id=<generated session ID>,
    new_message=types.UserContent(
        <formatted CSS prompt>
    ),
)
~~~

The result is stripped of an outer Markdown fence and written with:

~~~python
(SITE / "common.css").write_text(
    css if len(css) > 40 else _template_css(),
    encoding="utf-8",
)
~~~

The validation checks length only. It does not fully validate CSS syntax.

## 17. launch_worker

Tool signature:

~~~python
launch_worker(
    framework: str,
    objective: str,
)
~~~

Neither parameter has a Python default.

The allowed framework values are:

~~~text
strands
pydantic
maf
agno
mastra
~~~

The objective is invented by the orchestrator LLM.

A possible set of calls is:

~~~python
launch_worker(
    framework="strands",
    objective="Greetings and Introductions",
)

launch_worker(
    framework="pydantic",
    objective="Numbers and Basic Math",
)

launch_worker(
    framework="maf",
    objective="Food and Drink vocabulary",
)

launch_worker(
    framework="agno",
    objective="Common Spanish Verbs",
)

launch_worker(
    framework="mastra",
    objective="Colors and Shapes vocabulary",
)
~~~

Those objectives appeared in the existing board from a previous run. They are examples, not defaults. A new run resets the board and can select different objectives.

For each call, launch_worker formats:

~~~python
prompts.GAME_TASK.format(
    language="Spanish",
    objective=<LLM-selected objective>,
    slug=<framework key>,
)
~~~

It then calls:

~~~python
board.add_goal(
    task=<formatted GAME_TASK>,
)
~~~

Because path is omitted, the effective path argument is:

~~~python
path=Path("ROOT/5_agent_loop/site/board.sqlite")
~~~

SQLite returns a dynamic goal_id.

launch_worker then calls:

~~~python
_launch(
    goal_id=<dynamic SQLite goal ID>,
    worker=<selected worker record>,
    board_path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

## 18. _launch and catalog.launch_argv

_launch calls:

~~~python
catalog.launch_argv(
    worker=<selected worker record>,
    task_id=<dynamic goal ID>,
    board_path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

The possible commands are:

~~~text
uv run ROOT/2_strands_pydantic/strands_worker.py <goal_id> BOARD
uv run ROOT/2_strands_pydantic/pydantic_worker.py <goal_id> BOARD
uv run ROOT/3_maf_agno/maf_worker.py <goal_id> BOARD
uv run ROOT/3_maf_agno/agno_worker.py <goal_id> BOARD
npx tsx ROOT/4_mastra/worker.ts <goal_id> BOARD
~~~

Then _launch calls subprocess.Popen with:

~~~python
subprocess.Popen(
    argv=<one command above>,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    cwd=<parent directory of the worker file>,
    start_new_session=True,
)
~~~

On Windows the process-group argument differs. On macOS and Linux, start_new_session is True.

Worker current directories are:

| Framework | cwd |
|---|---|
| Strands | ROOT/2_strands_pydantic |
| Pydantic AI | ROOT/2_strands_pydantic |
| Microsoft Agent Framework | ROOT/3_maf_agno |
| Agno | ROOT/3_maf_agno |
| Mastra | ROOT/4_mastra |

Popen returns immediately, so the orchestrator can launch multiple workers before waiting.

## 19. wait_for_team

Tool signature:

~~~python
wait_for_team()
~~~

It takes no arguments because it closes over team.

It takes the processes from:

~~~python
team.pending
~~~

It displays the board by repeatedly calling:

~~~python
live_board.render(
    registry=team.registry,
)
~~~

live_board.render calls:

~~~python
board.list_todos(
    path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

The wait loop repeatedly evaluates:

~~~python
p.poll()
~~~

for each subprocess.

The effective timeout is:

~~~python
WORKER_TIMEOUT = 300
~~~

If that time is exceeded, _terminate receives each still-running Popen object.

When all processes finish, wait_for_team returns:

~~~python
team.status()
~~~

team.status calls is_built for each framework folder.

## 20. test_game

Tool signature:

~~~python
test_game(
    slug: str,
)
~~~

slug has no Python default. Expected values are:

~~~text
strands
pydantic
maf
agno
mastra
~~~

Typical calls are:

~~~python
test_game(slug="strands")
test_game(slug="pydantic")
test_game(slug="maf")
test_game(slug="agno")
test_game(slug="mastra")
~~~

For each slug, test_game first calls:

~~~python
team._built(slug)
~~~

which becomes:

~~~python
is_built(
    folder=Path("ROOT/5_agent_loop/site/<slug>"),
)
~~~

is_built checks that game.html, game.css, and game.js exist and have non-zero sizes.

For a built Strands game, test_game calls:

~~~python
qa_agent.judge_game(
    language="Spanish",
    objective=team.objectives.get("strands", ""),
    uri="file:///.../5_agent_loop/site/strands/game.html",
)
~~~

That coroutine is wrapped with:

~~~python
asyncio.wait_for(
    qa_agent.judge_game(...),
    timeout=150,
)
~~~

## 21. QA agent calls and arguments

qa_agent.judge_game creates Playwright MCP with:

~~~python
StdioServerParameters(
    command="npx",
    args=[
        "-y",
        "@playwright/mcp@latest",
        "--browser",
        "chrome",
        "--isolated",
    ],
)
~~~

By default --headless is absent. It is appended only when QA_HEADLESS equals 1.

The QA agent is:

~~~python
LlmAgent(
    name="qa_tester",
    model=config.orchestrator_llm(),
    instruction=(
        "You are a meticulous QA tester. "
        "Use the browser to check the game, then report your verdict."
    ),
    tools=[
        browser,
        report_game,
    ],
)
~~~

Its session call is:

~~~python
create_session(
    app_name="agent_loop",
    user_id="qa",
)
~~~

Its model call is:

~~~python
runner.run_async(
    user_id="qa",
    session_id=<generated QA session ID>,
    new_message=types.UserContent(
        prompts.QA_PROMPT.format(
            language="Spanish",
            objective=<the assigned objective>,
            uri=<game file URI>,
        )
    ),
    run_config=RunConfig(
        max_llm_calls=25,
    ),
)
~~~

The QA LLM uses browser tools dynamically and should finish by calling:

~~~python
report_game(
    works=<True or False>,
    note=<LLM-generated short sentence>,
)
~~~

Neither report argument has a default.

If the QA agent consumes all 25 calls without reporting, the code treats the game as working. If the browser is unavailable or the check errors, the orchestration tool reports that it could not finish checking and leaves the game as built.

## 22. relaunch_worker

Tool signature:

~~~python
relaunch_worker(
    framework: str,
    problem: str,
)
~~~

Neither argument has a default. The tool is only needed when QA reports a failure.

An example call is:

~~~python
relaunch_worker(
    framework="maf",
    problem="The answer buttons do not respond.",
)
~~~

It formats:

~~~python
prompts.FIX_TASK.format(
    language="Spanish",
    slug="maf",
    objective=team.objectives.get("maf", ""),
    symptom="The answer buttons do not respond.",
)
~~~

It then calls:

~~~python
board.add_goal(
    task=<formatted FIX_TASK>,
)
~~~

and:

~~~python
_launch(
    goal_id=<new dynamic goal ID>,
    worker=team.by_key["maf"],
    board_path=Path("ROOT/5_agent_loop/site/board.sqlite"),
)
~~~

team.fixed prevents the same framework from receiving more than one repair launch.

The orchestrator prompt tells the model to call wait_for_team and test_game again after a repair, but those follow-up calls are still model-selected.

## 23. build_hub

Tool signature:

~~~python
build_hub()
~~~

It takes no arguments because it closes over team.

It first calls:

~~~python
games = team.finished_games()
~~~

finished_games calls is_built for each framework and _read_title for each built game.html.

The resulting value is dynamic, for example:

~~~python
[
    {
        "label": "¡Hola, Detective! Spanish Greetings Game",
        "slug": "strands",
    },
    {
        "label": "Verb Voyage: Spanish Action Quest",
        "slug": "agno",
    },
]
~~~

It then calls:

~~~python
css_agent.build_hub(
    language="Spanish",
    games=<finished game list>,
    site_dir=Path("ROOT/5_agent_loop/site"),
)
~~~

css_agent.build_hub formats:

~~~python
prompts.HUB_PROMPT.format(
    language="Spanish",
    links=<generated game-link description>,
)
~~~

It uses the same _safe to _ask art-director path described for common.css, then writes:

~~~python
(SITE / "index.html").write_text(
    <generated hub or fallback template>,
    encoding="utf-8",
)
~~~

# Part 3: Worker subprocesses

Each worker is a separate operating-system process. The orchestrator does not import a worker or call a worker function directly.

## 24. Python worker command-line arguments

For Strands, Pydantic AI, MAF, and Agno, sys.argv has this shape:

~~~python
[
    "/absolute/path/to/<framework>_worker.py",
    "<goal_id>",
    "ROOT/5_agent_loop/site/board.sqlite",
]
~~~

Each worker executes:

~~~python
TASK_ID = int(sys.argv[1])
os.environ.setdefault("BOARD_PATH", sys.argv[2])
~~~

Therefore:

~~~python
TASK_ID = <dynamic SQLite goal ID>
BOARD_PATH = Path("ROOT/5_agent_loop/site/board.sqlite")
WORK_DIR = Path("ROOT/5_agent_loop/site")
WORKER_MODEL = "openai/gpt-5.5"
~~~

The model can be different if WORKER_MODEL was overridden.

The worker then calls:

~~~python
asyncio.run(main())
~~~

main takes no direct arguments. It reads the module-level TASK_ID.

The Day 5 branch calls:

~~~python
board.claim_todo(
    task_id=<goal ID>,
)
~~~

The message given to the worker agent is:

~~~text
You have claimed task #<goal_id> on the shared board. Work only that task and its steps. When the work is built and checked, mark task #<goal_id> itself done with complete_task, then stop.
~~~

Because TASK_ID is not None, the standalone seed function is not called. The worker does not reset the shared board.

## 25. Strands worker

File: ../2_strands_pydantic/strands_worker.py

The agent constructor receives:

~~~python
Agent(
    model=<OpenRouter OpenAIModel using openai/gpt-5.5>,
    system_prompt=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
~~~

It runs:

~~~python
worker.invoke_async(
    message=<task-specific message>,
)
~~~

## 26. Pydantic AI worker

File: ../2_strands_pydantic/pydantic_worker.py

The agent constructor receives:

~~~python
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
~~~

It runs:

~~~python
worker.run(
    message=<task-specific message>,
)
~~~

## 27. Microsoft Agent Framework worker

File: ../3_maf_agno/maf_worker.py

The filesystem tool receives:

~~~python
MCPStdioTool(
    name="filesystem",
    command="npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "ROOT/5_agent_loop/site",
    ],
    cwd="ROOT/5_agent_loop/site",
)
~~~

The worker agent receives:

~~~python
Agent(
    client=<OpenRouter client using openai/gpt-5.5>,
    instructions=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
~~~

It runs:

~~~python
worker.run(
    message=<task-specific message>,
)
~~~

## 28. Agno worker

File: ../3_maf_agno/agno_worker.py

The filesystem server receives:

~~~python
StdioServerParameters(
    command="npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "ROOT/5_agent_loop/site",
    ],
    cwd="ROOT/5_agent_loop/site",
)
~~~

The worker agent receives:

~~~python
Agent(
    model=<OpenRouter OpenAILike using openai/gpt-5.5>,
    instructions=INSTRUCTIONS,
    tools=[
        show_todos,
        plan_steps,
        complete_task,
        filesystem,
    ],
)
~~~

It runs:

~~~python
worker.arun(
    input=<task-specific message>,
)
~~~

## 29. Mastra worker

File: ../4_mastra/worker.ts

Its process.argv has this shape:

~~~typescript
[
  "<node executable>",
  "ROOT/4_mastra/worker.ts",
  "<goal_id>",
  "ROOT/5_agent_loop/site/board.sqlite",
]
~~~

It derives:

~~~typescript
TASK_ID = Number(args[0]);
WORK_DIR = dirname(BOARD_PATH);
~~~

The Mastra agent receives:

~~~typescript
new Agent({
  id: "worker",
  name: "Worker",
  instructions: INSTRUCTIONS,
  model: provider("openai/gpt-5.5"),
  tools: {
    ...boardTools,
    ...filesystemTools,
  },
});
~~~

It runs:

~~~typescript
worker.generate(message, {
  maxSteps: 25,
  onStepFinish: <callback>,
});
~~~

Afterward it disconnects the filesystem client and calls process.exit(0).

## 30. Dynamic calls inside workers

The worker files do not contain hard-coded functions such as write_game_html or write_game_js.

Instead, each worker LLM receives:

~~~text
show_todos
plan_steps
complete_task
filesystem tools
~~~

A typical but not guaranteed worker sequence is:

~~~text
show_todos()
plan_steps(goal_id, [...])
filesystem.write_file("<slug>/game.html", ...)
filesystem.write_file("<slug>/game.css", ...)
filesystem.write_file("<slug>/game.js", ...)
filesystem.read_file("<slug>/game.html")
filesystem.read_file("<slug>/game.css")
filesystem.read_file("<slug>/game.js")
complete_task(step_id, ...)
complete_task(goal_id, ...)
~~~

The exact calls and their order cannot be known before execution because each worker LLM chooses them dynamically.

# Part 4: Completion and fallbacks

## 31. The orchestrator runner finishes

When the orchestrator model stops, runner.run_async ends.

_run closes the runner with:

~~~python
runner.close()
~~~

If the orchestrator reaches 80 model calls, _run catches LlmCallsLimitExceededError and continues to the safety net. It also catches other exceptions raised during the runner loop.

## 32. orchestrator.run calls _ensure_site

The call is:

~~~python
_ensure_site(
    team=<Team object>,
)
~~~

If common.css does not exist:

~~~python
css_agent.write_template_style(
    site_dir=Path("ROOT/5_agent_loop/site"),
)
~~~

If index.html does not exist:

~~~python
css_agent.write_template_hub(
    language="Spanish",
    games=team.finished_games(),
    site_dir=Path("ROOT/5_agent_loop/site"),
)
~~~

The checks only test file existence. Existing malformed or stale files are not replaced by this safety net.

## 33. main performs the final checks

After orchestrator.run returns, main calls:

~~~python
orchestrator.is_built(
    folder=Path("ROOT/5_agent_loop/site/strands"),
)

orchestrator.is_built(
    folder=Path("ROOT/5_agent_loop/site/pydantic"),
)

orchestrator.is_built(
    folder=Path("ROOT/5_agent_loop/site/maf"),
)

orchestrator.is_built(
    folder=Path("ROOT/5_agent_loop/site/agno"),
)

orchestrator.is_built(
    folder=Path("ROOT/5_agent_loop/site/mastra"),
)
~~~

Only discovered workers are checked.

Each call verifies that these files exist and have non-zero sizes:

~~~text
<folder>/game.html
<folder>/game.css
<folder>/game.js
~~~

It does not validate HTML, CSS, JavaScript, or gameplay at this stage.

## 34. main opens the site

Because no_open is False, main calls:

~~~python
qa_agent.open_site(
    index_path=Path("ROOT/5_agent_loop/site/index.html"),
)
~~~

open_site calls:

~~~python
webbrowser.open(
    "file:///.../5_agent_loop/site/index.html",
)
~~~

The operating system then attempts to open the local page in the default browser.

# Fixed values versus runtime-selected values

The following values are fixed by the default command, unless overridden through environment variables:

| Value | Default |
|---|---|
| Language | Spanish |
| Skipped workers | None |
| Site directory | LOOP/site |
| Board path | LOOP/site/board.sqlite |
| Orchestrator app name | agent_loop |
| Orchestrator user ID | orchestrator |
| Orchestrator model | google/gemini-3.5-flash |
| Worker model | openai/gpt-5.5 |
| Orchestrator call limit | 80 |
| Worker timeout | 300 seconds |
| QA timeout | 150 seconds |
| QA call limit | 25 |
| QA browser | Chrome |
| QA browser mode | Visible and isolated |
| Open finished site | Yes |

The following values cannot be known before the run:

| Value | Why it is dynamic |
|---|---|
| Learning objectives | Selected by the orchestrator LLM |
| Orchestrator tool order | Selected by the orchestrator LLM |
| Goal IDs | Generated by SQLite |
| ADK session IDs | Generated at runtime |
| Worker todo steps | Selected by each worker LLM |
| Worker filesystem calls | Selected by each worker LLM |
| Game content and titles | Generated by worker LLMs |
| QA browser actions | Selected by the QA LLM |
| QA works and note values | Decided after browser interaction |
| Repair framework and problem | Based on QA results |
| Final hub game list | Depends on which game files are built |

# Requirements

A full run generally requires:

- OPENROUTER_API_KEY in the environment or repo .env.
- Internet access to OpenRouter.
- Python dependencies available through the root uv project.
- Node, npm, and npx for Mastra and MCP servers.
- Google Chrome for Playwright QA.
- Sufficient OpenRouter credit for the orchestrator, art director, workers, and QA agents.

The run can issue multiple model calls concurrently and may consume meaningful API credit.

# Running from the parent workspace

From inside 5_agent_loop:

~~~bash
uv run agent_loop.py
~~~

From ROOT:

~~~bash
uv run 5_agent_loop/agent_loop.py
~~~

To build without opening the final browser:

~~~bash
uv run agent_loop.py --no-open
~~~

To make QA use headless Chrome:

~~~bash
QA_HEADLESS=1 uv run agent_loop.py
~~~

To inspect worker discovery without resetting the board or spending model credit:

~~~bash
uv run agent_loop.py --dry-run
~~~
