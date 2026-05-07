# Sidekick Improvements 1–4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Sidekick LangGraph agent with a planning agent, upfront clarification, specialist sub-agents, and a verification agent — in that order, each building on the last.

**Architecture:** Each improvement adds one or more new nodes to the existing LangGraph. The graph flow evolves from `START → worker → evaluator → END` to `START → clarifier → planner → task_classifier → worker → verifier → evaluator → END`. State is extended with new fields for each node's output.

**Tech Stack:** LangGraph, LangChain, OpenAI via OpenRouter, Pydantic, Python 3.11+, uv

---

## File Structure

- **Modify:** `4_langgraph/sidekick_Tan/sidekick_tan.py` — all changes go here (new State fields, new Pydantic models, new node methods, updated `build_graph`)

---

## Task 1: Planning Agent

The planner runs before the worker. It reads the user request and success criteria, then produces an ordered list of subtasks. The worker receives this plan in its system prompt.

**Files:**
- Modify: `4_langgraph/sidekick_Tan/sidekick_tan.py`

- [x] **Step 1: Add `task_plan` to State**

In `sidekick_tan.py`, update the `State` TypedDict:

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]  # ordered subtask list from planner
```

- [x] **Step 2: Add `PlannerOutput` Pydantic model**

Below `EvaluatorOutput`, add:

```python
class PlannerOutput(BaseModel):
    task_plan: str = Field(
        description="An ordered, numbered list of concrete subtasks to complete the user's request. Each step should be specific and actionable."
    )
```

- [x] **Step 3: Add planner LLM to `__init__` and `setup`**

In `__init__`, add:
```python
self.planner_llm_with_output = None
```

In `setup`, after the evaluator LLM setup:
```python
planner_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
self.planner_llm_with_output = planner_llm.with_structured_output(PlannerOutput)
```

- [x] **Step 4: Add `planner` node method**

Add this method to the `Sidekick` class, before `worker`:

```python
def planner(self, state: State) -> Dict[str, Any]:
    user_request = ""
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            user_request = message.content
            break

    system_message = """You are a planning agent. Your job is to break down a user's request into a clear, ordered list of subtasks before any work begins.
Each subtask should be concrete and specific. Order them so that data is gathered before it is used, scripts are run before summaries are written, and nothing is assumed without first being verified."""

    user_message = f"""The user's request is:
{user_request}

The success criteria is:
{state["success_criteria"]}

Produce a numbered list of subtasks to complete this request in the correct order."""

    planner_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    result = self.planner_llm_with_output.invoke(planner_messages)
    return {"task_plan": result.task_plan}
```

- [x] **Step 5: Update `worker` to include task plan in system prompt**

In the `worker` method, after the line `system_message = f"""You are a helpful assistant...` block, add the task plan injection before the `if state.get("feedback_on_work")` check:

```python
    if state.get("task_plan"):
        system_message += f"""

