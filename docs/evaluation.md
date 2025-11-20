# 🧪 Evaluation Harness

The Evaluation Harness allows you to systematically measure the performance of your agents against a ground truth dataset.

## 🚀 Running Evaluations

Run the harness script:

```bash
python evals/harness.py
```

This will:
1.  Load scenarios from `evals/scenarios.json`.
2.  Run each scenario through the agent system.
3.  Score the results.
4.  Save the output to `evals/results.json`.

## 📊 Visualizing Results

We provide a **Jupyter Notebook** for interactive analysis.

1.  Start Jupyter:
    ```bash
    jupyter notebook
    ```
2.  Open `evals/evaluation_demo.ipynb`.
3.  Run the cells to see charts and pass rates.

## Adding Scenarios

Edit `evals/scenarios.json` to add new test cases:

```json
{
  "id": "new_case_001",
  "input": "User query here",
  "expected_intent": "target_intent"
}
```
