import pandas as pd
from sklearn.model_selection import train_test_split


INPUT_PATH = "training/data/threat_dataset_v7.csv"

TRAIN_PATH = "training/data/threat_v7_train.csv"
VAL_PATH = "training/data/threat_v7_val.csv"
TEST_PATH = "training/data/threat_v7_test.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING V7 DATASET")
print("=" * 60)

df = pd.read_csv(INPUT_PATH)

print("Total examples:", len(df))


# ============================================================
# 70 / 15 / 15 SPLIT
# ============================================================

train_df, temp_df = train_test_split(
    df,
    test_size=0.30,
    random_state=42,
    stratify=df["label"]
)

val_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    random_state=42,
    stratify=temp_df["label"]
)


# ============================================================
# SAVE
# ============================================================

train_df.to_csv(TRAIN_PATH, index=False)
val_df.to_csv(VAL_PATH, index=False)
test_df.to_csv(TEST_PATH, index=False)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("V7 DATASET SPLIT")
print("=" * 60)

print("\nTraining:", len(train_df))
print("Validation:", len(val_df))
print("Test:", len(test_df))


print("\nLABEL DISTRIBUTION")
print("-" * 30)

print("\nTRAIN")
print(train_df["label"].value_counts())

print("\nVALIDATION")
print(val_df["label"].value_counts())

print("\nTEST")
print(test_df["label"].value_counts())


print("\nLANGUAGE DISTRIBUTION")
print("-" * 30)

print("\nTRAIN")
print(train_df["language"].value_counts())

print("\nVALIDATION")
print(val_df["language"].value_counts())

print("\nTEST")
print(test_df["language"].value_counts())


print("\nCATEGORY DISTRIBUTION")
print("-" * 30)

print("\nTRAIN")
print(train_df["category"].value_counts())

print("\nVALIDATION")
print(val_df["category"].value_counts())

print("\nTEST")
print(test_df["category"].value_counts())


print("\n" + "=" * 60)
print("FILES SAVED")
print("=" * 60)

print(TRAIN_PATH)
print(VAL_PATH)
print(TEST_PATH)