You have been given the following execution plan. Follow this order strictly:
{state["task_plan"]}
"""
```

- [x] **Step 6: Update `build_graph` to wire the planner**

In `build_graph`, update the nodes and edges:

```python
async def build_graph(self):
    graph_builder = StateGraph(State)

    graph_builder.add_node("planner", self.planner)
    graph_builder.add_node("worker", self.worker)
    graph_builder.add_node("tools", ToolNode(tools=self.tools))
    graph_builder.add_node("evaluator", self.evaluator)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "worker")
    graph_builder.add_conditional_edges(
        "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
    )
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges(
        "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
    )

    self.graph = graph_builder.compile(checkpointer=self.memory)
```

- [x] **Step 7: Update `run_superstep` to include `task_plan` in initial state**

```python
state = {
    "messages": message,
    "success_criteria": success_criteria or "The answer should be clear and accurate",
    "feedback_on_work": None,
    "success_criteria_met": False,
    "user_input_needed": False,
    "task_plan": None,
}
```

- [x] **Step 8: Test manually**

Launch the app:
```bash
cd 4_langgraph/sidekick_Tan
uv run app.py
```

Send this request:
- Message: `Search for the current Bitcoin price, write a Python script that calculates 10% and 20% gains from that price, run it, and save the results to sandbox.`
- Success criteria: `A Python script saved to sandbox, and a results file with actual numbers from running the script.`

Expected: The evaluator feedback message shows "Evaluator Feedback..." and the worker followed a plan that ran the script before writing the summary. Check sandbox for output files.

- [x] **Step 9: Commit**

```bash
git add 4_langgraph/sidekick_Tan/sidekick_tan.py
git commit -m "feat: add planning agent node to sidekick"
```

---

## Task 2: Clarification Agent

The clarifier runs before the planner. It checks whether the request is ambiguous and, if so, asks the user one focused question. The graph stops and returns to the user. On the next run, the clarifier sees the answer and proceeds to the planner.

**Files:**
- Modify: `4_langgraph/sidekick_Tan/sidekick_tan.py`

- [x] **Step 1: Add `clarification_question` to State**

Update `State`:

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]
    clarification_question: Optional[str]  # set by clarifier if request is ambiguous
```

- [x] **Step 2: Add `ClarifierOutput` Pydantic model**

```python
class ClarifierOutput(BaseModel):
    needs_clarification: bool = Field(
        description="True if the request is ambiguous enough that a clarifying question is needed before planning."
    )
    question: str = Field(
        description="The single most important clarifying question to ask the user. Empty string if needs_clarification is False."
    )
```

- [x] **Step 3: Add clarifier LLM to `__init__` and `setup`**

In `__init__`, add:
```python
self.clarifier_llm_with_output = None
```

In `setup`, after planner LLM setup:
```python
clarifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
self.clarifier_llm_with_output = clarifier_llm.with_structured_output(ClarifierOutput)
```

- [x] **Step 4: Add `clarifier` node method**

Add before `planner`:

```python
def clarifier(self, state: State) -> Dict[str, Any]:
    # Skip if we already asked a question — user has now replied
    if state.get("clarification_question"):
        return {"clarification_question": None}

    user_request = ""
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            user_request = message.content
            break

    system_message = """You are a clarification agent. Your job is to decide whether a user's request is clear enough to act on, or whether one key question needs to be answered first.
Only ask for clarification if the request is genuinely ambiguous and the answer would significantly change how the task is done. Do not ask unnecessary questions."""

    user_message = f"""The user's request is:
{user_request}

The success criteria is:
{state["success_criteria"]}

