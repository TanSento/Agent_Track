from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv, find_dotenv
import os
import subprocess
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper



load_dotenv(find_dotenv(), override=True)  # walks up directories to find .env, works regardless of launch location
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright   
    # return because we need to clean up the browser and playwright after the session is done


def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def get_file_tools():
    # __file__                     → absolute path to this file (sidekick_tools_tan.py)
    # os.path.abspath(__file__)    → resolves any symlinks/relative parts to a clean absolute path
    # os.path.dirname(...)         → strips the filename, leaving just the directory (sidekick_Tan/)
    # os.path.join(..., "..", "sandbox") → goes one level up to 4_langgraph/, then into sandbox/
    # result: always 4_langgraph/sandbox/ regardless of where app.py is launched from
    sandbox_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sandbox")
    toolkit = FileManagementToolkit(root_dir=sandbox_path)
    return toolkit.get_tools()
    # gives the agent file system tools (read, write, list, delete) scoped to sandbox/ only


def _sandbox_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sandbox")


def read_sandbox_files() -> str:
    """List all files in sandbox and return their full contents."""
    sandbox = _sandbox_path()
    files = [f for f in os.listdir(sandbox) if os.path.isfile(os.path.join(sandbox, f))]
    if not files:
        return "Sandbox is empty."
    parts = []
    for filename in sorted(files):
        filepath = os.path.join(sandbox, filename)
        try:
            with open(filepath, "r") as f:
                content = f.read()
        except Exception:
            content = "[unreadable]"
        parts.append(f"--- {filename} ---\n{content}")
    return "\n\n".join(parts)


def run_sandbox_script(filename: str) -> str:
    """Run a Python script from sandbox and return its stdout output."""
    sandbox = _sandbox_path()
    script_path = os.path.join(sandbox, filename)
    if not os.path.exists(script_path):
        return f"Error: {filename} not found in sandbox."
    result = subprocess.run(
        ["python", script_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return f"Script error:\n{result.stderr}"
    return result.stdout or "(no output)"


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    file_tools = get_file_tools()

    tool_search = Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()

    sandbox_read_tool = Tool(
        name="read_sandbox_files",
        func=lambda _: read_sandbox_files(),
        description="List all files in sandbox and return their full contents. Use this to verify what has been saved."
    )

    sandbox_run_tool = Tool(
        name="run_sandbox_script",
        func=run_sandbox_script,
        description="Run a Python script from sandbox by filename and return its stdout output. Use this to verify script results."
    )

    return file_tools + [push_tool, tool_search, python_repl, wiki_tool, sandbox_read_tool, sandbox_run_tool]

