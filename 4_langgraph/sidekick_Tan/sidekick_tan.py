from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv, find_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
import os
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools_tan import playwright_tools, other_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(find_dotenv(), override=True)  # walks up directories to find .env, works regardless of launch location


# See TypedDict vs BaseModel md file for more info
class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    task_plan: Optional[str]  # ordered subtask list from planner
    clarification_question: Optional[str]  # set by clarifier if request is ambiguous
    task_type: Optional[str]  # "research" | "coding" | "writing" | "general"
    verification_feedback: Optional[str]  # set by verifier if issues found


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class PlannerOutput(BaseModel):
    task_plan: str = Field(
        description="An ordered, numbered list of concrete subtasks to complete the user's request. Each step should be specific and actionable."
    )


class VerifierOutput(BaseModel):
    issues_found: bool = Field(
        description="True if the worker's response contains inconsistencies, fabricated data, or claims that contradict the conversation history."
    )
    issues: str = Field(
        description="Description of the specific issues found. Empty string if issues_found is False."
    )


class TaskClassifierOutput(BaseModel):
    task_type: str = Field(
        description="The primary nature of the task. Must be one of: 'research' (web lookup, data gathering), 'coding' (write/run Python scripts), 'writing' (produce reports, summaries, documents), 'general' (mixed or unclear)."
    )


class ClarifierOutput(BaseModel):
    needs_clarification: bool = Field(
        description="True if the request is ambiguous enough that a clarifying question is needed before planning."
    )
    question: str = Field(
        description="The single most important clarifying question to ask the user. Empty string if needs_clarification is False."
    )