Decide: is this request clear enough to proceed, or is there one important clarifying question to ask first?"""

    clarifier_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    result = self.clarifier_llm_with_output.invoke(clarifier_messages)

    if result.needs_clarification:
        return {
            "clarification_question": result.question,
            "user_input_needed": True,
            "messages": [{"role": "assistant", "content": f"Question: {result.question}"}],
        }
    return {"clarification_question": None}
```

- [x] **Step 5: Add `clarifier_router` method**

```python
def clarifier_router(self, state: State) -> str:
    if state.get("clarification_question"):
        return "END"
    return "planner"
```

- [x] **Step 6: Update `build_graph` to wire the clarifier**

```python
async def build_graph(self):
    graph_builder = StateGraph(State)

    graph_builder.add_node("clarifier", self.clarifier)
    graph_builder.add_node("planner", self.planner)
    graph_builder.add_node("worker", self.worker)
    graph_builder.add_node("tools", ToolNode(tools=self.tools))
    graph_builder.add_node("evaluator", self.evaluator)

    graph_builder.add_edge(START, "clarifier")
    graph_builder.add_conditional_edges(
        "clarifier", self.clarifier_router, {"planner": "planner", "END": END}
    )
    graph_builder.add_edge("planner", "worker")
    graph_builder.add_conditional_edges(
        "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
    )
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges(
        "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
    )

    self.graph = graph_builder.compile(checkpointer=self.memory)
```

- [x] **Step 7: Update `run_superstep` to include `clarification_question` in initial state**

```python
state = {
    "messages": message,
    "success_criteria": success_criteria or "The answer should be clear and accurate",
    "feedback_on_work": None,
    "success_criteria_met": False,
    "user_input_needed": False,
    "task_plan": None,
    "clarification_question": None,
}
```

- [x] **Step 8: Test manually**

Send a vague request:
- Message: `Write me a report`
- Success criteria: `A report saved to sandbox`

Expected: The chat shows `Question: ...` asking what the report should be about. Then reply with a topic and hit Go again — the clarifier skips (question already asked), planner runs, worker executes.

- [x] **Step 9: Commit**

```bash
git add 4_langgraph/sidekick_Tan/sidekick_tan.py
git commit -m "feat: add clarification agent node before planner"
```

---

## Task 3: Specialist Sub-agents (Task Classifier)

A task classifier node runs after the planner and sets `task_type` in state. The worker reads `task_type` and adapts its system prompt to behave as a specialist: researcher, coder, or writer.

**Files:**
- Modify: `4_langgraph/sidekick_Tan/sidekick_tan.py`

- [ ] **Step 1: Add `task_type` to State**

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]
    clarification_question: Optional[str]
    task_type: Optional[str]  # "research" | "coding" | "writing" | "general"
```

- [ ] **Step 2: Add `TaskClassifierOutput` Pydantic model**

```python
class TaskClassifierOutput(BaseModel):
    task_type: str = Field(
        description="The primary nature of the task. Must be one of: 'research' (web lookup, data gathering), 'coding' (write/run Python scripts), 'writing' (produce reports, summaries, documents), 'general' (mixed or unclear)."
    )
```

- [ ] **Step 3: Add classifier LLM to `__init__` and `setup`**

In `__init__`, add:
```python
self.classifier_llm_with_output = None
```

In `setup`, after clarifier LLM setup:
```python
classifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
self.classifier_llm_with_output = classifier_llm.with_structured_output(TaskClassifierOutput)
```

- [ ] **Step 4: Add `task_classifier` node method**

Add before `worker`:

```python
def task_classifier(self, state: State) -> Dict[str, Any]:
    system_message = """You are a task classification agent. Given a task plan, classify the primary nature of the work into one of:
- 'research': mainly web browsing, searching, gathering information
- 'coding': mainly writing and running Python scripts
- 'writing': mainly producing reports, summaries, or structured documents
- 'general': a significant mix of the above"""

    user_message = f"""Task plan:
{state.get("task_plan", "")}

Success criteria:
{state["success_criteria"]}

Classify the primary task type."""

    classifier_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    result = self.classifier_llm_with_output.invoke(classifier_messages)
    return {"task_type": result.task_type}
```

- [ ] **Step 5: Update `worker` to use specialist system prompts**

Replace the opening of the `worker` system prompt with a specialist-aware version:

```python
def worker(self, state: State) -> Dict[str, Any]:
    task_type = state.get("task_type", "general")

    specialist_context = {
        "research": "You are a research specialist. Prioritise using web search and browser tools to gather accurate, up-to-date information. Always verify facts before reporting them.",
        "coding": "You are a coding specialist. Write clean Python scripts, always run them using the Python REPL tool, and only report output that you have actually seen printed. Never assume what code will output — run it first.",
        "writing": "You are a writing specialist. Produce well-structured, clear documents. Base all content strictly on information already gathered or computed — do not invent data.",
        "general": "You are a helpful assistant that can use tools to complete tasks.",
    }.get(task_type, "You are a helpful assistant that can use tools to complete tasks.")

    system_message = f"""{specialist_context}
You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This is the success criteria:
{state["success_criteria"]}
You should reply either with a question for the user about this assignment, or with your final response.
If you have a question for the user, you need to reply by clearly stating your question. An example might be:

