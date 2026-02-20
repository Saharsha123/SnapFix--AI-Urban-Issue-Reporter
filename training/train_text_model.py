import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# ===============================
# LOAD DATASET
# ===============================

df = pd.read_csv("complaints_text_dataset.csv")

texts = df["text"].astype(str).tolist()
labels = df["label"].astype(str).tolist()

# ===============================
# LABEL ENCODING
# ===============================

unique_labels = sorted(set(labels))
label_to_idx = {lbl: i for i, lbl in enumerate(unique_labels)}
idx_to_label = {i: lbl for lbl, i in label_to_idx.items()}

y = [label_to_idx[lbl] for lbl in labels]

print("Labels:", unique_labels)

# ===============================
# TRAIN / TEST SPLIT
# ===============================

X_train, X_test, y_train, y_test = train_test_split(
    texts,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ===============================
# VECTORIZATION
# ===============================

vectorizer = TfidfVectorizer(
    max_features=5000,
    ngram_range=(1, 2),
    stop_words="english"
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# ===============================
# MODEL TRAINING
# ===============================

clf = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    n_jobs=-1
)

clf.fit(X_train_vec, y_train)

acc = clf.score(X_test_vec, y_test)
print(f"Validation Accuracy: {acc:.4f}")

# ===============================
# SAVE ARTIFACTS
# ===============================

joblib.dump(vectorizer, "text_vectorizer.joblib")
joblib.dump(clf, "text_classifier.joblib")
joblib.dump(label_to_idx, "label_to_idx.joblib")

print("✅ Text model and artifacts saved successfully")
