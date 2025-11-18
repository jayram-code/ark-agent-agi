import pandas as pd

df = pd.read_csv("data/Hide_and_Seek_SAMPLE.csv")
row = df.iloc[0].to_dict()

# Keep only numeric
num_row = {k: v for k, v in row.items() if isinstance(v, (int, float))}

print("\nCopy this into run_emotion_pipeline.py:")
print(num_row)
