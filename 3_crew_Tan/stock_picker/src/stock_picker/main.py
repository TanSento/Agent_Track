#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from stock_picker.crew import StockPicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'sector': 'Technology',
    }

    # Create and run the crew
    crew = StockPicker().crew()
    result = crew.kickoff(inputs=inputs)


    # Print final restuls
    print("\n\n============ FINAL DECISION ============\n\n")
    print(result.raw)



if __name__ == "__main__":
    run()