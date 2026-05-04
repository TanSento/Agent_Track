# TypedDict vs Pydantic BaseModel in LangGraph

## Why State uses TypedDict

LangGraph specifically requires `TypedDict` for state because:

1. **LangGraph's internals use dict-based state** — it merges, snapshots, and checkpoints state as plain dicts. `TypedDict` is just a dict with type hints, so it's natively compatible.

2. **`Annotated[List[Any], add_messages]` is a LangGraph reducer** — this syntax tells LangGraph *how* to merge the `messages` field across node updates (append, not overwrite). Pydantic doesn't support this reducer pattern.

3. **Performance** — no validation overhead on every state update, which happens frequently in a graph.

## Why EvaluatorOutput uses BaseModel

`EvaluatorOutput` uses `BaseModel` because it's used for **structured LLM output parsing** (via `.with_structured_output()`), where Pydantic's validation and schema generation is exactly what's needed.

Different tools, different jobs.
