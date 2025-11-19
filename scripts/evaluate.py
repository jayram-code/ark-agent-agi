import os, sys
sys.path.append(os.getcwd())
from evaluation.eval_harness import run_dataset

def main():
    ds = os.path.join(os.getcwd(), "failure_cases.jsonl")
    out = run_dataset(ds)
    print("results_csv", os.path.abspath("evaluation/results.csv"))
    print("summary_json", os.path.abspath("evaluation/summary.json"))
    print("overall_accuracy", out["summary"].get("overall_accuracy"))

if __name__ == "__main__":
    main()
