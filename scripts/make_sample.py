import pandas as pd
src = "data/Hide_and_Seek_DATASET.csv"
dst = "data/Hide_and_Seek_SAMPLE.csv"
n = 20000
print("Reading", n, "rows from", src)
df = pd.read_csv(src, nrows=n)
df.to_csv(dst, index=False)
print("Wrote sample to", dst)
