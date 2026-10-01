"""Run the board worker with the smallest practical setup."""

import asyncio

import board
from google.adk.runners import InMemoryRunner
from task_worker.agent import WORKSPACE, root_agent

TASK = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."


def seed() -> int:
    """Start a fresh board and return the new goal's ID."""
    board.reset_board()
    return board.add_goal(TASK)


async def run() -> None:
    """Ask the ADK agent to work the goal."""
    runner = InMemoryRunner(agent=root_agent)
    await runner.run_debug("Please work the goal on the board.", verbose=True)


def main() -> None:
    goal_id = seed()
    board.claim_todo(goal_id)
    asyncio.run(run())

    board.show_board()

    spanish = WORKSPACE / "spanish.txt"
    if spanish.exists():
        print("\nspanish.txt:\n" + spanish.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
