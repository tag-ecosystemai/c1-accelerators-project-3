import pandas as pd

df = pd.read_csv("data/raw/DataCoSupplyChainDataset.csv", encoding="latin-1")

print("Rows:", len(df))
print("Unique Order Id:", df["Order Id"].nunique())
print("\nScheduled days:\n", df["Days for shipment (scheduled)"].value_counts().sort_index())
print("\nLate rate:", df["Late_delivery_risk"].mean())
print("\nMissing lat/lon:", df[["Latitude", "Longitude"]].isna().sum().to_dict())
print("\nDepartments:", df["Department Name"].nunique(), "| Categories:", df["Category Name"].nunique())