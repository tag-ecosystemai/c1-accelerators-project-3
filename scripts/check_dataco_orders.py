import pandas as pd

df = pd.read_csv("data/raw/DataCoSupplyChainDataset.csv", encoding="latin-1")
g = df.groupby("Order Id")

print("Orders where items disagree on:")
print(" - late label:      ", (g["Late_delivery_risk"].nunique() > 1).sum())
print(" - shipping mode:   ", (g["Shipping Mode"].nunique() > 1).sum())
print(" - scheduled days:  ", (g["Days for shipment (scheduled)"].nunique() > 1).sum())
print(" - order date:      ", (g["order date (DateOrders)"].nunique() > 1).sum())
print(" - latitude:        ", (g["Latitude"].nunique() > 1).sum())
print(" - category:        ", (g["Category Name"].nunique() > 1).sum())

print("\nLate rate by shipping mode:")
print(df.groupby("Shipping Mode")["Late_delivery_risk"].mean().round(3))

print("\nLate rate by department:")
print(df.groupby("Department Name")["Late_delivery_risk"].mean().sort_values().round(3))