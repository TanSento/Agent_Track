# Sidekick Improvements

## 5. Memory Across Sessions — pending
Currently `MemorySaver` is in-memory only and wiped on reset. Persisting memory to disk (e.g. SQLite via `SqliteSaver`) would let the sidekick remember past tasks, user preferences, and prior mistakes across sessions — making it a genuine long-term co-worker rather than starting fresh every time.

## 6. MD to PDF Conversion Tool — pending
Add a tool that converts markdown report files in sandbox to PDF. The agent could call this after saving any `.md` report, giving the user a ready-to-share document instead of a raw text file.
