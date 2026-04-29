import pandas as pd

df = pd.read_csv("data/classicHits.csv")
df = df.drop(df[df['Year'] >= 2000].index)

df.to_csv('./data/cleanedClassicHits.csv', index=False)
