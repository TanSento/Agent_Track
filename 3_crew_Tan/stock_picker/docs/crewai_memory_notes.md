# CrewAI 1.x Memory Configuration Notes

## Default behaviour (`memory=True`)

When you pass `memory=True` to `Crew`, CrewAI internally creates a `Memory()` instance
with the following defaults:

| Weight | Default |
|---|---|
| `recency_weight` | 0.3 |
| `semantic_weight` | 0.4 |
| `importance_weight` | 0.3 |
| `recency_half_life_days` | 30 |

The default embedder is **OpenAI `text-embedding-3-small`**, so specifying it explicitly
is redundant unless you want a different model or provider.

---

## Custom Memory weights

To control scoring behaviour, import `Memory` and pass an instance instead of `True`:

```python
from crewai.memory import Memory
```

### Example 1 — Favour recency (e.g. sprint retrospective)

```python
memory = Memory(
    recency_weight=0.5,
    semantic_weight=0.3,
    importance_weight=0.2,
    recency_half_life_days=7,
)
```

### Example 2 — Favour importance (e.g. architecture knowledge base)

```python
memory = Memory(
    recency_weight=0.1,
    semantic_weight=0.5,
    importance_weight=0.4,
    recency_half_life_days=180,
)
```

### Wiring it into your Crew

```python
@crew
def crew(self) -> Crew:
    manager = Agent(
        config=self.agents_config['manager'],
        allow_delegation=True
    )

    memory = Memory(
        recency_weight=0.5,
        semantic_weight=0.3,
        importance_weight=0.2,
        recency_half_life_days=7,
        # Optional — defaults to OpenAI text-embedding-3-small
        # embedder={"provider": "openai", "config": {"model": "text-embedding-3-small"}},
    )

    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        process=Process.hierarchical,
        verbose=True,
        manager_agent=manager,
        memory=memory,   # pass Memory instance, not True
    )
```

> **Note:** When passing a `Memory` instance, configure the `embedder` on the `Memory`
> object itself — not on the `Crew`. The `Crew.embedder` field is only used when
> `memory=True` (auto-instantiation path).

---

## What changed from CrewAI 0.x → 1.x

| Old API (0.x) | New API (1.x) |
|---|---|
| `LongTermMemory`, `ShortTermMemory`, `EntityMemory` | Single unified `Memory` class |
| `RAGStorage`, `LTMSQLiteStorage` | Pluggable `storage=` backend (LanceDB default) |
| Pass storage objects to `Crew` | Pass `memory=True` or a `Memory(...)` instance |