Question: please clarify whether you want a summary or a detailed answer

If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
"""
    # ... rest of worker unchanged from here
```

- [ ] **Step 6: Update `build_graph` to wire the task classifier**

```python
async def build_graph(self):
    graph_builder = StateGraph(State)

    graph_builder.add_node("clarifier", self.clarifier)
    graph_builder.add_node("planner", self.planner)
    graph_builder.add_node("task_classifier", self.task_classifier)
    graph_builder.add_node("worker", self.worker)
    graph_builder.add_node("tools", ToolNode(tools=self.tools))
    graph_builder.add_node("evaluator", self.evaluator)

    graph_builder.add_edge(START, "clarifier")
    graph_builder.add_conditional_edges(
        "clarifier", self.clarifier_router, {"planner": "planner", "END": END}
    )
    graph_builder.add_edge("planner", "task_classifier")
    graph_builder.add_edge("task_classifier", "worker")
    graph_builder.add_conditional_edges(
        "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
    )
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges(
        "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
    )

    self.graph = graph_builder.compile(checkpointer=self.memory)
```

- [ ] **Step 7: Update `run_superstep` to include `task_type` in initial state**

```python
state = {
    "messages": message,
    "success_criteria": success_criteria or "The answer should be clear and accurate",
    "feedback_on_work": None,
    "success_criteria_met": False,
    "user_input_needed": False,
    "task_plan": None,
    "clarification_question": None,
    "task_type": None,
}
```

- [ ] **Step 8: Test manually**

Send a coding-heavy request:
- Message: `Write a Python script that generates the first 20 Fibonacci numbers and saves them to a file in sandbox.`
- Success criteria: `A Python script saved to sandbox that was actually run, and a file with the 20 Fibonacci numbers.`

Expected: Worker behaves as coding specialist — runs the script before saving the output. Verify the sandbox files match actual script output.

- [ ] **Step 9: Commit**

```bash
git add 4_langgraph/sidekick_Tan/sidekick_tan.py
git commit -m "feat: add task classifier node for specialist worker prompts"
```

---

## Task 4: Verification Agent

The verifier runs after the worker (before the evaluator). It checks whether the worker's response is internally consistent — e.g. do the numbers in a summary match what the code in the script would actually produce. If issues are found it routes back to the worker with specific feedback.

**Files:**
- Modify: `4_langgraph/sidekick_Tan/sidekick_tan.py`

- [ ] **Step 1: Add `verification_feedback` to State**

```python
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]
    clarification_question: Optional[str]
    task_type: Optional[str]
    verification_feedback: Optional[str]  # set by verifier if issues found
```

- [ ] **Step 2: Add `VerifierOutput` Pydantic model**

```python
class VerifierOutput(BaseModel):
    issues_found: bool = Field(
        description="True if the worker's response contains inconsistencies, fabricated data, or claims that contradict the conversation history."
    )
    issues: str = Field(
        description="Description of the specific issues found. Empty string if issues_found is False."
    )
```

- [ ] **Step 3: Add verifier LLM to `__init__` and `setup`**

In `__init__`, add:
```python
self.verifier_llm_with_output = None
```

In `setup`, after classifier LLM setup:
```python
verifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
self.verifier_llm_with_output = verifier_llm.with_structured_output(VerifierOutput)
```

- [ ] **Step 4: Add `verifier` node method**

Add before `evaluator`:

```python
def verifier(self, state: State) -> Dict[str, Any]:
    last_response = state["messages"][-1].content

    system_message = """You are a verification agent. Your job is to catch inconsistencies in the worker's response before it reaches the evaluator.

Look for:
- Numbers or data in summaries that don't match what the code or logic in the conversation would actually produce
- Claims that a file was written or a script was run, when no tool call evidence exists in the conversation
- Summaries that contradict tool outputs visible in the conversation history

