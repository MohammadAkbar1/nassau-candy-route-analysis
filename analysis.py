import pandas as pd

df = pd.read_csv("data/dataset.csv")

# Convert dates
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Ship Date'] = pd.to_datetime(df['Ship Date'])

# Lead Time
df['Lead Time'] = (df['Ship Date'] - df['Order Date']).dt.days

# Removed invalid values
df = df[df['Lead Time'] >= 0]
