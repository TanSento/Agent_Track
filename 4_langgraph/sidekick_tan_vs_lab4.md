# sidekick_tan.py vs 4_lab4.ipynb — Key Differences

## 1. Architecture
- `sidekick_tan.py` — object-oriented (`class Sidekick`) with `__init__`, `async setup()`, instance methods
- `4_lab4.ipynb` — procedural script, everything is module-level functions and global variables

## 2. Playwright / Tool Setup
- `sidekick_tan.py` — imports `playwright_tools()` and `other_tools()` from `sidekick_tools_tan.py`, which also includes file tools, push notifications, web search (Serper), Wikipedia, and Python REPL
- `4_lab4.ipynb` — only playwright tools via `create_async_playwright_browser()` + `nest_asyncio.apply()`, no other tools

## 3. Worker System Prompt
- `sidekick_tan.py` — adds current datetime (`datetime.now()`) and explicitly mentions available tools in the prompt
- `4_lab4.ipynb` — simpler prompt, no datetime, no tool mention

## 4. Thread / Session Management
- `sidekick_tan.py` — `sidekick_id` fixed per instance (set in `__init__`), same thread for the life of the object
- `4_lab4.ipynb` — `make_thread_id()` generates a new UUID per Gradio session stored in `gr.State`, supports multiple concurrent users

## 5. Success Criteria Fallback
- `sidekick_tan.py` — has default: `success_criteria or "The answer should be clear and accurate"`
- `4_lab4.ipynb` — no fallback, takes user input as-is

## 6. Gradio UI & Cleanup
- `sidekick_tan.py` — no UI (lives in a separate `app.py`), has a `cleanup()` method to close browser/playwright
- `4_lab4.ipynb` — Gradio UI built inline, no cleanup

## Summary
`sidekick_tan.py` is a refactored, class-based, more capable version with more tools and proper resource cleanup. `4_lab4.ipynb` is the simpler original prototype.
