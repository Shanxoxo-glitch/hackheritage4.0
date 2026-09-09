"""
SPLIT DISTRESS DATASET V3  (leak-aware)

  * handwritten rows : stratified 65 / 15 / 20  -> train / val / TEST
  * templated rows   : GroupShuffleSplit 85 / 15 by `group` -> train / val
                       (a template's core phrase lives in ONE split only)
  * TEST = handwritten only. Templated text never reaches test.
"""
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split

INPUT_PATH = "training/data/distress_dataset_v3.csv"
TRAIN_PATH = "training/data/distress_v3_train.csv"
VAL_PATH = "training/data/distress_v3_val.csv"
TEST_PATH = "training/data/distress_v3_test.csv"
SEED = 42

df = pd.read_csv(INPUT_PATH)
hw = df[df["source"] == "handwritten"].copy()
tp = df[df["source"] == "templated"].copy()

# handwritten: 20% test, then 15% of total handwritten as val
hw_trainval, hw_test = train_test_split(
    hw, test_size=0.20, random_state=SEED, stratify=hw["label"])
hw_train, hw_val = train_test_split(
    hw_trainval, test_size=0.1875, random_state=SEED, stratify=hw_trainval["label"])

# templated: group-aware train/val
gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=SEED)
tr_idx, va_idx = next(gss.split(tp, tp["label"], groups=tp["group"]))
tp_train, tp_val = tp.iloc[tr_idx], tp.iloc[va_idx]

train = pd.concat([hw_train, tp_train]).sample(frac=1, random_state=SEED).reset_index(drop=True)
val = pd.concat([hw_val, tp_val]).sample(frac=1, random_state=SEED).reset_index(drop=True)
test = hw_test.sample(frac=1, random_state=SEED).reset_index(drop=True)

# leak checks
assert not (set(train["text"]) & set(test["text"])), "text leak train/test"
assert not (set(train["text"]) & set(val["text"])), "text leak train/val"
assert not (set(train["group"]) & set(test["group"])), "group leak train/test"
assert not (set(tp_train["group"]) & set(tp_val["group"])), "template group leak train/val"

train.to_csv(TRAIN_PATH, index=False)
val.to_csv(VAL_PATH, index=False)
test.to_csv(TEST_PATH, index=False)

print("=" * 60)
print("DISTRESS V3 SPLIT")
print("=" * 60)
for name, part in [("TRAIN", train), ("VAL", val), ("TEST", test)]:
    print(f"\n{name}: {len(part)}")
    print("  labels   :", part["label"].value_counts().sort_index().to_dict())
    print("  language :", part["language"].value_counts().to_dict())
    print("  source   :", part["source"].value_counts().to_dict())
print("\nLeak checks passed (no shared text, no shared template group).")
print("Saved:", TRAIN_PATH, VAL_PATH, TEST_PATH)
