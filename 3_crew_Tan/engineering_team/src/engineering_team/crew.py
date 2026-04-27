import py_compile
import tempfile
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from engineering_team.models import SystemDesign


def log_module_built(output) -> None:
    """Callback fired after each code or test task completes."""
    print(f"[callback] task complete: {output.description[:80].strip()}")
    raw = output.raw or ""
    if raw.strip().startswith(("def ", "class ", "import ", "from ")):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(raw)
            tmp_path = f.name
        try:
            py_compile.compile(tmp_path, doraise=True)
            print(f"[callback] syntax OK")
        except py_compile.PyCompileError as e:
            print(f"[callback] syntax error: {e}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)


@CrewBase
class DesignCrew:
    """Single-agent crew: engineering lead designs the full system."""

    agents_config = "config/design_agents.yaml"
    tasks_config = "config/design_tasks.yaml"
    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config["engineering_lead"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_task"],  # type: ignore[index]
            output_pydantic=SystemDesign,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class ModuleCrew:
    """Two-agent crew: backend engineer writes a module, test engineer tests it."""

    agents_config = "config/module_agents.yaml"
    tasks_config = "config/module_tasks.yaml"
    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],  # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=240,
            max_retry_limit=5,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["test_engineer"],  # type: ignore[index]
            verbose=True,
            allow_code_execution=True,
            code_execution_mode="safe",
            max_execution_time=240,
            max_retry_limit=5,
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config["code_task"],  # type: ignore[index]
            callback=log_module_built,
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config["test_task"],  # type: ignore[index]
            callback=log_module_built,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


@CrewBase
class FrontendCrew:
    """Single-agent crew: frontend engineer builds the Gradio UI."""

    agents_config = "config/frontend_agents.yaml"
    tasks_config = "config/frontend_tasks.yaml"
    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],  # type: ignore[index]
            verbose=True,
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
