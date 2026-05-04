# Pydantic `BaseModel` Usage in `2_openai`

> Community contributions folders excluded.

---

## Notebooks

| File | Models Defined |
|---|---|
| `3_lab3.ipynb` | `NameCheckOutput(BaseModel)` |
| `3_lab3_Tan.ipynb` | `NameCheckOutput`, `ProfanityCheckOutput`, `ToneCheckOutput` |
| `4_lab4.ipynb` | `WebSearchItem`, `WebSearchPlan`, `ReportData` |
| `4_lab4_Tan.ipynb` | `WebSearchItem`, `WebSearchPlan`, `ReportData` |

---

## Python Agents (`deep_research` / `deep_research_Tan`)

| File | Models Defined |
|---|---|
| `deep_research/planner_agent.py` | `WebSearchItem`, `WebSearchPlan` |
| `deep_research/writer_agent.py` | `ReportData` |
| `deep_research_Tan/planner_agent.py` | `WebSearchItem`, `WebSearchPlan` |
| `deep_research_Tan/writer_agent.py` | `ReportData` |
| `deep_research_Tan/clarifier_agent.py` | `ClarificationPlan` *(custom addition)* |

---

## Notable Pattern Shift vs `1_foundations`

In `1_foundations`, Pydantic is used almost exclusively for **evaluation output** (`Evaluation` with `is_acceptable` + `feedback`).

In `2_openai`, Pydantic moves beyond evaluation — it structures the **agent's planning output** and the **final report**:

- `WebSearchItem` / `WebSearchPlan` — tells the planner exactly what searches to run
- `ReportData` — structures the final written report
- `ClarificationPlan` — structures the clarifying questions before research begins

Each agent's **output schema** becomes the next agent's **input contract** — this is the core multi-agent pattern enabled by Pydantic.
