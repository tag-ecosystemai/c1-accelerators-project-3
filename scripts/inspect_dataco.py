import pandas as pd

# Change the filename to match what you downloaded
df = pd.read_csv("data/raw/DataCoSupplyChainDataset.csv", encoding="latin-1")

print("Rows:", len(df))
print("\nCOLUMNS:")
for col in df.columns:
    print(" -", col)

print("\nONE EXAMPLE ROW:")
print(df.iloc[0])