import pandas as pd
try:
    df = pd.read_csv("evaluation/results.csv")
    print(df[["true_intent", "pred_intent", "intent_correct"]].tail(20))
    print(f"\nTotal cases processed: {len(df)}")
    print(f"Intent Accuracy so far: {df['intent_correct'].mean():.2%}")
    print(f"Sentiment Accuracy so far: {df['sentiment_correct'].mean():.2%}") # Assuming column name
except Exception as e:
    print(f"Error reading results: {e}")