class Sidekick:
    def __init__(self):    # no async init because we don't need to await anything
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.planner_llm_with_output = None
        self.classifier_llm_with_output = None
        self.clarifier_llm_with_output = None
        self.verifier_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        openrouter_kwargs = {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key": os.environ["OPENROUTER_API_KEY"],
        }
        worker_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        planner_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.planner_llm_with_output = planner_llm.with_structured_output(PlannerOutput)
        classifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.classifier_llm_with_output = classifier_llm.with_structured_output(TaskClassifierOutput)
        clarifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.clarifier_llm_with_output = clarifier_llm.with_structured_output(ClarifierOutput)
        verifier_llm = ChatOpenAI(model="openai/gpt-4o-mini", **openrouter_kwargs)
        self.verifier_llm_with_output = verifier_llm.with_structured_output(VerifierOutput)
        await self.build_graph()


    def clarifier(self, state: State) -> Dict[str, Any]:
        # Skip if a clarifying question was already asked in this conversation
        for message in state["messages"]:
            if isinstance(message, AIMessage) and message.content and message.content.startswith("Question:"):
                return {"clarification_question": None}

        user_request = ""
        for message in state["messages"]:
            if isinstance(message, HumanMessage):
                user_request = message.content
                break

        system_message = """You are a clarification agent. 
                        Your job is to decide whether a user's request is clear enough to act on, or whether one key question needs to be answered first.
                        Only ask for clarification if the request is genuinely ambiguous and the answer would significantly change how the task is done.
                        Do not ask unnecessary questions."""

        user_message = f"""The user's request is: {user_request}
                        The success criteria is: {state["success_criteria"]}.
                        Decide: is this request clear enough to proceed, or is there one important clarifying question to ask first?"""

        clarifier_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        result = self.clarifier_llm_with_output.invoke(clarifier_messages)

        if result.needs_clarification:
            return {
                "clarification_question": result.question,
                "user_input_needed": True,
                "messages": [{"role": "assistant", "content": f"Question: {result.question}"}],
            }
        return {"clarification_question": None}

    def clarifier_router(self, state: State) -> str:
        if state.get("clarification_question"):
            return "END"
        return "planner"

    def planner(self, state: State) -> Dict[str, Any]:
        user_request = ""
        for message in state["messages"]:
            if isinstance(message, HumanMessage):
                user_request = message.content
                break

        system_message = """You are a planning agent. Your job is to break down a user's request into a clear, ordered list of subtasks before any work begins.
                            Each subtask should be concrete and specific.
                            Order them so that data is gathered before it is used, scripts are run before summaries are written, and nothing is assumed without first being verified.
                            When referring to file saving steps, use plain filenames like "results.txt" — do NOT prefix with "sandbox/" as the file tools are already scoped to the sandbox directory."""

        user_message = f"""The user's request is: {user_request}
                            The success criteria is: {state["success_criteria"]}
                            Produce a numbered list of subtasks to complete this request in the correct order."""

        planner_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        result = self.planner_llm_with_output.invoke(planner_messages)
        return {"task_plan": result.task_plan}

    def task_classifier(self, state: State) -> Dict[str, Any]:
        system_message = """You are a task classification agent. Given a task plan, classify the primary nature of the work into one of:
                        - 'research': mainly web browsing, searching, gathering information
                        - 'coding': mainly writing and running Python scripts
                        - 'writing': mainly producing reports, summaries, or structured documents
                        - 'general': a significant mix of the above"""

        user_message = f"""Task plan:
                        {state.get("task_plan", "")}

                        Success criteria:
                        {state["success_criteria"]}

                        Classify the primary task type."""

        classifier_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        result = self.classifier_llm_with_output.invoke(classifier_messages)
        return {"task_type": result.task_type}

    # worker node - uses tools to complete tasks
    def worker(self, state: State) -> Dict[str, Any]:
        task_type = state.get("task_type", "general")

        specialist_context = {
            "research": "You are a research specialist. Prioritise using web search and browser tools to gather accurate, up-to-date information. Always verify facts before reporting them.",
            "coding": "You are a coding specialist. Write clean Python scripts, always run them using the Python REPL tool, and only report output that you have actually seen printed. Never assume what code will output — run it first. Always save the script itself to sandbox using the file writing tool. When you need to save output to a file, use print() in your script to capture the output, then use the file writing tool to save it — do not write files directly from inside the script.",
            "writing": "You are a writing specialist. Produce well-structured, clear documents. Base all content strictly on information already gathered or computed — do not invent data.",
            "general": "You are a helpful assistant that can use tools to complete tasks.",
        }.get(task_type, "You are a helpful assistant that can use tools to complete tasks.")

        system_message = f"""{specialist_context}
                            You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
                            You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
                            You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
                            When saving files, use plain filenames like "results.txt" or "script.py" — do NOT prefix with "sandbox/" as your file tools are already scoped to the sandbox directory.
                            The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

                            This is the success criteria: {state["success_criteria"]}
                            You should reply either with a question for the user about this assignment, or with your final response.
                            If you have a question for the user, you need to reply by clearly stating your question. An example might be:

                            Question: please clarify whether you want a summary or a detailed answer

                            If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
                            """

        if state.get("task_plan"):
            system_message += f""" You have been given the following execution plan. Follow this order strictly: {state["task_plan"]}"""

        if state.get("feedback_on_work"):
            system_message += f"""
                                Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
                                Here is the feedback on why this was rejected: {state["feedback_on_work"]}
                                With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        if state.get("verification_feedback"):
            system_message += f"""
                                A verification check on your previous response found the following issues:
                                {state["verification_feedback"]}
                                Please correct these issues in your next response."""

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "verifier"

    def verifier(self, state: State) -> Dict[str, Any]:
        last_response = state["messages"][-1].content

        system_message = """You are a verification agent. Your job is to catch inconsistencies in the worker's response before it reaches the evaluator.

                        Look for:
                        - Numbers or data in summaries that don't match what the code or logic in the conversation would actually produce
                        - Claims that a file was written or a script was run, when no tool call evidence exists in the conversation
                        - Summaries that contradict tool outputs visible in the conversation history

                        Be precise — only flag clear, specific inconsistencies. Do not flag things that are simply unverifiable."""

        user_message = f"""Here is the full conversation history:
                        {self.format_conversation(state["messages"])}

                        The worker's final response to verify is:
                        {last_response}

                        Check for internal inconsistencies or fabricated data."""

        verifier_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        result = self.verifier_llm_with_output.invoke(verifier_messages)

        if result.issues_found:
            return {
                "verification_feedback": result.issues,
                "messages": [{"role": "assistant", "content": f"Verification issues found: {result.issues}"}],
            }
        return {"verification_feedback": None}

    def verifier_router(self, state: State) -> str:
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
                            Assess the Assistant's last response based on the given criteria.
                            Respond with your feedback, and with your decision on whether the success criteria has been met,
                            and whether more input is needed from the user."""

        user_message = f"""You are evaluating a conversation between the User and Assistant.
                        You decide what action to take based on the last response from the Assistant.

                        The entire conversation with the assistant, with the user's original request and all replies, is:
                        {self.format_conversation(state["messages"])}

                        The success criteria for this assignment is:
                        {state["success_criteria"]}

                        And the final response from the Assistant that you are evaluating is:
                        {last_response}

                        Respond with your feedback, and decide if the success criteria is met by this response.
                        Also, decide if more user input is required, either because the assistant has a question,
                        needs clarification, or seems to be stuck and unable to answer without help.

                        The Assistant has access to a tool to write files.
                        If the Assistant says they have written a file, then you can assume they have done so.
                        Overall you should give the Assistant the benefit of the doubt if they say they've done something.
                        But you should reject if you feel that more work should go into this.

                        """
        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("task_classifier", self.task_classifier)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("verifier", self.verifier)
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "clarifier")
        graph_builder.add_conditional_edges(
            "clarifier", self.clarifier_router, {"planner": "planner", "END": END}
        )
        graph_builder.add_edge("planner", "task_classifier")
        graph_builder.add_edge("task_classifier", "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "verifier": "verifier"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "verifier", self.verifier_router, {"worker": "worker", "evaluator": "evaluator"}
        )
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}, "recursion_limit": 50}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "task_plan": None,
            "clarification_question": None,
            "task_type": None,
            "verification_feedback": None,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
