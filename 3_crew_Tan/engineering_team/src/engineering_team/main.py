#!/usr/bin/env python
import warnings
from pathlib import Path

from engineering_team.crew import DesignCrew, ModuleCrew, FrontendCrew
from engineering_team.models import SystemDesign

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"

requirements = """
A simple account management system for a trading simulation platform.
The system should allow users to create an account, deposit funds, and withdraw funds.
The system should allow users to record that they have bought or sold shares, providing a quantity.
The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
The system should be able to report the holdings of the user at any point in time.
The system should be able to report the profit or loss of the user at any point in time.
The system should be able to list the transactions that the user has made over time.
The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
from buying more shares than they can afford, or selling shares that they don't have.
The system has access to a function get_share_price(symbol) which returns the current price of a share,
and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
"""


def run():
    # Phase 1: engineering lead designs the full system
    print("=== Phase 1: System Design ===")
    design_result = DesignCrew().crew().kickoff(inputs={"requirements": requirements})
    system_design: SystemDesign = design_result.pydantic
    print(f"System overview: {system_design.system_overview}")
    print(f"Modules to build: {[m.module_name for m in system_design.modules]}\n")

    # Phase 2: build each module sequentially
    for spec in system_design.modules:
        print(f"=== Phase 2: Building {spec.module_name} ===")
        ModuleCrew().crew().kickoff(inputs={
            "requirements": requirements,
            "module_name": spec.module_name,
            "class_name": spec.class_name,
            "description": spec.description,
            "dependencies": ", ".join(spec.dependencies) if spec.dependencies else "none",
            "system_overview": system_design.system_overview,
        })

    # Phase 3: read all generated modules then build the frontend
    print("=== Phase 3: Frontend ===")
    modules_code = _read_generated_modules(system_design)
    module_list = "\n".join(
        f"- {s.module_name} ({s.class_name}): {s.description}"
        for s in system_design.modules
    )
    FrontendCrew().crew().kickoff(inputs={
        "requirements": requirements,
        "system_overview": system_design.system_overview,
        "module_list": module_list,
        "modules_code": modules_code,
    })


def _read_generated_modules(system_design: SystemDesign) -> str:
    """Read each generated module file from disk and return combined source."""
    parts = []
    for spec in system_design.modules:
        path = OUTPUT_DIR / spec.module_name
        if path.exists():
            parts.append(f"# --- {spec.module_name} ---\n{path.read_text()}")
        else:
            print(f"[warning] expected output file not found: {path}")
    return "\n\n".join(parts)
