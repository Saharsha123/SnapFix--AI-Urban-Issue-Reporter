import joblib
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np

# ===== LOAD DATA =====
df = pd.read_csv("../complaints_text_dataset.csv")

X_text = df["text"]
y_true = df["label"]

# ===== LOAD MODEL =====
vectorizer = joblib.load("../text_vectorizer.joblib")
model = joblib.load("../text_classifier.joblib")
label_to_idx = joblib.load("../label_to_idx.joblib")

X_vec = vectorizer.transform(X_text)
y_pred = model.predict(X_vec)

# ===== ENCODE LABELS =====
y_true_encoded = np.array([label_to_idx[label] for label in y_true])

# ===== METRICS =====
precision = precision_score(y_true_encoded, y_pred, average="macro")
recall = recall_score(y_true_encoded, y_pred, average="macro")
f1 = f1_score(y_true_encoded, y_pred, average="macro")

print("\nTable 3 Metrics (TF-IDF + Logistic Regression):")
print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1-Score  : {f1:.4f}")