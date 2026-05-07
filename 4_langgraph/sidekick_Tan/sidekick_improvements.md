# Sidekick Improvements

## 4b. Verifier Routes Directly to Worker on Issues — pending
Currently when the verifier finds issues, it always routes to the evaluator, which may set `user_input_needed=True` and go to END — meaning the worker never gets a chance to fix the problem. The verifier should route directly back to the worker when `issues_found=True`, bypassing the evaluator entirely. The evaluator's "benefit of the doubt" prompt makes it too lenient to reliably catch and re-queue verified failures. Fix: `verifier_router` returns `"worker"` when issues are found, `"evaluator"` when clean.

## 5. Memory Across Sessions — pending
Currently `MemorySaver` is in-memory only and wiped on reset. Persisting memory to disk (e.g. SQLite via `SqliteSaver`) would let the sidekick remember past tasks, user preferences, and prior mistakes across sessions — making it a genuine long-term co-worker rather than starting fresh every time.

## 6. MD to PDF Conversion Tool — pending
Add a tool that converts markdown report files in sandbox to PDF. The agent could call this after saving any `.md` report, giving the user a ready-to-share document instead of a raw text file.
