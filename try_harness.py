import json

from src.orchestrator import Orchestrator

orch = Orchestrator()

def run_test_harness(dataset_path):
    results = []

    with open(dataset_path, "r") as f:
        for line in f:
            case = json.loads(line)
            customer_text = case["text"]
            expected = case["expected"]

            output = orch.handle(customer_text)   # your agent flow

            passed = (output.get("action") == expected)

            results.append({
                "id": case["id"],
                "expected": expected,
                "got": output.get("action"),
                "passed": passed
            })

    return results
