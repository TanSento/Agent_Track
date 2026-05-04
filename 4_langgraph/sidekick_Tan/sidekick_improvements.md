# Sidekick Improvements

## 1. Planning Agent for Task Decomposition
Add a planning agent that runs before the worker — it breaks down complex tasks into clear, ordered subtasks before any execution begins. Without this, the worker tends to figure out sequencing on the fly, which leads to mistakes like writing output summaries before actually running the underlying code. A planner would enforce a logical execution order — e.g. gather data first, run any scripts second, then write summaries from the real output — preventing fabricated or inconsistent results. More broadly, a planning layer improves coherence and reduces retries on any multi-step task.

## 2. Clarification Questions Before Starting
Allow the agent to ask the user clarifying questions upfront if the request is ambiguous, then incorporate the user's answers into the actual work. Currently the agent only asks questions mid-task when stuck — proactive clarification before starting would reduce retries and produce better first attempts.

## 3. Specialist Sub-agents
Instead of one worker doing everything, route tasks to specialist agents based on type: a research agent for web tasks, a coding agent for Python, a writing agent for reports. Reduces errors from context overload on complex multi-part tasks and produces higher quality output in each domain.

## 4. Verification Agent
A dedicated agent that verifies output before the evaluator sees it — e.g. actually executes saved scripts and checks that results match the summary. This would have directly caught the investment prompt bug where the numbers in the summary didn't match the script output.

## 5. Memory Across Sessions
Currently `MemorySaver` is in-memory only and wiped on reset. Persisting memory to disk (e.g. SQLite via `SqliteSaver`) would let the sidekick remember past tasks, user preferences, and prior mistakes across sessions — making it a genuine long-term co-worker rather than starting fresh every time.

## 6. MD to PDF Conversion Tool
Add a tool that converts markdown report files in sandbox to PDF. The agent could call this after saving any `.md` report, giving the user a ready-to-share document instead of a raw text file.
