import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

print("Importing google.generativeai...")
try:
    import google.generativeai
    print("Success.")
except ImportError as e:
    print(f"Failed: {e}")

print("Importing utils.observability.metrics...")
try:
    import utils.observability.metrics
    print("Success.")
except ImportError as e:
    print(f"Failed: {e}")

print("Importing agents.planner_agent...")
try:
    from agents.planner_agent import PlannerAgent
    print("Success.")
except ImportError as e:
    print(f"Failed: {e}")
except Exception as e:
    print(f"Error: {e}")
