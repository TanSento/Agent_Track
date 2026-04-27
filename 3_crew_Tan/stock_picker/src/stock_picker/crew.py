from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from typing import List
from pydantic import BaseModel, Field
from .tools.push_tool import PushNotificationTool
from crewai.memory import Memory  # import the Memory class


# Read md files in docs folder to understand the workflow

class TrendingCompany(BaseModel):
    """ A company that is trending in the news and attracting attention """
    name: str = Field(description="Company name")
    ticker: str = Field(description="Company ticker symbol")
    reason: str = Field(description="Reason why this company is trending in the news")


class TrendingCompanyList(BaseModel):
    """ A list of trending companies in the news and attracting attention """
    companies: List[TrendingCompany] = Field(description="List of trending companies in the news")


class TrendingCompanyResearch(BaseModel):
    """ Detailed research on a company """
    name: str = Field(description="Company name")
    market_position: str = Field(description="Current market position and competitive analysis")
    future_outlook: str = Field(description="Future outlook and growth prospects")
    investment_potential: str = Field(description="Investment potential and suitability for investment")


class TrendingCompanyResearchList(BaseModel):
    """ A list of detailed research on all the companies """
    research_list: List[TrendingCompanyResearch] = Field(description="Comprehensive research on all trending companies")


@CrewBase
class StockPicker():
    """StockPicker crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trending_company_finder(self) -> Agent:
        return Agent(config=self.agents_config['trending_company_finder'],
                     tools=[SerperDevTool()], 
                     memory=True)
    
    @agent
    def financial_researcher(self) -> Agent:
        return Agent(config=self.agents_config['financial_researcher'], 
                     tools=[SerperDevTool()])

    @agent
    def stock_picker(self) -> Agent:
        return Agent(config=self.agents_config['stock_picker'], 
                     tools=[PushNotificationTool()], 
                     memory=True
                    )  

    @task
    def find_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['find_trending_companies'],
            output_pydantic=TrendingCompanyList,
        ) # output a JSON schema, conforming to pydantic TrendingCompanyList and TrendingCompany object above
          # Recall that in tasks.yaml, this task output_file: output/trending_companies.json

    @task
    def research_trending_companies(self) -> Task:
        return Task(
            config=self.tasks_config['research_trending_companies'],
            output_pydantic=TrendingCompanyResearchList,
        ) # output a JSON schema, conforming to pydantic TrendingCompanyResearchList and TrendingCompanyResearch object above
          # Recall that in tasks.yaml, this task output_file: output/research_report.json

    @task
    def pick_best_company(self) -> Task:
        return Task(
            config=self.tasks_config['pick_best_company']
        )

    @crew
    def crew(self) -> Crew:
        """Creates the StockPicker crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True
        )

        # memory = Memory(
        #     recency_weight=0.5,
        #     semantic_weight=0.3,
        #     importance_weight=0.2,
        #     recency_half_life_days=7,
        #     # Optional: specify embedder, otherwise defaults to OpenAI text-embedding-3-small
        #     # embedder={"provider": "openai", "config": {"model": "text-embedding-3-small"}},
        # )   
        # Optional: Read more at docs/crewai_memory_notes.md
            
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=True,
            embedder={
                "provider": "openai",
                "config": {"model": "text-embedding-3-small"},
            },
        )  # Do not need embedder unless you want to use a different embedding model and provider 

    