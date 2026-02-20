import pandas as pd

df = pd.read_csv("complaints_text_dataset.csv")

counts = df["label"].value_counts().sort_index()
total = len(df)

table = pd.DataFrame({
    "Count": counts,
    "Percentage": (counts / total * 100).round(2)
})

print("\nTable 4: Complaint Frequency Distribution\n")
print(table)