Be precise — only flag clear, specific inconsistencies. Do not flag things that are simply unverifiable."""

    user_message = f"""Here is the full conversation history:
{self.format_conversation(state["messages"])}

The worker's final response to verify is:
{last_response}

Check for internal inconsistencies or fabricated data."""

    verifier_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    result = self.verifier_llm_with_output.invoke(verifier_messages)

    if result.issues_found:
        return {
            "verification_feedback": result.issues,
            "messages": [{"role": "assistant", "content": f"Verification issues found: {result.issues}"}],
        }
    return {"verification_feedback": None}
```

- [ ] **Step 5: Add `verifier_router` method**

```python
def verifier_router(self, state: State) -> str:
    if state.get("verification_feedback"):
        return "worker"
    return "evaluator"
```

- [ ] **Step 6: Update `worker` to include verification feedback**

In the `worker` method, after the `feedback_on_work` block, add:

```python
    if state.get("verification_feedback"):
        system_message += f"""
A verification check on your previous response found the following issues:
{state["verification_feedback"]}
Please correct these issues in your next response."""
```

- [ ] **Step 7: Update `build_graph` to wire the verifier**

```python
async def build_graph(self):
    graph_builder = StateGraph(State)

    graph_builder.add_node("clarifier", self.clarifier)
    graph_builder.add_node("planner", self.planner)
    graph_builder.add_node("task_classifier", self.task_classifier)
    graph_builder.add_node("worker", self.worker)
    graph_builder.add_node("tools", ToolNode(tools=self.tools))
    graph_builder.add_node("verifier", self.verifier)
    graph_builder.add_node("evaluator", self.evaluator)

    graph_builder.add_edge(START, "clarifier")
    graph_builder.add_conditional_edges(
        "clarifier", self.clarifier_router, {"planner": "planner", "END": END}
    )
    graph_builder.add_edge("planner", "task_classifier")
    graph_builder.add_edge("task_classifier", "worker")
    graph_builder.add_conditional_edges(
        "worker", self.worker_router, {"tools": "tools", "verifier": "verifier"}
    )
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges(
        "verifier", self.verifier_router, {"worker": "worker", "evaluator": "evaluator"}
    )
    graph_builder.add_conditional_edges(
        "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
    )

    self.graph = graph_builder.compile(checkpointer=self.memory)
```

- [ ] **Step 8: Update `run_superstep` to include `verification_feedback` in initial state**

```python
state = {
    "messages": message,
    "success_criteria": success_criteria or "The answer should be clear and accurate",
    "feedback_on_work": None,
    "success_criteria_met": False,
    "user_input_needed": False,
    "task_plan": None,
    "clarification_question": None,
    "task_type": None,
    "verification_feedback": None,
}
```

- [ ] **Step 9: Test with the investment prompt**

Launch and send:
- Message: `Search for the current Bitcoin and Ethereum prices. Write a Python script that simulates investing $1000 split equally across 5 coins at today's prices, calculates what each position would be worth after a 20% pump, then save the script and a results summary to sandbox.`
- Success criteria: `A Python script saved to sandbox that was actually run, and a results summary whose numbers match the script output exactly.`

Expected: The verifier catches any mismatch between the summary and what the script math would produce, sends the worker back to fix it before the evaluator sees it.

- [ ] **Step 10: Commit**

```bash
git add 4_langgraph/sidekick_Tan/sidekick_tan.py
git commit -m "feat: add verification agent node before evaluator"
```

---

## Final Graph Flow

```
START
  │
  ▼
clarifier ──(needs clarification?)──▶ END (question shown to user)
  │ (clear request)
  ▼
planner
  │
  ▼
task_classifier
  │
  ▼
worker ──(tool_calls?)──▶ tools ──▶ worker
  │ (no tool calls)
  ▼
verifier ──(issues found?)──▶ worker (with correction feedback)
  │ (no issues)
  ▼
evaluator ──(criteria met?)──▶ END
  │ (not met)
  ▼
worker (retry with evaluator feedback)
```
