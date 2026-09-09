import pandas as pd


V5_PATH = "training/data/threat_dataset_v5.csv"
V6_PATH = "training/data/threat_dataset_v6.csv"

OUTPUT_PATH = "training/data/threat_dataset_v7.csv"


print("=" * 60)
print("COMBINING V5 + V6")
print("=" * 60)


# ============================================================
# LOAD DATASETS
# ============================================================

print("\nLoading V5...")
v5 = pd.read_csv(V5_PATH)

print("V5 examples:", len(v5))


print("\nLoading V6...")
v6 = pd.read_csv(V6_PATH)

print("V6 examples:", len(v6))


# ============================================================
# COMBINE
# ============================================================

df = pd.concat(
    [v5, v6],
    ignore_index=True
)


# Remove exact duplicate sentences
before = len(df)

df = df.drop_duplicates(
    subset=["text"]
).reset_index(drop=True)

duplicates_removed = before - len(df)


# Shuffle
df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("V7 COMBINED DATASET")
print("=" * 60)

print("\nV5 examples:", len(v5))
print("V6 examples:", len(v6))
print("Duplicates removed:", duplicates_removed)
print("Final examples:", len(df))


print("\nLABEL DISTRIBUTION")
print("-" * 30)

print(
    df["label"].value_counts()
)


print("\nLANGUAGE DISTRIBUTION")
print("-" * 30)

print(
    df["language"].value_counts()
)


print("\nCATEGORY DISTRIBUTION")
print("-" * 30)

print(
    df["category"].value_counts()
)


print("\nSOURCE DISTRIBUTION")
print("-" * 30)

print(
    df["source"].value_counts()
)


print("\n" + "=" * 60)
print("SAVED TO:")
print(OUTPUT_PATH)
print("=" * 60)
