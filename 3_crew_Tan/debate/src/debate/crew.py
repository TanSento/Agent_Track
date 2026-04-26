from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase     # Decorator to load agent and task configurations from YAML files.
class Debate():
    """Debate crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # @CrewBase automatically defaults to config/agents.yaml and config/tasks.yaml
    # which is exactly where your files already live. The explicit declaration in 3_crew is redundant.
    # You'd only need to add it if your config files were in a non-standard location

    # agents_config = 'config/agents.yaml'
    # tasks_config = 'config/tasks.yaml'

    @agent
    def debater(self) -> Agent:
        return Agent(config=self.agents_config['debater'], verbose=True)

    @agent
    def judge(self) -> Agent:
        return Agent(config=self.agents_config['judge'], verbose=True)

    @task
    def propose(self) -> Task:
        return Task(config=self.tasks_config['propose'])

    @task
    def oppose(self) -> Task:
        return Task(config=self.tasks_config['oppose'])

    @task
    def decide(self) -> Task:
        return Task(config=self.tasks_config['decide'])

    @crew
    def crew(self) -> Crew:
        """Creates the Debate crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
